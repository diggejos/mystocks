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
from models import User, bcrypt, db, Watchlist, StockKPI # Make sure to import the app instance
from dash.exceptions import PreventUpdate
from layouts import themes

def get_data_callbacks(app, server):
    
    @app.callback(
        [Output('individual-stocks-store', 'data', allow_duplicate=True),
         Output('watchlist-summary', 'children'),
         Output('stock-graph', 'figure'),
         Output('stock-graph', 'style'),
         Output('stock-news', 'children'),
         Output('indexed-comparison-graph', 'figure'),
         Output('indexed-comparison-stock-dropdown', 'options'),
         Output('indexed-comparison-stock-dropdown', 'value'),
         Output('prices-stock-dropdown', 'options'),
         Output('prices-stock-dropdown', 'value'),
         Output('news-stock-dropdown', 'options'),
         Output('news-stock-dropdown', 'value'),
         Output('stock-suggestions-input', 'value')],  # Updated this line
        [Input('add-stock-button', 'n_clicks'),
         Input('reset-stocks-button', 'n_clicks'),
         Input('refresh-data-icon', 'n_clicks'),
         Input({'type': 'remove-stock', 'index': ALL}, 'n_clicks'),
         Input('chart-type', 'value'),
         Input('movag_input', 'value'),
         Input('benchmark-selection', 'value'),
         Input('predefined-ranges', 'value'),
         Input('indexed-comparison-stock-dropdown', 'value'),
         Input('prices-stock-dropdown', 'value'),
         Input('news-stock-dropdown', 'value'),
         Input('saved-watchlists-dropdown', 'value'),
         Input('plotly-theme-store', 'data')],
        [State('stock-suggestions-input', 'value'),
         State('individual-stocks-store', 'data')],
        prevent_initial_call='initial_duplicate'
    )
    def update_watchlist_and_graphs(add_n_clicks, reset_n_clicks, refresh_n_clicks, remove_clicks, chart_type, movag_input, benchmark_selection, predefined_range, selected_comparison_stocks, selected_prices_stocks, selected_news_stocks ,selected_watchlist, plotly_theme, new_stock, individual_stocks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,dash.no_update,dash.no_update)
    
        trigger = ctx.triggered[0]['prop_id']
    
        # Check if the watchlist dropdown triggered the update
        if 'saved-watchlists-dropdown' in trigger and selected_watchlist:
            watchlist = db.session.get(Watchlist, selected_watchlist)
            if watchlist:
                individual_stocks = json.loads(watchlist.stocks)
                selected_prices_stocks = individual_stocks[:5]
                selected_comparison_stocks = individual_stocks[:5]
                selected_news_stocks = individual_stocks[:5]
    
    
        # Handle stock addition using the selected ticker from input
        if 'add-stock-button' in trigger and new_stock:
            new_stock = new_stock.upper().strip()
            if new_stock and new_stock not in individual_stocks:
                individual_stocks.append(new_stock)
        elif 'reset-stocks-button' in trigger:
            individual_stocks = []
        elif 'refresh-data-icon' in trigger:
            pass
        elif 'remove-stock' in trigger:
            index_to_remove = json.loads(trigger.split('.')[0])['index']
            if 0 <= index_to_remove < len(individual_stocks):
                individual_stocks.pop(index_to_remove)
    
        if benchmark_selection in individual_stocks:
            individual_stocks.remove(benchmark_selection)
    
        options = [{'label': stock, 'value': stock} for stock in individual_stocks]
    
        # Update selected stocks for Prices and Indexed Comparison dropdowns
        if selected_comparison_stocks:
            selected_comparison_stocks = [stock for stock in selected_comparison_stocks if stock in individual_stocks]
        else:
            selected_comparison_stocks = individual_stocks[:5]
    
        if selected_prices_stocks:
            selected_prices_stocks = [stock for stock in selected_prices_stocks if stock in individual_stocks]
        else:
            selected_prices_stocks = individual_stocks[:5]
            
        if selected_news_stocks:
            selected_news_stocks = [stock for stock in selected_news_stocks if stock in individual_stocks]
        else:
            selected_news_stocks = individual_stocks[:5]
    
        if not individual_stocks and benchmark_selection == 'None':
            return (
                individual_stocks,
                ut.generate_watchlist_table(individual_stocks),
                px.line(title="Please add at least one stock symbol.", template=plotly_theme),
                {'height': '400px'},
                html.Div("Please add at least one stock symbol."),
                px.line(title="Please add at least one stock symbol.", template=plotly_theme),
                options,
                selected_comparison_stocks,
                options,
                selected_prices_stocks,
                options,
                selected_news_stocks,
                ""
            )
    
        today = pd.to_datetime('today')
    
        # Determine the start date and interval based on predefined range
        if predefined_range == '5D_15m':
            start_date = today - timedelta(days=5)
            interval = '15m'
        elif predefined_range == '1D_15m':
            start_date = today - timedelta(hours=24)
            interval = '5m'
        elif predefined_range == 'YTD':
            start_date = datetime(today.year, 1, 1)
            interval = '1d'
        elif predefined_range == '1M':
            start_date = today - timedelta(days=30)
            interval = '1d'
        elif predefined_range == '3M':
            start_date = today - timedelta(days=3 * 30)
            interval = '1d'
        elif predefined_range == '12M':
            start_date = today - timedelta(days=365)
            interval = '1d'
        elif predefined_range == '24M':
            start_date = today - timedelta(days=730)
            interval = '1d'
        elif predefined_range == '5Y':
            start_date = today - timedelta(days=1825)
            interval = '1d'
        elif predefined_range == '10Y':
            start_date = today - timedelta(days=3650)
            interval = '1d'
        else:
            start_date = pd.to_datetime('2024-01-01')
            interval = '1d'
    
        end_date = today
    
        # Fetch stock data from Yahoo Finance
        data = []
        for symbol in individual_stocks:
            try:
                df = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        
                # Conditional check for intraday data
                if predefined_range in ['1D_15m']:
                    # Check if there's data in the last 24 hours
                    if df.empty:
                        print(f"No intraday data found for {symbol} in the last 24 hours. Skipping to the next stock.")
                        continue  # Skip to the next stock if no intraday data is available
        
                # Continue processing the data if not intraday or if data is available
                df.reset_index(inplace=True)
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                else:
                    df['Datetime'] = pd.to_datetime(df['Datetime'])
                    df.set_index('Datetime', inplace=True)
        
                df = df.tz_localize(None)
                df['Stock'] = symbol
                df['30D_MA'] = df.groupby('Stock')['Close'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
                df['100D_MA'] = df.groupby('Stock')['Close'].transform(lambda x: x.rolling(window=100, min_periods=1).mean())
                data.append(df)
    
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                continue
    
        if not data and benchmark_selection == 'None':
            return (
                individual_stocks,
                ut.generate_watchlist_table(individual_stocks),
                px.line(title="No data found for the given stock symbols and date range.", template=plotly_theme),
                {'height': '400px'},
                html.Div("No news found for the given stock symbols."),
                px.line(title="No data found for the given stock symbols and date range.", template=plotly_theme),
                options,
                selected_comparison_stocks,
                options,
                selected_prices_stocks,
                options,
                selected_news_stocks,
                ""
            )
    
        df_all = pd.concat(data) if data else pd.DataFrame()
    
    
        # Create indexed data for comparison
        indexed_data = {}
        for symbol in individual_stocks:
            if symbol in df_all['Stock'].unique():
                df_stock = df_all[df_all['Stock'] == symbol].copy()
                df_stock['Index'] = df_stock['Close'] / df_stock['Close'].iloc[0] * 100
                indexed_data[symbol] = df_stock[['Index']].rename(columns={"Index": symbol})
    
        if benchmark_selection != 'None':
            benchmark_data = yf.download(benchmark_selection, start=start_date, end=end_date, interval=interval)
            if not benchmark_data.empty:
                benchmark_data.reset_index(inplace=True)
                benchmark_data['Index'] = benchmark_data['Close'] / benchmark_data['Close'].iloc[0] * 100
    
        if indexed_data:
            df_indexed = pd.concat(indexed_data, axis=1)
            df_indexed.reset_index(inplace=True)
            df_indexed.columns = ['Date'] + [symbol for symbol in indexed_data.keys()]
            df_indexed['Date'] = pd.to_datetime(df_indexed['Date'], errors='coerce')
    
            available_stocks = [stock for stock in selected_comparison_stocks if stock in df_indexed.columns]
            if not available_stocks:
                return (
                    individual_stocks,
                    ut.generate_watchlist_table(individual_stocks),
                    px.line(title="Selected stocks are not available in the data.", template=plotly_theme),
                    {'height': '400px'},
                    html.Div("No data found for the selected comparison stocks."),
                    px.line(title="Selected stocks are not available in the data.", template=plotly_theme),
                    options,
                    selected_comparison_stocks,
                    options,
                    selected_prices_stocks,
                    ""
                )
    
            df_indexed_filtered = df_indexed[['Date'] + available_stocks]
    
            fig_indexed = px.line(df_indexed_filtered, x='Date', y=available_stocks, template=plotly_theme)
            fig_indexed.update_yaxes(matches=None, title_text=None)
            fig_indexed.update_xaxes(title_text=None)
            fig_indexed.update_layout(legend=dict(
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
        
          
            if benchmark_selection != 'None':
                fig_indexed.add_scatter(x=benchmark_data['Date'], y=benchmark_data['Index'], mode='lines',
                                        name=benchmark_selection, line=dict(dash='dot'))
        else:
            fig_indexed = px.line(title="No data available.", template=plotly_theme)
    
        # Prepare the stock price graph
        df_prices_filtered = df_all[df_all['Stock'].isin(selected_prices_stocks)]
        num_stocks = len(selected_prices_stocks)
        graph_height = 400 * num_stocks
    
        fig_stock = make_subplots(
            rows=num_stocks,
            cols=1,
            shared_xaxes=False,
            vertical_spacing=0.05,
            subplot_titles=selected_prices_stocks,
            specs=[[{"secondary_y": True}]] * num_stocks,
        )
    
        for i, symbol in enumerate(selected_prices_stocks):
            df_stock = df_prices_filtered[df_prices_filtered['Stock'] == symbol]
    
            if not df_stock.empty and len(df_stock) > 1:  # Ensure there's enough data
                if chart_type == 'line':
                    fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['Close'], name=f'{symbol} Close',
                                                    line=dict(color='blue')), row=i + 1, col=1)
    
                    last_close = df_stock['Close'].iloc[-2]
                    latest_close = df_stock['Close'].iloc[-1]
                    change_percent = ((latest_close - last_close) / last_close) * 100
    
                    fig_stock.add_trace(go.Scatter(
                        x=[df_stock.index[-1]],
                        y=[latest_close],
                        mode='markers',
                        marker=dict(color='red', size=10),
                        name=f'{symbol} Last Price'
                    ), row=i + 1, col=1)
    
                    latest_timestamp = df_stock.index[-1]
                    fig_stock.add_annotation(
                        x=latest_timestamp,
                        y=latest_close,
                        text=f"{latest_close:.2f} ({change_percent:.2f}%)<br>{latest_timestamp.strftime('%Y-%m-%d')}",
                        showarrow=True,
                        arrowhead=None,
                        ax=20,
                        ay=-40,
                        row=i + 1,
                        col=1,
                        font=dict(color="blue", size=12),
                        bgcolor='white'
                    )
    
                    fig_stock.add_shape(
                        type="line",
                        x0=df_stock.index.min(),
                        x1=df_stock.index.max(),
                        y0=latest_close,
                        y1=latest_close,
                        line=dict(
                            color="red",
                            width=2,
                            dash="dot"
                        ),
                        row=i + 1, col=1
                    )
                elif chart_type == 'candlestick':
                    fig_stock.add_trace(go.Candlestick(
                        x=df_stock.index,
                        open=df_stock['Open'],
                        high=df_stock['High'],
                        low=df_stock['Low'],
                        close=df_stock['Close'],
                        name=f'{symbol} Candlestick'), row=i + 1, col=1)
    
                    fig_stock.update_xaxes(rangeslider={'visible': False}, row=i + 1, col=1)
    
                if 'Volume' in movag_input:
                    fig_stock.add_trace(go.Bar(x=df_stock.index, y=df_stock['Volume'], name=f'{symbol} Volume',
                                                marker=dict(color='gray'), opacity=0.3), row=i + 1, col=1, secondary_y=True)
                    fig_stock.update_yaxes(showgrid=False, secondary_y=True, row=i + 1, col=1)
    
                if '30D_MA' in movag_input:
                    fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['30D_MA'], name=f'{symbol} 30D MA',
                                                    line=dict(color='green')), row=i + 1, col=1)
    
                if '100D_MA' in movag_input:
                    fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['100D_MA'], name=f'{symbol} 100D MA',
                                                    line=dict(color='red')), row=i + 1, col=1)
    
        fig_stock.update_layout(template=plotly_theme, height=graph_height, showlegend=False,
                                margin=dict(l=40, r=40, t=40, b=40))
        fig_stock.update_yaxes(title_text=None, secondary_y=False)
        fig_stock.update_yaxes(title_text=None, secondary_y=True, showgrid=False)
    
        # Fetch related news for the stocks in the watchlist
        news_content = ut.fetch_news(selected_news_stocks)
    
    
        return (
            individual_stocks,
            ut.generate_watchlist_table(individual_stocks),
            fig_stock,
            {'height': f'{graph_height}px', 'overflow': 'auto'},
            news_content,
            fig_indexed,
            options,
            selected_comparison_stocks,
            options,
            selected_prices_stocks,
            options,
            selected_news_stocks,
            ""
        )

    @app.callback(
        Output('top-stocks-table', 'children'),
        [Input('risk-tolerance-dropdown', 'value')]
    )
    def get_top_stocks(risk_tolerance):
        if risk_tolerance is None:
            raise PreventUpdate
    
        # Get the latest batch_id from the database
        latest_batch = db.session.query(StockKPI.batch_id).order_by(StockKPI.batch_id.desc()).first()
    
        if latest_batch is None:
            return html.Div("No stock data available.", style={"color": "red"})
    
        latest_batch_id = latest_batch[0]  # Extract batch_id from the tuple
    
        # Fetch top 20 stocks for the selected risk tolerance and latest batch_id
        stock_data = StockKPI.query.filter_by(risk_tolerance=risk_tolerance, batch_id=latest_batch_id).all()
    
        # If no data found
        if not stock_data:
            return html.Div(f"No top stocks available for {risk_tolerance} risk tolerance.", style={"color": "red"})
    
        # Normalize the momentum for the progress bar
        max_momentum = max([stock.price_momentum for stock in stock_data if stock.price_momentum], default=1)
    
    
        # Table headers with info icons and tooltips
        table_header = [
            html.Thead(html.Tr([
                html.Th([
                    "Stock", html.I(className="bi bi-info-circle-fill", id="stock-info", style={"margin-left": "5px"}), 
                    dbc.Tooltip("The stock symbol or ticker for the company.", target="stock-info", placement="top")
                ], style={"width": "100px"}),  # Reduced width for Stock column
                html.Th([
                    "P/E Ratio", html.I(className="bi bi-info-circle-fill", id="pe-info", style={"margin-left": "0px","width":"50px"}), 
                    dbc.Tooltip("Price-to-Earnings ratio: measures a company's current share price relative to its per-share earnings.", target="pe-info", placement="top")
                ], className="d-none d-md-table-cell"),  # Hide on mobile
                html.Th([
                    "Beta", html.I(className="bi bi-info-circle-fill", id="beta-info", style={"margin-left": "5px"}), 
                    dbc.Tooltip("Beta measures the stock's volatility relative to the overall market.", target="beta-info", placement="top")
                ]),
                html.Th([
                    "ROE", html.I(className="bi bi-info-circle-fill", id="roe-info", style={"margin-left": "5px"}), 
                    dbc.Tooltip("Return on Equity (ROE): shows how effectively a company uses shareholders' equity to generate profit.", target="roe-info", placement="top")
                ]),
                html.Th([
                    "Momentum", html.I(className="bi bi-info-circle-fill", id="momentum-info", style={"margin-left": "5px"}), 
                    dbc.Tooltip("Momentum measures the stock's recent price performance.", target="momentum-info", placement="top")
                ])
            ]))
        ]
    
        # Build the table rows with progress bars and labels side by side in one row using flexbox
        rows = []
        for idx, stock in enumerate(stock_data):
            # Conditional styling for P/E Ratio (green for low values)
            pe_style = {"backgroundColor": "lightgreen"} if stock.pe_ratio and stock.pe_ratio < 20 else {"backgroundColor": "lightcoral"}
    
            # Normalize the progress bar values
            momentum_normalized = (stock.price_momentum / max_momentum) * 100 if stock.price_momentum else 0
            roe_percentage = stock.roe * 100 if stock.roe else 0
            beta_normalized = (stock.beta / 3) * 100 if stock.beta else 0
    
            # Add row with flexbox layout to place text and progress bar side by side
            rows.append(html.Tr([
                html.Td(stock.symbol, style={"width": "20px", "white-space": "nowrap", "text-overflow": "ellipsis", "overflow": "hidden"}),  # Fixed and reduced width for Stock column
                html.Td(f"{stock.pe_ratio:.1f}" if stock.pe_ratio else "N/A", style=pe_style, className="d-none d-md-table-cell"),  # Hide on mobile, round to 1 digit after comma
    
                # Beta column with small number and progress bar
                html.Td([
                    html.Div([
                        html.Span(f"{stock.beta:.1f}", style={"margin-right": "5px", "font-size": "10px", "min-width": "25px", "text-align": "right"}),  # Fixed width for Beta number
                        dbc.Progress(value=beta_normalized, striped=True, color="info", style={"height": "20px", "flex-grow": "1"})  # Allow progress bar to take remaining space
                    ], style={"display": "flex", "align-items": "center", "white-space": "nowrap"})  # Prevent wrapping
                ]),
    
                # ROE column with small number and progress bar
                html.Td([
                    html.Div([
                        html.Span(f"{roe_percentage:.1f}%", style={"margin-right": "5px", "font-size": "10px", "min-width": "25px", "text-align": "right"}),  # Fixed width for ROE number
                        dbc.Progress(value=roe_percentage, striped=True, color="success", style={"height": "20px", "flex-grow": "1"})  # Allow progress bar to take remaining space
                    ], style={"display": "flex", "align-items": "center", "white-space": "nowrap"})  # Prevent wrapping
                ]),
    
                # Momentum column with small number and progress bar
                html.Td([
                    html.Div([
                        html.Span(f"{stock.price_momentum:.1f}", style={"margin-right": "5px", "font-size": "10px", "min-width": "25px", "text-align": "right"}),  # Fixed width for Momentum number
                        dbc.Progress(value=momentum_normalized, striped=True, color="info", style={"height": "20px", "flex-grow": "1"})  # Allow progress bar to take remaining space
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
    
    @app.callback(
        [Output('forecast-graph', 'figure'),
         Output('forecast-stock-warning', 'children'),
         Output('forecast-data-store', 'data')],
        [Input('generate-forecast-button', 'n_clicks'),
         Input('plotly-theme-store', 'data')],
        [State('forecast-stock-input', 'value'),
         State('forecast-horizon-input', 'value'),
         State('predefined-ranges', 'value')]  # Added predefined-ranges state
    )
    def generate_forecasts(n_clicks, plotly_theme, selected_stocks, horizon, predefined_range):
        if n_clicks and selected_stocks:
            if len(selected_stocks) > 3:
                return dash.no_update, "Please select up to 3 stocks only.", dash.no_update
    
            # Use the modularized forecast generation function
            forecast_data = ut.generate_forecast_data(selected_stocks, horizon)
    
            forecast_figures = []
            today = pd.to_datetime('today')
    
            for symbol in selected_stocks:
                if 'error' in forecast_data[symbol]:
                    # Create an empty figure with an error message
                    fig = go.Figure()
                    fig.update_layout(template=plotly_theme)
                    fig.add_annotation(text=f"Could not generate forecast for {symbol}: {forecast_data[symbol]['error']}", showarrow=False)
                    forecast_figures.append(fig)
                    continue
    
                df = forecast_data[symbol]['historical']
                forecast = forecast_data[symbol]['forecast']
    
                # Set start date based on predefined range
                if predefined_range == 'YTD':
                    start_date = datetime(today.year, 1, 1)
                elif predefined_range == '1M':
                    start_date = today - timedelta(days=30)
                elif predefined_range == '3M':
                    start_date = today - timedelta(days=3 * 30)
                elif predefined_range == '12M':
                    start_date = today - timedelta(days=365)
                elif predefined_range == '24M':
                    start_date = today - timedelta(days=730)
                elif predefined_range == '5Y':
                    start_date = today - timedelta(days=1825)
                else:
                    start_date = pd.to_datetime('2024-01-01')  # Default range if no match
    
                df_filtered = df[df['Date'] >= start_date]
                forecast_filtered = forecast[forecast['ds'] >= start_date]
    
                fig = go.Figure()
                fig.update_layout(template=plotly_theme)
    
                # Add forecast mean line
                fig.add_trace(go.Scatter(
                    x=forecast_filtered['ds'], 
                    y=forecast_filtered['yhat'], 
                    mode='lines', 
                    name=f'{symbol} Forecast',
                    line=dict(color='blue')
                ))
    
                # Add the confidence interval (bandwidth)
                fig.add_trace(go.Scatter(
                    x=forecast_filtered['ds'],
                    y=forecast_filtered['yhat_upper'],
                    mode='lines',
                    name='Upper Bound',
                    line=dict(width=0),
                    showlegend=False
                ))
    
                fig.add_trace(go.Scatter(
                    x=forecast_filtered['ds'],
                    y=forecast_filtered['yhat_lower'],
                    fill='tonexty',  # Fill to the next trace (yhat_upper)
                    mode='lines',
                    name='Lower Bound',
                    line=dict(width=0),
                    fillcolor='rgba(0, 100, 255, 0.2)',  # Light blue fill
                    showlegend=False
                ))
    
                # Add historical data
                fig.add_trace(go.Scatter(
                    x=df_filtered['Date'], 
                    y=df_filtered['Close'], 
                    mode='lines', 
                    name=f'{symbol} Historical',
                    line=dict(color='green')
                ))
    
                fig.update_layout(
                    title=f"Stock Price Forecast for {symbol}",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=600,
                    showlegend=False,
                    template=plotly_theme  # Ensure theme is applied
                )
    
                forecast_figures.append(fig)
    
            if not forecast_figures:
                return dash.no_update, dash.no_update, dash.no_update
    
            # Combine all forecasts into subplots
            combined_fig = make_subplots(
                rows=len(forecast_figures), cols=1,
                shared_xaxes=True, 
                subplot_titles=selected_stocks
            )
    
            for i, fig in enumerate(forecast_figures):
                for trace in fig['data']:
                    combined_fig.add_trace(trace, row=i+1, col=1)
    
            combined_fig.update_layout(
                template=plotly_theme,  # Apply theme to combined figure
                title=None,
                height=400 * len(forecast_figures),
                showlegend=False,
                margin=dict(l=40, r=40, t=40, b=40)
            )
    
            return combined_fig, "", combined_fig
    
        # Ensure the default empty figure also uses the plotly theme
        empty_fig = go.Figure()
        empty_fig.update_layout(template=plotly_theme)
    
        return empty_fig, "", dash.no_update
    

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
            data = yf.download(stock_symbol, start=investment_date, end=end_date)
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
                    text=[f"${investment_amount:.2f}", f"${profit:.2f}", f"${current_value:.2f}"],
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
                    margin=dict(t=100,l=10,r=10,b=10)  
                )
    
                return html.Div([
                    html.P(f"Initial Investment Amount: ${investment_amount:.2f}", className='mb-2'),
                    html.P(f"Shares Bought: {shares_bought:.2f}", className='mb-2'),
                    html.P(f"Current Value: ${current_value:.2f}", className='mb-2'),
                    html.P(f"Profit: ${profit:.2f}", className='mb-2'),
                    dcc.Graph(figure=fig_waterfall)
                ])
            else:
                return html.Div([
                    html.P(f"No data available for {stock_symbol} from {investment_date.strftime('%Y-%m-%d')}", className='mb-2')
                ])
        return dash.no_update
    
    
    @app.callback(
    [Output('saved-watchlists-dropdown', 'options'),
     Output('saved-watchlists-dropdown', 'value'),
     Output('new-watchlist-name', 'value')],
    [Input('login-status', 'data'),
     Input('create-watchlist-button', 'n_clicks'),
     Input('delete-watchlist-button', 'n_clicks')],
    [State('new-watchlist-name', 'value'),
     State('individual-stocks-store', 'data'),
     State('saved-watchlists-dropdown', 'value'),
     State('theme-store', 'data'),  # Get the selected theme (name, not URL)
     State('login-username-store', 'data')]
    )
    def manage_watchlists(login_status, create_clicks, delete_clicks, new_watchlist_name, stocks, selected_watchlist_id, selected_theme, username):
        # Check if the user is logged in, if not clear the dropdown and inputs
        if not username or not login_status:
            return [], None, ''  # Clear the dropdown and inputs if not logged in
        
        # Get the user from the database
        user = User.query.filter_by(username=username).first()
        
        # If no user is found, handle this case
        if user is None:
            # Handle the case where no user is found
            print(f"User with username {username} not found")
            return [], None, ''  # Clear the dropdown and inputs
        
        # Handle watchlist deletion
        if delete_clicks and selected_watchlist_id:
            watchlist = Watchlist.query.get(selected_watchlist_id)
            if watchlist and watchlist.user_id == user.id:
                db.session.delete(watchlist)
                db.session.commit()
                selected_watchlist_id = None  # Clear the selected watchlist after deletion
        
        # Handle watchlist creation or update
        elif create_clicks:
            if selected_watchlist_id:
                # Update existing watchlist if selected
                watchlist = Watchlist.query.get(selected_watchlist_id)
                if watchlist and watchlist.user_id == user.id:
                    watchlist.stocks = json.dumps(stocks)  # Update the stock list in the watchlist
                    db.session.commit()
            elif new_watchlist_name:
                # Create a new watchlist
                new_watchlist = Watchlist(user_id=user.id, name=new_watchlist_name, stocks=json.dumps(stocks))
                db.session.add(new_watchlist)
                db.session.commit()
    
            # Update the theme in the user's profile (save the theme name, not the URL)
            for theme_name, theme_info in themes.items():
                if theme_info['dbc'] == selected_theme:
                    user.theme = theme_name  # Save the theme name (e.g., 'JOURNAL')
                    break
            db.session.commit()
    
        # Load and return updated watchlist options for the user
        watchlists = Watchlist.query.filter_by(user_id=user.id).all()
        watchlist_options = [{'label': w.name, 'value': w.id} for w in watchlists]
    
        return watchlist_options, selected_watchlist_id, ''  # Clear the new watchlist name input after creation or update
    
    
    @app.callback(
        [Output('conversation-store', 'data'),
         Output('chatbot-conversation', 'children'),
         Output('chatbot-input', 'value')],
        [Input('send-button', 'n_clicks')],
        [State('chatbot-input', 'value'),
         State('conversation-store', 'data'),
         State('login-username-store', 'data'),
         State('saved-watchlists-dropdown', 'value'),  # Get the selected watchlist
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
        system_message = {"role": "system", "content": "You are a helpful stock financial advisor."}

        # Initialize conversation history if it's not already set
        if conversation_history is None:
            conversation_history = [system_message]

        if send_clicks and send_clicks > 0 and user_input:
            # Append the user's input to the conversation history
            conversation_history.append({"role": "user", "content": user_input})

            # If the input contains the keyword 'performance' and the user is logged in
            if "performance" in user_input.lower() and username:
                if selected_watchlist and watchlist_stocks:
                    # Fetch stock performance for the selected watchlist
                    performance_data = ut.get_stock_performance(watchlist_stocks)
                    performance_summaries = [
                        f"{symbol}: Latest Close - ${data['latest_close']:.2f}" if data['latest_close'] is not None else f"{symbol}: Latest Close - N/A"
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
            conversation_history.append({"role": "assistant", "content": response})

            # Update the conversation display with the user's input and assistant's response
            conversation_display = []
            for message in conversation_history:
                if message["role"] == "user":
                    conversation_display.append(html.P(f"YOU: {message['content']}", className='user'))
                elif message["role"] == "assistant":
                    conversation_display.append(
                        html.Div(
                            [
                                html.Span("🤖", className="robot-avatar", style={"margin-right": "10px"}),
                                html.Span(f"{message['content']}", className='chatbot-text'),
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
                html.A("this article", href="https://finance.yahoo.com/news/buy-sell-hold-stock-analyst-180414724.html", target="_blank"),
                "."
            ], className='mt-2')
        )
        
        for symbol in stock_symbols:
            df = ut.fetch_analyst_recommendations(symbol)
            if not df.empty:
                fig = ut.generate_recommendations_heatmap(df, plotly_theme)
                recommendations_content.append(html.H4(f"{symbol}", className='mt-3'))
                recommendations_content.append(dcc.Graph(figure=fig))
            else:
                recommendations_content.append(html.P(f"No analyst recommendations found for {symbol}."))
        
        return recommendations_content

    
    @app.callback(
    Output('individual-stocks-store', 'data'),
    [Input('url', 'pathname'),  # Triggers when the page is loaded/refreshed
     Input('saved-watchlists-dropdown', 'value'),
     Input('login-status', 'data')],
    [State('login-username-store', 'data')],
    prevent_initial_call=False  # Ensure this runs on page load
    )
    def load_watchlist(pathname, watchlist_id, login_status, username):
        # Check if the user is logged in and a username is provided
        if login_status and username:
            # Fetch the user from the database
            user = User.query.filter_by(username=username).first()
            
            # Ensure user exists before proceeding
            if user is None:
                print(f"User with username {username} not found")
                return ['AAPL', 'MSFT']  # Default stocks if no user is found
    
            # Load the selected watchlist from the dropdown
            if watchlist_id:
                watchlist = db.session.get(Watchlist, watchlist_id)
                if watchlist and watchlist.user_id == user.id:
                    return json.loads(watchlist.stocks)
    
            # If no specific watchlist is selected, load the default or most recent watchlist
            default_watchlist = Watchlist.query.filter_by(user_id=user.id, is_default=True).first()
            if default_watchlist:
                return json.loads(default_watchlist.stocks)
    
            # If no default watchlist, load the most recent watchlist
            recent_watchlist = Watchlist.query.filter_by(user_id=user.id).order_by(Watchlist.id.desc()).first()
            if recent_watchlist:
                return json.loads(recent_watchlist.stocks)
    
        # If not logged in or no watchlist is selected, return AAPL and MSFT as the default stocks
        return ['AAPL', 'MSFT']
    
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

        # If current_articles is None, initialize it to an empty list
        if current_articles is None:
            current_articles = []

        max_articles = (n_clicks + 1) * 4  # Increase the max articles by 4 each time the button is clicked
        additional_articles = []

        for article in news[4:max_articles]:
            related_tickers = ", ".join(article.get('relatedTickers', []))
            publisher = article.get('publisher', 'Unknown Publisher')  # Get the publisher information
            news_card = dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H5(html.A(article['title'], href=article['link'], target="_blank")),
                        html.Img(src=article['thumbnail']['resolutions'][0]['url'], style={"width": "250px", "height": "auto"})
                        if 'thumbnail' in article else html.Div(),
                        html.P(f"Related Tickers: {related_tickers}" if related_tickers else "No related tickers available."),
                        html.Footer(
                            f"Published by: {publisher} | Published at: {datetime.utcfromtimestamp(article['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')}",
                            style={"margin-bottom": "0px", "padding-bottom": "0px"}
                        )
                    ])
                ),
                xs=12, md=6,  # Full width on mobile, half width on desktop
                className="mb-2"
            )
            additional_articles.append(news_card)

        if max_articles >= len(news):
            # Hide the "Load More" button if all articles have been loaded
            return current_articles + additional_articles, "No more articles", {'display': 'none'}
        
        return current_articles + additional_articles, "Load More", dash.no_update
    
    

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
            modal_content = html.P("No financial data available for this stock.")
    
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
         State('saved-watchlists-dropdown', 'value'),  # Get the selected watchlist
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
                    performance_data = ut.get_stock_performance(watchlist_stocks)
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
            conversation_history = [{"role": "system", "content": "You are a helpful stock financial advisor."}]
            introduction_message = f"{personalized_greeting} How can I assist you today? {watchlist_message}"
            conversation_history.append({"role": "assistant", "content": introduction_message})
    
            conversation_display = [
                html.Div(
                    [
                        html.Span("🤖", className="robot-avatar", style={"margin-right": "10px"}),
                        html.Span(f"{introduction_message}", className='chatbot-text'),
                    ],
                    className="chatbot-response fade-in"
                )
            ]
            return True, conversation_history, conversation_display
    
        return is_open, conversation_history, dash.no_update
    
    @app.callback(
        Output('forecast-graph', 'figure', allow_duplicate=True),
        [Input('active-tab', 'data')],
        [State('forecast-data-store', 'data')],
        prevent_initial_call=True
    )
    def display_stored_forecast(active_tab, stored_forecast):
        if active_tab == '🌡️ Forecast' and stored_forecast:
            return stored_forecast
        return dash.no_update
    
