import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL, MATCH
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import utils as ut
# Make sure to import the app instance
from models import User, db, Watchlist, StockKPI
from dash.exceptions import PreventUpdate
from layouts import themes
import asyncio


def get_data_callbacks(app, server, cache):

    async def preload_data_async(cache):
        try:
            await asyncio.gather(
                preload_prices_async(cache),
                preload_news_async(cache)
            )
        except Exception as e:
            print(f"Error during preloading: {e}")

    async def preload_prices_async(cache):
        try:
            print("Preloading prices data asynchronously...")
            prices_data = yf.download(['AAPL', 'MSFT'], pd.to_datetime(
                'today') - timedelta(days=365), pd.to_datetime('today'), interval="1d")
            if not prices_data.empty:
                cache.set('prices_data', prices_data)
            else:
                print("Failed to preload prices data: empty DataFrame")
        except Exception as e:
            print(f"Error during price preload: {e}")

    async def preload_news_async(cache):
        try:
            print("Preloading news data asynchronously...")
            news_data = ut.fetch_news(['AAPL', 'MSFT'])
            if news_data:
                cache.set('news_data', news_data)
            else:
                print("Failed to preload news data: empty data")
        except Exception as e:
            print(f"Error during news preload: {e}")

    # Preload data at startup

    def run_preload(cache):
        print("Starting async preload...")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No event loop is running
        loop = None

    if loop and loop.is_running():
        # If already in an event loop, create the task
        asyncio.create_task(preload_data_async(cache))
    else:
        # If no event loop is running, run the task
        asyncio.run(preload_data_async(cache))

    print("Async preload completed.")

    @cache.memoize(timeout=600)  # Cache the result for 10 minutes
    def fetch_news_with_cache(stock_symbols):
        # Your existing function to fetch the news
        return ut.fetch_news(stock_symbols)

    @cache.memoize(timeout=600)  # Cache the result for 10 minutes
    def fetch_analyst_reco_with_cache(symbol):
        # Your existing function to fetch the news
        return ut.fetch_analyst_recommendations(symbol)

    @cache.memoize(timeout=600)  # Cache for 15 minutes
    def get_stock_data_cached(symbol, start_date, end_date, interval):
        return yf.download(symbol, start=start_date, end=end_date, interval=interval)
    

    preloaded_prices = cache.get('prices_data')
    preloaded_news = cache.get('news_data')

    # --------------------------------------------------

        
    @app.callback(
            [
                Output('stock-news', 'children'),
                Output('news-stock-dropdown', 'options'),
                Output('news-stock-dropdown', 'value')
            ],
            [Input('news-stock-dropdown', 'value')],
            [Input('individual-stocks-store', 'data')]
    )

    def update_news(selected_news_stocks, individual_stocks):
        if not individual_stocks:
            return (
                html.Div(
                    "No stocks available. Please add stocks to view the news."),
                [""],  # Empty dropdown options
                ""   # Empty value
            )

        # Generate options for the news dropdown based on individual stocks
        options = [{'label': stock, 'value': stock}
            for stock in individual_stocks]

        # If no stock is selected, default to the first 5 stocks (if available)
        if not selected_news_stocks:
            selected_news_stocks = individual_stocks[:5]

        # Fetch related news for the selected stocks
        news_content = fetch_news_with_cache(selected_news_stocks)

        return (
            news_content,
            options,
            selected_news_stocks
        )

    @app.callback(
        [
            Output('forecast-stock-input', 'options'),
            Output('forecast-stock-input', 'value'),

     ],
        Input('forecast-stock-input', 'value'),
        Input('individual-stocks-store', 'data')

    )
    def update_forecast_dropdown(selected_forecast_stocks, individual_stocks):
        if not individual_stocks:
            return []

        options = [{'label': stock, 'value': stock}
            for stock in individual_stocks]
        
        if not selected_forecast_stocks:
            selected_forecast_stocks = individual_stocks[:1]
            
        return options, selected_forecast_stocks
    
    
    @app.callback(
        [
            Output('simulation-stock-input', 'options'),
            Output('simulation-stock-input', 'value'),

     ],
        Input('simulation-stock-input', 'value'),
        Input('individual-stocks-store', 'data')
    )
    def update_simulation_dropdown(selected_simulation_stocks, individual_stocks):
        if not individual_stocks:
            return []

        options = [{'label': stock, 'value': stock}
            for stock in individual_stocks]
        
        if not selected_simulation_stocks:
            selected_simulation_stocks = individual_stocks[:1]
            
        return options, selected_simulation_stocks
    
    # Callback to handle modifications to `individual-stocks-store`
    @app.callback(
        [
            Output('individual-stocks-store', 'data'),  # Update the individual stocks store
            Output('stock-suggestions-input', 'value')   # Clear the input field after adding
        ],
        [
            Input('saved-watchlists-dropdown', 'value'),
            Input('refresh-data-icon', 'n_clicks'),
            Input('stock-suggestions-input', 'value'),
            Input('reset-stocks-button', 'n_clicks'),
            Input({'type': 'remove-stock', 'index': ALL}, 'n_clicks')
        ],
        [
            State('login-username-store', 'data'),
            State('individual-stocks-store', 'data')
        ],
        prevent_initial_call=True
    )
    def modify_individual_stocks(
        watchlist_id, refresh_n_clicks, new_stock, reset_n_clicks, remove_clicks, username, individual_stocks
    ):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id']
        default_stocks = []  # Set default to empty list for a full reset
        
        # Load watchlist if selected
        if 'saved-watchlists-dropdown' in trigger_id:
            # Load the watchlist data based on selected dropdown
            if watchlist_id:
                # Fetch watchlist from database
                watchlist = db.session.get(Watchlist, watchlist_id)
                if watchlist:
                    individual_stocks = json.loads(watchlist.stocks)
                else:
                    individual_stocks = default_stocks
            else:
                individual_stocks = default_stocks
    
        # Add new stock from suggestions input
        elif 'stock-suggestions-input' in trigger_id and new_stock:
            new_stock = new_stock.upper().strip()
            if new_stock and new_stock not in individual_stocks:
                individual_stocks.append(new_stock)
            # Clear the input field after adding the stock
            return individual_stocks, ''
    
        # Reset stocks if reset button is clicked
        elif 'reset-stocks-button' in trigger_id:
            individual_stocks = []  # Reset to empty list
            return individual_stocks, dash.no_update
    
        # Remove specific stock based on index
        elif 'remove-stock' in trigger_id:
            index_to_remove = json.loads(trigger_id.split('.')[0])['index']
            if 0 <= index_to_remove < len(individual_stocks):
                individual_stocks.pop(index_to_remove)
            return individual_stocks, dash.no_update
    
        print(f"Updated individual_stocks: {individual_stocks}")  # Debugging
        
        # Return the updated stocks list and no update for input if no new stock added
        return individual_stocks, dash.no_update

 
    
    @app.callback(
    Output('watchlist-summary', 'children'),
    [
        Input('individual-stocks-store', 'data'),
        Input('saved-watchlists-dropdown', 'value'),
        Input('reset-stocks-button', 'n_clicks')
    ]
    )
    def update_watchlist_summary(individual_stocks, selected_watchlist, reset_n_clicks):
        if not individual_stocks:
            return html.Div("Your watchlist is empty. Add stocks to track them here.")
    
        # Generate and return the watchlist summary
        return ut.generate_watchlist_table(individual_stocks)


    from dash import no_update
    
    @app.callback(
        [
            Output('save-watchlist-modal', 'is_open'),
            Output('delete-watchlist-modal', 'is_open'),
            Output('overwrite-warning', 'children'),
            Output('new-watchlist-name', 'style'),
            Output('saved-watchlists-dropdown', 'options'),
            Output('saved-watchlists-dropdown', 'value'),
            Output('new-watchlist-name', 'value'),
            Output('save_modal_triggered', 'data')
        ],
        [
            Input('create-watchlist-button', 'n_clicks'),
            Input('confirm-save-watchlist', 'n_clicks'),
            Input('delete-watchlist-button', 'n_clicks'),
            Input('confirm-delete-watchlist', 'n_clicks'),
            Input('cancel-save-watchlist', 'n_clicks'),
            Input('cancel-delete-watchlist', 'n_clicks'),
            Input('saved-watchlists-dropdown', 'value'),  # To load selected watchlist
            Input('url', 'pathname'),  # Detects tab changes
            Input('login-username-store', 'data')  # Detects initial load for a logged-in user
        ],
        [
            State('new-watchlist-name', 'value'),
            State('individual-stocks-store', 'data'),
            State('login-username-store', 'data'),
            State('save_modal_triggered', 'data')
        ],
        prevent_initial_call=True
    )
    def manage_watchlists(
        create_clicks, confirm_save_clicks, delete_clicks, confirm_delete_clicks,
        cancel_save_clicks, cancel_delete_clicks, selected_watchlist_id, pathname, username_initial,
        new_watchlist_name, stocks, username, save_modal_triggered
    ):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        open_save_modal, open_delete_modal = False, False
    
        # Ensure user is logged in
        if not username:
            return open_save_modal, open_delete_modal, "", {"display": "none"}, [], None, "", False
    
        # Fetch user and load watchlists when necessary
        user = User.query.filter_by(username=username).first()
        if not user:
            return open_save_modal, open_delete_modal, "", {"display": "none"}, [], None, "", False
    
        # Check if we need to load the watchlists (on initial load or when tab changes)
        watchlists = Watchlist.query.filter_by(user_id=user.id).all()
        watchlist_options = [{'label': w.name, 'value': w.id} for w in watchlists]
    
        if trigger_id in ['login-username-store', 'url']:  # Load on initial login or tab change
            selected_watchlist = watchlist_options[0]['value'] if watchlist_options else None
            return (
                open_save_modal, open_delete_modal, "", {"display": "none"},
                watchlist_options, selected_watchlist, "", save_modal_triggered
            )
    
        # Load selected watchlist data when dropdown value changes
        if trigger_id == 'saved-watchlists-dropdown':
            if selected_watchlist_id:
                watchlist = Watchlist.query.get(selected_watchlist_id)
                if watchlist and watchlist.user_id == user.id:
                    return (
                        open_save_modal, open_delete_modal, "", {"display": "none"},
                        watchlist_options, selected_watchlist_id, "", save_modal_triggered
                    )
            return open_save_modal, open_delete_modal, "", {"display": "none"}, watchlist_options, None, "", save_modal_triggered
    
        # Handle "Save" button click - open save modal only if this button was clicked
        if trigger_id == 'create-watchlist-button':
            save_modal_triggered = True  # Mark that the save modal was intentionally triggered
            if selected_watchlist_id or any(w.name == new_watchlist_name for w in watchlists):
                overwrite_message = (
                    "Overwrite the existing watchlist?" if selected_watchlist_id else 
                    "A watchlist with this name exists. Do you want to overwrite it?"
                )
                return True, False, overwrite_message, {"display": "none"}, watchlist_options, no_update, "", save_modal_triggered
    
            # Prompt for new watchlist name if no duplicates
            return True, False, "", {"display": "inline-block"}, watchlist_options, no_update, "", save_modal_triggered
    
        elif trigger_id == 'confirm-save-watchlist' and save_modal_triggered:
            if selected_watchlist_id:
                watchlist = Watchlist.query.get(selected_watchlist_id)
                if watchlist and watchlist.user_id == user.id:
                    watchlist.stocks = json.dumps(stocks)
                    db.session.commit()
                    return False, False, "", {"display": "none"}, watchlist_options, selected_watchlist_id, "", False
            elif new_watchlist_name:
                duplicate = Watchlist.query.filter_by(user_id=user.id, name=new_watchlist_name).first()
                if duplicate:
                    db.session.delete(duplicate)
                    db.session.commit()
        
                new_watchlist = Watchlist(user_id=user.id, name=new_watchlist_name, stocks=json.dumps(stocks))
                db.session.add(new_watchlist)
                db.session.commit()
                selected_watchlist_id = new_watchlist.id
        
            # Ensure `individual-stocks-store` retains its state if no change is needed
            return False, False, "", {"display": "none"}, watchlist_options, selected_watchlist_id, dash.no_update, False
            

            # Reload watchlists after save
            watchlists = Watchlist.query.filter_by(user_id=user.id).all()
            options = [{'label': w.name, 'value': w.id} for w in watchlists]
            return False, False, "", {"display": "none"}, options, selected_watchlist_id, "", False
    
        # Handle delete button click
        elif trigger_id == 'delete-watchlist-button' and selected_watchlist_id:
            open_delete_modal = True
            return open_save_modal, open_delete_modal, "", {"display": "none"}, no_update, no_update, no_update, save_modal_triggered
    
        # Confirm deletion
        elif trigger_id == 'confirm-delete-watchlist' and selected_watchlist_id:
            watchlist = Watchlist.query.get(selected_watchlist_id)
            if watchlist and watchlist.user_id == user.id:
                db.session.delete(watchlist)
                db.session.commit()
                selected_watchlist_id = None
    
            # Reload watchlists after delete
            watchlists = Watchlist.query.filter_by(user_id=user.id).all()
            options = [{'label': w.name, 'value': w.id} for w in watchlists]
            return False, False, "", {"display": "none"}, options, selected_watchlist_id, "", save_modal_triggered
    
        # Cancel modal actions and reset `save_modal_triggered`
        elif trigger_id in ['cancel-save-watchlist', 'cancel-delete-watchlist']:
            return False, False, "", {"display": "none"}, no_update, no_update, "", False
    
        return open_save_modal, open_delete_modal, "", {"display": "none"}, watchlist_options, selected_watchlist_id, "", save_modal_triggered
    
    

 
    # @app.callback(
    #     [
    #         Output('save-watchlist-modal', 'is_open'),
    #         Output('delete-watchlist-modal', 'is_open'),
    #         Output('overwrite-warning', 'children'),
    #         Output('new-watchlist-name', 'style'),
    #         Output('saved-watchlists-dropdown', 'options'),
    #         Output('saved-watchlists-dropdown', 'value'),
    #         Output('new-watchlist-name', 'value'),
    #         Output('save_modal_triggered', 'data')
    #     ],
    #     [
    #         Input('create-watchlist-button', 'n_clicks'),
    #         Input('confirm-save-watchlist', 'n_clicks'),
    #         Input('delete-watchlist-button', 'n_clicks'),
    #         Input('confirm-delete-watchlist', 'n_clicks'),
    #         Input('cancel-save-watchlist', 'n_clicks'),
    #         Input('cancel-delete-watchlist', 'n_clicks'),
    #         Input('saved-watchlists-dropdown', 'value'),  # To load selected watchlist
    #         Input('url', 'pathname'),  # Detects tab changes
    #         Input('login-username-store', 'data')  # Detects initial load for a logged-in user
    #     ],
    #     [
    #         State('new-watchlist-name', 'value'),
    #         State('individual-stocks-store', 'data'),
    #         State('login-username-store', 'data'),
    #         State('save_modal_triggered', 'data')
    #     ],
    #     prevent_initial_call=True
    # )
    # def manage_watchlists(
    #     create_clicks, confirm_save_clicks, delete_clicks, confirm_delete_clicks,
    #     cancel_save_clicks, cancel_delete_clicks, selected_watchlist_id, pathname, username_initial,
    #     new_watchlist_name, stocks, username, save_modal_triggered
    # ):
    #     ctx = dash.callback_context
    #     trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    #     open_save_modal, open_delete_modal = False, False
    
    #     # Ensure user is logged in
    #     if not username:
    #         return open_save_modal, open_delete_modal, "", {"display": "none"}, [], None, "", False
    
    #     # Fetch user and load watchlists when necessary
    #     user = User.query.filter_by(username=username).first()
    #     if not user:
    #         return open_save_modal, open_delete_modal, "", {"display": "none"}, [], None, "", False
    
    #     # Check if we need to load the watchlists (on initial load or when tab changes)
    #     watchlists = Watchlist.query.filter_by(user_id=user.id).all()
    #     watchlist_options = [{'label': w.name, 'value': w.id} for w in watchlists]
    
    #     if trigger_id in ['login-username-store', 'url']:  # Load on initial login or tab change
    #         selected_watchlist = watchlist_options[0]['value'] if watchlist_options else None
    #         return (
    #             open_save_modal, open_delete_modal, "", {"display": "none"},
    #             watchlist_options, selected_watchlist, "", save_modal_triggered
    #         )
    
    #     # Load selected watchlist data when dropdown value changes
    #     if trigger_id == 'saved-watchlists-dropdown':
    #         if selected_watchlist_id:
    #             watchlist = Watchlist.query.get(selected_watchlist_id)
    #             if watchlist and watchlist.user_id == user.id:
    #                 return (
    #                     open_save_modal, open_delete_modal, "", {"display": "none"},
    #                     watchlist_options, selected_watchlist_id, "", save_modal_triggered
    #                 )
    #         return open_save_modal, open_delete_modal, "", {"display": "none"}, watchlist_options, None, "", save_modal_triggered
    
    #     # Handle "Save" button click - open save modal only if this button was clicked
    #     if trigger_id == 'create-watchlist-button':
    #         save_modal_triggered = True  # Mark that the save modal was intentionally triggered
    #         if selected_watchlist_id or any(w.name == new_watchlist_name for w in watchlists):
    #             overwrite_message = (
    #                 "Overwrite the existing watchlist?" if selected_watchlist_id else 
    #                 "A watchlist with this name exists. Do you want to overwrite it?"
    #             )
    #             return True, False, overwrite_message, {"display": "none"}, watchlist_options, no_update, "", save_modal_triggered
    
    #         # Prompt for new watchlist name if no duplicates
    #         return True, False, "", {"display": "inline-block"}, watchlist_options, no_update, "", save_modal_triggered
    
    #     # Confirm save or overwrite action only if the modal was intentionally triggered
    #     elif trigger_id == 'confirm-save-watchlist' and save_modal_triggered:
    #         if selected_watchlist_id:
    #             watchlist = Watchlist.query.get(selected_watchlist_id)
    #             if watchlist and watchlist.user_id == user.id:
    #                 watchlist.stocks = json.dumps(stocks)
    #                 db.session.commit()
    #                 return False, False, "", {"display": "none"}, watchlist_options, selected_watchlist_id, "", False
    #         elif new_watchlist_name:
    #             duplicate = Watchlist.query.filter_by(user_id=user.id, name=new_watchlist_name).first()
    #             if duplicate:
    #                 db.session.delete(duplicate)
    #                 db.session.commit()
    
    #             new_watchlist = Watchlist(user_id=user.id, name=new_watchlist_name, stocks=json.dumps(stocks))
    #             db.session.add(new_watchlist)
    #             db.session.commit()
    #             selected_watchlist_id = new_watchlist.id
    
    #         # Reload watchlists after save
    #         watchlists = Watchlist.query.filter_by(user_id=user.id).all()
    #         options = [{'label': w.name, 'value': w.id} for w in watchlists]
    #         return False, False, "", {"display": "none"}, options, selected_watchlist_id, "", False
    
    #     # Handle delete button click
    #     elif trigger_id == 'delete-watchlist-button' and selected_watchlist_id:
    #         open_delete_modal = True
    #         return open_save_modal, open_delete_modal, "", {"display": "none"}, no_update, no_update, no_update, save_modal_triggered
    
    #     # Confirm deletion
    #     elif trigger_id == 'confirm-delete-watchlist' and selected_watchlist_id:
    #         watchlist = Watchlist.query.get(selected_watchlist_id)
    #         if watchlist and watchlist.user_id == user.id:
    #             db.session.delete(watchlist)
    #             db.session.commit()
    #             selected_watchlist_id = None
    
    #         # Reload watchlists after delete
    #         watchlists = Watchlist.query.filter_by(user_id=user.id).all()
    #         options = [{'label': w.name, 'value': w.id} for w in watchlists]
    #         return False, False, "", {"display": "none"}, options, selected_watchlist_id, "", save_modal_triggered
    
    #     # Cancel modal actions and reset `save_modal_triggered`
    #     elif trigger_id in ['cancel-save-watchlist', 'cancel-delete-watchlist']:
    #         return False, False, "", {"display": "none"}, no_update, no_update, "", False
    
    #     return open_save_modal, open_delete_modal, "", {"display": "none"}, watchlist_options, selected_watchlist_id, "", save_modal_triggered
    
  
    @app.callback(
        [
            Output('stock-graph', 'figure'),
            Output('stock-graph', 'style'),
            Output('prices-stock-dropdown', 'options'),
            Output('prices-stock-dropdown', 'value'),
            Output('prices-fig-store', 'data', allow_duplicate=True)
        ],
        [
            Input('url', 'pathname'),
            Input('chart-type', 'value'),
            Input('movag_input', 'value'),
            Input('predefined-ranges', 'value'),
            Input('plotly-theme-store', 'data'),
            Input('individual-stocks-store', 'data'),
            Input('prices-stock-dropdown', 'value')
        ],
        [State('prices-fig-store', 'data')],
        prevent_initial_call=True
    )
    def update_stock_graph_and_dropdown(
        pathname, chart_type, movag_input, predefined_range, plotly_theme,
        individual_stocks, selected_prices_stocks, stored_data
    ):
        if pathname != '/prices':
            raise PreventUpdate
    
        options = [{'label': stock, 'value': stock} for stock in individual_stocks]
        selected_prices_stocks = selected_prices_stocks or individual_stocks[-10:]
    
        today = pd.to_datetime('today')
        start_date, interval = determine_date_range(predefined_range, today)
        data_frames = []
    
        for stock in selected_prices_stocks:
            try:
                df = get_stock_data_cached(stock, start_date, today, interval)
                if df.empty:
                    continue
    
                df.index = pd.to_datetime(df.index)  # Ensure index is datetime
                df['Date'] = df.index  # Add a 'Date' column for plotting consistency
    
                if '30D_MA' in movag_input:
                    df['30D_MA'] = df['Close'].rolling(window=30).mean()
                if '100D_MA' in movag_input:
                    df['100D_MA'] = df['Close'].rolling(window=100).mean()
                df['Stock'] = stock
                data_frames.append(df)
            except Exception as e:
                print(f"Data for {stock} not available: {e}")
                continue
    
        df_all = pd.concat(data_frames, ignore_index=False) if data_frames else pd.DataFrame()
    
        if df_all.empty:
            fig_store_data = {}
            empty_fig = {
                'data': [],
                'layout': {'title': 'No Data Available for Selected Stocks'}
            }
            return empty_fig, {'height': '400px'}, options, selected_prices_stocks, fig_store_data
    
        fig_stock, graph_height = ut.generate_fig_stock(df_all, selected_prices_stocks, movag_input, chart_type, plotly_theme, interval)
    
        fig_store_data = {
            'figure': fig_stock,
            'data': df_all.to_dict('records'),
            'options': options,
            'individual_stocks': individual_stocks,
            'chart_type': chart_type,
            'movag_input': movag_input,
            'predefined_range': predefined_range,
            'plotly_theme': plotly_theme,
            'graph_height': graph_height
        }
    
        return fig_stock, {'height': f'{graph_height}px'}, options, selected_prices_stocks, fig_store_data


    
    @app.callback(
    [
        Output('indexed-comparison-graph', 'figure'),
        Output('indexed-comparison-stock-dropdown', 'options'),
        Output('indexed-comparison-stock-dropdown', 'value')
    ],
    [
        Input('url', 'pathname'),  # Trigger on page change
        Input('indexed-comparison-stock-dropdown', 'value'),
        Input('benchmark-selection', 'value'),
        Input('predefined-ranges', 'value'),
        Input('individual-stocks-store', 'data')
    ],
    [State('individual-stocks-store', 'data'), State('plotly-theme-store', 'data')]
    )
    def update_indexed_comparison_graph(pathname, selected_comparison_stocks, benchmark_selection, predefined_range, individual_stocks_update, individual_stocks, plotly_theme):
        
        options = [{'label': stock, 'value': stock} for stock in individual_stocks]
    
        if not selected_comparison_stocks:
            selected_comparison_stocks = individual_stocks[-10:]
    
        today = pd.to_datetime('today')
        start_date, interval = determine_date_range(predefined_range, today)
        end_date = today
    
        indexed_data = {}
        for symbol in selected_comparison_stocks:
            # Retry logic for cache miss or API failures
            try:
                df_stock = get_stock_data_cached(symbol, start_date, end_date, interval)
                if not df_stock.empty:
                    df_stock['Index'] = df_stock['Close'] / df_stock['Close'].iloc[0] * 100
                    indexed_data[symbol] = df_stock[['Index']].rename(columns={"Index": symbol})
            except KeyError as e:
                print(f"Data for {symbol} not available: {e}")
                continue
    
        # Check and process benchmark data
        benchmark_data = process_benchmark_data(benchmark_selection, start_date, end_date, interval)
    
        fig_indexed = generate_indexed_graph(indexed_data, benchmark_data, plotly_theme, selected_comparison_stocks)
    
        return fig_indexed, options, selected_comparison_stocks
    
    
    def determine_date_range(predefined_range, today):
        if predefined_range == '5D_15m':
            return today - timedelta(days=5), '15m'
        elif predefined_range == '1D_15m':
            return today - timedelta(hours=24), '5m'
        elif predefined_range == 'YTD':
            return datetime(today.year, 1, 1), '1d'
        elif predefined_range == '1M':
            return today - timedelta(days=30), '1d'
        elif predefined_range == '3M':
            return today - timedelta(days=3 * 30), '1d'
        elif predefined_range == '12M':
            return today - timedelta(days=365), '1d'
        elif predefined_range == '24M':
            return today - timedelta(days=730), '1d'
        elif predefined_range == '5Y':
            return today - timedelta(days=1825), '1d'
        elif predefined_range == '10Y':
            return today - timedelta(days=3650), '1d'
        else:
            return pd.to_datetime('2024-01-01'), '1d'
    
    
    def process_benchmark_data(benchmark_selection, start_date, end_date, interval):
        if benchmark_selection != 'None':
            try:
                benchmark_data = get_stock_data_cached(benchmark_selection, start_date, end_date, interval)
                if not benchmark_data.empty:
                    benchmark_data['Index'] = benchmark_data['Close'] / benchmark_data['Close'].iloc[0] * 100
                return benchmark_data
            except KeyError as e:
                print(f"Benchmark data for {benchmark_selection} not available: {e}")
        return None
    
    
    def generate_indexed_graph(indexed_data, benchmark_data, plotly_theme, selected_comparison_stocks):
        if indexed_data:
            df_indexed = pd.concat(indexed_data, axis=1)
            df_indexed.reset_index(inplace=True)
            df_indexed.columns = ['Date'] + [symbol for symbol in indexed_data.keys()]
            df_indexed['Date'] = pd.to_datetime(df_indexed['Date'], errors='coerce')
    
            available_stocks = [stock for stock in selected_comparison_stocks if stock in df_indexed.columns]
            if available_stocks:
                df_indexed_filtered = df_indexed[['Date'] + available_stocks]
                fig_indexed = px.line(df_indexed_filtered, x='Date', y=available_stocks, template=plotly_theme)
                fig_indexed.update_layout(dragmode=False)
                fig_indexed.update_yaxes(matches=None, title_text=None)
                fig_indexed.update_xaxes(title_text=None)
                fig_indexed.update_layout(
                    dragmode=False,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        font=dict(size=10)
                    ), legend_title_text=None, margin=dict(l=10, r=10, t=15, b=10))
                
                fig_indexed.add_shape(
                    type='line',
                    x0=df_indexed['Date'].min(),
                    y0=100,
                    x1=df_indexed['Date'].max(),
                    y1=100,
                    line=dict(
                        color="Black",
                        width=2,
                        dash="dot"
                    )
                )
                    
                if benchmark_data is not None and not benchmark_data.empty:
                    fig_indexed.add_scatter(
                        x=benchmark_data.index, y=benchmark_data['Index'],
                        mode='lines', name=str(benchmark_data.index[0].date()),  # Convert Timestamp to a string representation of the date
                        line=dict(dash='dot')
                    )

            else:
                fig_indexed = px.line(title="Selected stocks are not available in the data.", template=plotly_theme)
        else:
            fig_indexed = px.line(title="No data available.", template=plotly_theme)
    
        fig_indexed.update_layout(template=plotly_theme, height=400, showlegend=True)
        return fig_indexed



    @app.callback(
        Output('top-stocks-table', 'children'),
        [Input('risk-tolerance-dropdown', 'value')]
    )
    def get_top_stocks(risk_tolerance):
        if risk_tolerance is None:
            raise PreventUpdate

        # Get the latest batch_id from the database
        latest_batch = db.session.query(StockKPI.batch_id).order_by(
            StockKPI.batch_id.desc()).first()

        if latest_batch is None:
            return html.Div("No stock data available.", style={"color": "red"})

        latest_batch_id = latest_batch[0]  # Extract batch_id from the tuple

        # Fetch top 20 stocks for the selected risk tolerance and latest batch_id
        stock_data = StockKPI.query.filter_by(
            risk_tolerance=risk_tolerance, batch_id=latest_batch_id).all()

        # If no data found
        if not stock_data:
            return html.Div(f"No top stocks available for {risk_tolerance} risk tolerance.", style={"color": "red"})

        # Normalize the momentum for the progress bar
        max_momentum = max(
            [stock.price_momentum for stock in stock_data if stock.price_momentum], default=1)

        # Table headers with info icons and tooltips
        table_header = [
            html.Thead(html.Tr([
                html.Th([
                    "Stock", html.I(className="bi bi-info-circle-fill",
                                    id="stock-info", style={"margin-left": "5px"}),
                    dbc.Tooltip("The stock symbol or ticker for the company.",
                                target="stock-info", placement="top")
                ], style={"width": "100px"}),  # Reduced width for Stock column
                html.Th([
                    "P/E Ratio", html.I(className="bi bi-info-circle-fill",
                                        id="pe-info", style={"margin-left": "0px", "width": "50px"}),
                    dbc.Tooltip("Price-to-Earnings ratio: measures a company's current share price relative to its per-share earnings.",
                                target="pe-info", placement="top")
                ], className="d-none d-md-table-cell"),  # Hide on mobile
                html.Th([
                    "Beta", html.I(className="bi bi-info-circle-fill",
                                   id="beta-info", style={"margin-left": "5px"}),
                    dbc.Tooltip("Beta measures the stock's volatility relative to the overall market.",
                                target="beta-info", placement="top")
                ]),
                html.Th([
                    "ROE", html.I(className="bi bi-info-circle-fill",
                                  id="roe-info", style={"margin-left": "5px"}),
                    dbc.Tooltip("Return on Equity (ROE): shows how effectively a company uses shareholders' equity to generate profit.",
                                target="roe-info", placement="top")
                ]),
                html.Th([
                    "Momentum", html.I(className="bi bi-info-circle-fill",
                                       id="momentum-info", style={"margin-left": "5px"}),
                    dbc.Tooltip("Momentum measures the stock's recent price performance.",
                                target="momentum-info", placement="top")
                ])
            ]))
        ]

        # Build the table rows with progress bars and labels side by side in one row using flexbox
        rows = []
        for idx, stock in enumerate(stock_data):
            # Conditional styling for P/E Ratio (green for low values)
            pe_style = {"backgroundColor": "lightgreen"} if stock.pe_ratio and stock.pe_ratio < 20 else {
                "backgroundColor": "lightcoral"}

            # Normalize the progress bar values
            momentum_normalized = (
                stock.price_momentum / max_momentum) * 100 if stock.price_momentum else 0
            roe_percentage = stock.roe * 100 if stock.roe else 0
            beta_normalized = (stock.beta / 3) * 100 if stock.beta else 0

            # Add row with flexbox layout to place text and progress bar side by side
            rows.append(html.Tr([
                # Fixed and reduced width for Stock column
                html.Td(stock.symbol, style={
                        "width": "20px", "white-space": "nowrap", "text-overflow": "ellipsis", "overflow": "hidden"}),
                html.Td(f"{stock.pe_ratio:.1f}" if stock.pe_ratio else "N/A", style=pe_style,
                        className="d-none d-md-table-cell"),  # Hide on mobile, round to 1 digit after comma

                # Beta column with small number and progress bar
                html.Td([
                    html.Div([
                        html.Span(f"{stock.beta:.1f}", style={"margin-right": "5px", "font-size": "10px",
                                  "min-width": "25px", "text-align": "right"}),  # Fixed width for Beta number
                        dbc.Progress(value=beta_normalized, striped=True, color="info", style={
                                     "height": "20px", "flex-grow": "1"})  # Allow progress bar to take remaining space
                    ], style={"display": "flex", "align-items": "center", "white-space": "nowrap"})  # Prevent wrapping
                ]),

                # ROE column with small number and progress bar
                html.Td([
                    html.Div([
                        html.Span(f"{roe_percentage:.1f}%", style={"margin-right": "5px", "font-size": "10px",
                                  "min-width": "25px", "text-align": "right"}),  # Fixed width for ROE number
                        dbc.Progress(value=roe_percentage, striped=True, color="success", style={
                                     "height": "20px", "flex-grow": "1"})  # Allow progress bar to take remaining space
                    ], style={"display": "flex", "align-items": "center", "white-space": "nowrap"})  # Prevent wrapping
                ]),

                # Momentum column with small number and progress bar
                html.Td([
                    html.Div([
                        html.Span(f"{stock.price_momentum:.1f}", style={"margin-right": "5px", "font-size": "10px",
                                  "min-width": "25px", "text-align": "right"}),  # Fixed width for Momentum number
                        dbc.Progress(value=momentum_normalized, striped=True, color="info", style={
                                     "height": "20px", "flex-grow": "1"})  # Allow progress bar to take remaining space
                    ], style={"display": "flex", "align-items": "center", "white-space": "nowrap"})  # Prevent wrapping
                ])
            ]))

        table_body = [html.Tbody(rows)]

        # Return the complete table with headers and body, responsive for mobile
        return dbc.Table(
            table_header + table_body,
            bordered=True,
            hover=True,
            striped=True,
            responsive=True,  # Enable responsive behavior
            className="table-sm table-responsive"
        )

    from flask import session
    from dash.exceptions import PreventUpdate
    
    
    from dash import no_update

    @app.callback(
        [
            Output('forecast-graph', 'figure'),
            Output('forecast-kpi-output', 'children')
        ],
        [Input('url', 'pathname')],
        [Input('forecast-data-store', 'data')],
        # prevent_initial_call=True
    )
    def display_stored_forecast(pathname, stored_forecast):
        # Display stored forecast only when navigating back to /forecast
        if pathname == '/forecast' and stored_forecast:
            return stored_forecast.get('figure'), stored_forecast.get('kpi_outputs')
        return no_update, no_update
    
    

    @app.callback(Output('simulation-result', 'children'),
                  Input('simulate-button', 'n_clicks'),
                  State('simulation-stock-input', 'value'),
                  State('investment-amount', 'value'),
                  State('investment-date', 'date'),
                  State('plotly-theme-store', 'data'))
    def simulate_investment(n_clicks, stock_symbol, investment_amount, investment_date, plotly_theme):
        if n_clicks and stock_symbol and investment_amount and investment_date:
            investment_date = pd.to_datetime(investment_date)
            end_date = pd.to_datetime('today')
            data = yf.download(
                stock_symbol, start=investment_date, end=end_date)

            if not data.empty:
                initial_price = data['Close'].iloc[0]
                current_price = data['Close'].iloc[-1]
                shares_bought = investment_amount / initial_price
                current_value = shares_bought * current_price
                profit = current_value - investment_amount

                # Create waterfall chart
                fig_waterfall = go.Figure(go.Waterfall(
                    name="Investment Analysis",
                    orientation="v",
                    measure=["absolute", "relative", "total"],
                    x=["Initial Investment", "Profit/Loss", "Current Value"],
                    y=[investment_amount, profit, current_value],
                    text=[f"${investment_amount:.2f}",
                          f"${profit:.2f}", f"${current_value:.2f}"],
                    textposition="inside",
                    insidetextfont={"color": "white"},
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    decreasing={"marker": {"color": "red"}},
                    increasing={"marker": {"color": "green"}},
                    totals={"marker": {"color": "grey"}}
                ))
                fig_waterfall.update_layout(
                    showlegend=False,
                    template=plotly_theme,
                    yaxis=dict(visible=False),
                    margin=dict(t=100, l=10, r=10, b=10),
                    dragmode=False
                )

                return html.Div([
                    html.P(
                        f"Initial Investment Amount: ${investment_amount:.2f}", className='mb-2'),
                    html.P(
                        f"Shares Bought: {shares_bought:.2f}", className='mb-2'),
                    html.P(
                        f"Current Value: ${current_value:.2f}", className='mb-2'),
                    html.P(f"Profit: ${profit:.2f}", className='mb-2'),
                    dcc.Graph(figure=fig_waterfall)
                ])
            else:
                return html.Div([
                    html.P(
                        f"No data available for {stock_symbol} from {investment_date.strftime('%Y-%m-%d')}", className='mb-2')
                ])
        return dash.no_update
    
    


    @app.callback(
        [Output('conversation-store', 'data'),
          Output('chatbot-conversation', 'children'),
          Output('chatbot-input', 'value')],
        [Input('send-button', 'n_clicks')],
        [State('chatbot-input', 'value'),
          State('conversation-store', 'data'),
          State('login-username-store', 'data'),
          # Get the selected watchlist
          State('saved-watchlists-dropdown', 'value'),
          State('individual-stocks-store', 'data')],     # Get stocks from the selected watchlist
        prevent_initial_call=True
    )
    def manage_chatbot_interaction(send_clicks, user_input, conversation_history, username, selected_watchlist, watchlist_stocks):
        from openai import OpenAI
        from dotenv import load_dotenv
        import os
        load_dotenv()
        open_api_key = os.getenv('OPEN_API_KEY')

        client = OpenAI(api_key=open_api_key)

        # Define the system message for context
        system_message = {"role": "system",
                          "content": "You are a helpful stock financial advisor."}

        # Initialize conversation history if it's not already set
        if conversation_history is None:
            conversation_history = [system_message]

        if send_clicks and send_clicks > 0 and user_input:
            # Append the user's input to the conversation history
            conversation_history.append(
                {"role": "user", "content": user_input})

            # If the input contains the keyword 'performance' and the user is logged in
            if "performance" in user_input.lower() and username:
                if selected_watchlist and watchlist_stocks:
                    # Fetch stock performance for the selected watchlist
                    performance_data = ut.get_stock_performance(
                        watchlist_stocks)
                    performance_summaries = [
                        f"{symbol}: Latest Close - ${data['latest_close']:.2f}" if data[
                            'latest_close'] is not None else f"{symbol}: Latest Close - N/A"
                        for symbol, data in performance_data.items()
                    ]
                    response = f"Here is the performance data for the stocks in your selected watchlist: {'; '.join(performance_summaries)}."
                else:
                    response = "You don't have a watchlist selected to show performance data."
            else:
                # Use OpenAI to generate a response for other queries
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=conversation_history,
                )
                response = completion.choices[0].message.content

            # Append the assistant's response to the conversation history
            conversation_history.append(
                {"role": "assistant", "content": response})

            # Update the conversation display with the user's input and assistant's response
            conversation_display = []
            for message in conversation_history:
                if message["role"] == "user":
                    conversation_display.append(
                        html.P(f"YOU: {message['content']}", className='user'))
                elif message["role"] == "assistant":
                    conversation_display.append(
                        html.Div(
                            [
                                html.Span("🤖", className="robot-avatar",
                                          style={"margin-right": "10px"}),
                                html.Span(
                                    f"{message['content']}", className='chatbot-text'),
                            ],
                            className="chatbot-response fade-in"
                        )
                    )

            # Clear the chatbot input after responding
            return conversation_history, conversation_display, ""

        # If no new input, return the current state without updates
        return conversation_history, dash.no_update, dash.no_update

    @app.callback(
        Output('analyst-recommendations-content', 'children'),
        [Input('individual-stocks-store', 'data'),
          Input('plotly-theme-store', 'data')]
    )
    def update_analyst_recommendations(stock_symbols, plotly_theme):
        if not stock_symbols:
            return html.P("Please select stocks to view their analyst recommendations.")

        recommendations_content = []

        # Add the text to be displayed at the top
        recommendations_content.append(
            html.P([
                "For more information on how to interpret these ratings, please visit ",
                html.A(
                    "this article", href="https://finance.yahoo.com/news/buy-sell-hold-stock-analyst-180414724.html", target="_blank"),
                "."
            ], className='mt-2')
        )

        for symbol in stock_symbols:
            # df = ut.fetch_analyst_recommendations(symbol)
            df = fetch_analyst_reco_with_cache(symbol)

            if not df.empty:
                fig = ut.generate_recommendations_heatmap(df, plotly_theme)
                recommendations_content.append(
                    html.H4(f"{symbol}", className='mt-3'))
                recommendations_content.append(dcc.Graph(figure=fig))
            else:
                recommendations_content.append(
                    html.P(f"No analyst recommendations found for {symbol}."))

        return recommendations_content
    
    


    

    @app.callback(
        [Output({'type': 'additional-news', 'index': MATCH}, 'children'),
          Output({'type': 'load-more-button', 'index': MATCH}, 'children'),
          Output({'type': 'load-more-button', 'index': MATCH}, 'style')],
        [Input({'type': 'load-more-button', 'index': MATCH}, 'n_clicks')],
        [State({'type': 'load-more-button', 'index': MATCH}, 'id'),
          State({'type': 'additional-news', 'index': MATCH}, 'children')]
    )
    def load_more_articles(n_clicks, button_id, current_articles):
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate

        symbol = button_id['index']
        ticker = yf.Ticker(symbol)
        news = ticker.news

        if not news or len(news) <= 4:
            return dash.no_update, dash.no_update, dash.no_update

        if current_articles is None:
            current_articles = []

        # Increase the max articles by 4 each time the button is clicked
        max_articles = (n_clicks + 1) * 4
        additional_articles = []

        for article in news[4:max_articles]:
            related_tickers = ", ".join(article.get('relatedTickers', []))
            publisher = article.get('publisher', 'Unknown Publisher')

            news_card = dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H5(
                            html.A(article['title'], href=article['link'], target="_blank")),
                        html.Img(
                            src=article['thumbnail']['resolutions'][0]['url'],
                            style={"max-width": "150px",
                                    "height": "auto", "margin-bottom": "10px"}
                        ) if 'thumbnail' in article else html.Div(),
                        html.P(
                            f"Related Tickers: {related_tickers}" if related_tickers else "No related tickers available."),
                        html.Footer(
                            f"Published by: {publisher} | Published at: {datetime.utcfromtimestamp(article['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')}",
                            style={"font-size": "12px", "margin-top": "auto"}
                        )
                    ], style={"min-height": "250px", "max-height": "350px", "display": "flex", "flex-direction": "column"})
                ),
                xs=12, md=6,  # Full width on mobile, half width on desktop
                className="mb-2"
            )
            additional_articles.append(news_card)

        if max_articles >= len(news):
            return dbc.Row(additional_articles), "No more articles", {'display': 'none'}

        return dbc.Row(additional_articles), "Load More", dash.no_update

    @app.callback(
        [Output('financials-modal', 'is_open'),
          Output('financials-modal-title', 'children'),
          Output('financials-modal-body', 'children')],
        [Input({'type': 'stock-symbol', 'index': ALL}, 'n_clicks')],
        [State('individual-stocks-store', 'data'),
          State('financials-modal', 'is_open')]
    )
    def display_financials_modal(n_clicks, watchlist, is_open):
        ctx = dash.callback_context

        # Prevent the modal from opening if no click or all n_clicks are None
        if not ctx.triggered or not watchlist or not any(n_clicks):
            raise PreventUpdate

        # Get the ID of the triggered button
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'stock-symbol' not in triggered_id:
            raise PreventUpdate  # Ensure the modal only opens when a stock symbol is clicked

        # Extract the index from the triggered ID
        index = json.loads(triggered_id)['index']
        stock_symbol = watchlist[index]

        # Fetch financials data
        ticker = yf.Ticker(stock_symbol)
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow
        info = ticker.info

        if financials is not None and not financials.empty:
            income_statement_content = ut.create_financials_table(financials)
            balance_sheet_content = ut.create_financials_table(balance_sheet)
            cashflow_content = ut.create_financials_table(cashflow)
            company_info_content = ut.create_company_info(info)

            # Create tabs for the modal
            modal_content = dbc.Tabs([
                dbc.Tab(company_info_content, label="Company Info"),
                dbc.Tab(balance_sheet_content, label="Balance Sheet"),
                dbc.Tab(income_statement_content, label="Income Statement"),
                dbc.Tab(cashflow_content, label="Cash Flow"),
            ], active_tab="tab-0")  # Set the first tab as active by default
        else:
            modal_content = html.P(
                "No financial data available for this stock.")

        return True, f"Financials for {stock_symbol}", modal_content

    @app.callback(
        Output('financials-modal', 'is_open', allow_duplicate=True),
        [Input('close-financials-modal', 'n_clicks')],
        [State('financials-modal', 'is_open')],
        prevent_initial_call=True
    )
    def close_financials_modal(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        [Output("chatbot-modal", "is_open"),
          Output("conversation-store", "data", allow_duplicate=True),
          Output("chatbot-conversation", "children", allow_duplicate=True)],
        [Input("open-chatbot-button", "n_clicks"),
          Input("clear-button", "n_clicks")],
        [State("chatbot-modal", "is_open"),
          State('conversation-store', 'data'),
          State('login-username-store', 'data'),
          # Get the selected watchlist
          State('saved-watchlists-dropdown', 'value'),
          State('individual-stocks-store', 'data')],     # Get stocks from the selected watchlist
        prevent_initial_call=True
    )
    def toggle_or_clear_chatbot(open_click, clear_click, is_open, conversation_history, username, selected_watchlist, watchlist_stocks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open, conversation_history, dash.no_update

        # If the chatbot button is clicked or the clear button is clicked
        if ctx.triggered[0]["prop_id"] in ["open-chatbot-button.n_clicks", "clear-button.n_clicks"]:
            # Handle opening and closing the modal
            if ctx.triggered[0]["prop_id"] == "open-chatbot-button.n_clicks" and is_open:
                return not is_open, conversation_history, dash.no_update

            watchlist_message = ""
            personalized_greeting = "Hello! My name is Financio, your financial advisor 🤖."

            # If the user is logged in
            if username:
                # Check if the watchlist is selected and stocks are available
                if selected_watchlist and watchlist_stocks:
                    # Generate the stock performance summaries for the selected watchlist
                    performance_data = ut.get_stock_performance(
                        watchlist_stocks)
                    performance_summaries = [
                        f"{symbol}: Latest - ${data['latest_close']:.2f}"
                        for symbol, data in performance_data.items()
                    ]
                    watchlist_message = f"Here are the stocks on your selected watchlist and their performance: {'; '.join(performance_summaries)}."
                else:
                    watchlist_message = "You currently don't have a watchlist selected."

                # Personalize greeting for logged-in users
                personalized_greeting = f"Hello, {username}! My name is Financio, your financial advisor 🤖."
            else:
                # Handle the case when the user is not logged in
                watchlist_message = "You're not logged in, so I don't have access to your watchlist."

            # Initialize the conversation with a personalized message
            conversation_history = [
                {"role": "system", "content": "You are a helpful stock financial advisor."}]
            introduction_message = f"{personalized_greeting} How can I assist you today? {watchlist_message}"
            conversation_history.append(
                {"role": "assistant", "content": introduction_message})

            conversation_display = [
                html.Div(
                    [
                        html.Span("🤖", className="robot-avatar",
                                  style={"margin-right": "10px"}),
                        html.Span(f"{introduction_message}",
                                  className='chatbot-text'),
                    ],
                    className="chatbot-response fade-in"
                )
            ]
            return True, conversation_history, conversation_display

        return is_open, conversation_history, dash.no_update


    @app.callback(
        [
            Output('forecast-graph', 'figure', allow_duplicate=True),
            Output('forecast-stock-warning', 'children'),
            Output('forecast-kpi-output', 'children', allow_duplicate=True),
            Output('forecast-data-store', 'data'),
            Output('forecast-attempt-store', 'data')
        ],
        [
            Input('url', 'pathname'),  # Ensure callback only triggers when on the correct page
            Input('generate-forecast-button', 'n_clicks'),
            Input('plotly-theme-store', 'data')
        ],
        [
            State('forecast-stock-input', 'value'),
            State('forecast-horizon-input', 'value'),
            State('predefined-ranges', 'value'),
            State('login-status', 'data'),
            State('login-username-store', 'data'),
            State('forecast-attempt-store', 'data')
        ],
        prevent_initial_call=True
    )
    def generate_forecasts(pathname, n_clicks, plotly_theme, selected_stocks, horizon, predefined_range, login_status, username, forecast_attempt):
        # Only execute if on the correct page
        if pathname != '/forecast' or n_clicks is None:
            raise PreventUpdate
    
        if n_clicks is None:
            raise PreventUpdate
    
        # Initialize or increment forecast_attempt based on login status
        if not login_status or not username:
            forecast_attempt = session.get('forecast_attempts', 0)
            if forecast_attempt >= 2:
                return no_update, "You've already generated two free forecasts. Please upgrade for more.", no_update, no_update, forecast_attempt
            forecast_attempt += 1
            session['forecast_attempts'] = forecast_attempt
    
        elif username:
            user = User.query.filter_by(username=username).first()
            if user and user.subscription_status == 'free' and user.forecast_attempts >= 2:
                return no_update, "You've already generated two free forecasts. Please upgrade for more.", no_update, no_update, forecast_attempt
            if user and user.subscription_status == 'free':
                user.forecast_attempts += 1
                db.session.commit()
                forecast_attempt = user.forecast_attempts
    
        # Check for selected stocks
        if not selected_stocks:
            return no_update, "Please select at least one stock.", no_update, no_update, forecast_attempt
        if len(selected_stocks) > 3:
            return no_update, "Please select up to 3 stocks only.", no_update, no_update, forecast_attempt
    
        # Generate forecast data
        forecast_data = ut.generate_forecast_data(selected_stocks, horizon)
        forecast_figures = []
        kpi_outputs = []
        today = pd.to_datetime('today')
    
        for symbol in selected_stocks:
            if 'error' in forecast_data[symbol]:
                continue
    
            # Ensure that each KPI value is rounded appropriately
            kpi = forecast_data[symbol]['kpi']
            kpi['expected_price'] = round(kpi['expected_price'])  # Round to integer
            kpi['latest_actual_price'] = round(kpi['latest_actual_price'])  # Round to integer
            kpi['upper_bound'] = round(kpi['upper_bound'])  # Round to integer
            kpi['lower_bound'] = round(kpi['lower_bound'])  # Round to integer
            kpi['percentage_difference'] = round(kpi['percentage_difference'], 2)  # Keep two decimals for percentage
    
            # Generate figure and KPI card
            fig = ut.create_forecast_figure(forecast_data[symbol], plotly_theme, symbol, predefined_range, today)
            kpi_output = ut.create_kpi_card(kpi, symbol)  # Pass integers and percentages
    
            forecast_figures.append(fig)
            kpi_outputs.append(kpi_output)
    
        combined_fig = ut.combine_forecast_figures(forecast_figures, plotly_theme)
    
        # Store both figure and KPI data
        forecast_store_data = {
            'figure': combined_fig,
            'kpi_outputs': kpi_outputs
        }
    
        return combined_fig, "", kpi_outputs, forecast_store_data, forecast_attempt

    

    app.clientside_callback(
        """
        function(n1, n2, n3, n4, n5, is_open1, is_open2, is_open3, is_open4, is_open5) {
            let triggered_id = dash_clientside.callback_context.triggered[0].prop_id.split('.')[0];
    
            return [
                triggered_id === 'faq-q1' ? !is_open1 : is_open1,
                triggered_id === 'faq-q2' ? !is_open2 : is_open2,
                triggered_id === 'faq-q3' ? !is_open3 : is_open3,
                triggered_id === 'faq-q4' ? !is_open4 : is_open4,
                triggered_id === 'faq-q5' ? !is_open5 : is_open5
            ];
        }
        """,
        [Output("collapse-q1", "is_open"),
         Output("collapse-q2", "is_open"),
         Output("collapse-q3", "is_open"),
         Output("collapse-q4", "is_open"),
         Output("collapse-q5", "is_open")],
        [Input("faq-q1", "n_clicks"),
         Input("faq-q2", "n_clicks"),
         Input("faq-q3", "n_clicks"),
         Input("faq-q4", "n_clicks"),
         Input("faq-q5", "n_clicks")],
        [State("collapse-q1", "is_open"),
         State("collapse-q2", "is_open"),
         State("collapse-q3", "is_open"),
         State("collapse-q4", "is_open"),
         State("collapse-q5", "is_open")]
    )

    app.clientside_callback(
        """
        function(n_clicks, is_open) {
            if (n_clicks) {
                return !is_open;
            }
            return is_open;
        }
        """,
        Output("toc-collapse", "is_open"),
        Input("toc-toggle", "n_clicks"),
        State("toc-collapse", "is_open")
    )
