

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

# List of available Bootstrap themes and corresponding Plotly themes
themes = {
    'YETI': {'dbc': dbc.themes.YETI, 'plotly': 'simple_white'},
    'CERULEAN': {'dbc': dbc.themes.CERULEAN, 'plotly': 'simple_white'},
    'COSMO': {'dbc': dbc.themes.COSMO, 'plotly': 'simple_white'},
    'CYBORG': {'dbc': dbc.themes.CYBORG, 'plotly': 'plotly_dark'},
    'JOURNAL': {'dbc': dbc.themes.JOURNAL, 'plotly': 'simple_white'},
    'LUMEN': {'dbc': dbc.themes.LUMEN, 'plotly': 'simple_white'},
    'MATERIA': {'dbc': dbc.themes.MATERIA, 'plotly': 'simple_white'},
    'MINTY': {'dbc': dbc.themes.MINTY, 'plotly': 'simple_white'},
    'SIMPLEX': {'dbc': dbc.themes.SIMPLEX, 'plotly': 'simple_white'},
    'SKETCHY': {'dbc': dbc.themes.SKETCHY, 'plotly': 'simple_white'},
    'SPACELAB': {'dbc': dbc.themes.SPACELAB, 'plotly': 'simple_white'},
    'VAPOR': {'dbc': dbc.themes.VAPOR, 'plotly': 'plotly_dark'}
}

# Initialize the Dash app with a default Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div([
    dcc.Store(id='individual-stocks-store', data=[]),
    dcc.Store(id='theme-store', data=dbc.themes.BOOTSTRAP),
    dcc.Store(id='plotly-theme-store', data='plotly_white'),
    html.Link(id='theme-switch', rel='stylesheet', href=dbc.themes.BOOTSTRAP),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Dashboard", href="/", active="exact")),
            dbc.NavItem(dbc.NavLink("About", href="/about", active="exact")),
            dbc.DropdownMenu(
                children=[dbc.DropdownMenuItem(theme, id=f'theme-{theme}') for theme in themes],
                nav=True,
                in_navbar=True,
                label="Select Theme"
            ),
        ],
        brand=[
            html.Img(src='/assets/logo_with_transparent_background.png', height='60px'),
            "Josua's Stock Dashboard"
        ],
        brand_href="/",
        color="primary",
        dark=True,
        className="sticky-top mb-4"
    ),
    dcc.Location(id='url', refresh=False),
    dbc.Container(id='page-content', fluid=True)
])

# Layout for the Dashboard page
dashboard_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Label("Stock Symbols:", className="font-weight-bold"),
                        dcc.Dropdown(
                            id='stock-input',
                            options=[
                                {'label': 'Apple (AAPL)', 'value': 'AAPL'},
                                {'label': 'Microsoft (MSFT)', 'value': 'MSFT'},
                                {'label': 'Google (GOOGL)', 'value': 'GOOGL'},
                                {'label': 'Tesla (TSLA)', 'value': 'TSLA'},
                                {'label': 'META (META)', 'value': 'META'},
                                {'label': 'Netflix (NFLX)', 'value': 'NFLX'},
                                {'label': 'MSCI WORLD ETF (URTH)', 'value': 'URTH'},
                                {'label': 'Paypal (PYPL)', 'value': 'PYPL'},
                                {'label': 'Bitcoin (BTC-USD)', 'value': 'BTC-USD'},
                                {'label': 'Uber (UBER)', 'value': 'UBER'}
                            ],
                            value=['AAPL', 'AMZN', 'MSFT'],
                            multi=True,
                            className='form-control'
                        ),
                    ], className='mb-3'),
                    html.Div([
                        html.Label("Add Individual Stock:", className="font-weight-bold"),
                        dcc.Input(
                            id='individual-stock-input',
                            type='text',
                            placeholder='e.g. SPOT for Spotify',
                            debounce=True,
                            className='form-control'
                        ),
                        dbc.Button("Add Stock", id='add-stock-button', color='secondary', className='mt-2 me-2'),
                        dbc.Button("Reset Stocks", id='reset-stocks-button', color='danger', className='mt-2')
                    ], className='mb-3'),
                    html.Div([
                        html.Label("Select Date Range:", className="font-weight-bold"),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date=pd.to_datetime('2023-01-01'),
                            end_date=pd.to_datetime('today'),
                            className='form-control'
                        ),
                    ], className='mb-3'),
                    html.Div([
                        html.Label("Or Select Predefined Range:", className="font-weight-bold"),
                        dcc.RadioItems(
                            id='predefined-ranges',
                            options=[
                                {'label': 'Year to Date', 'value': 'YTD'},
                                {'label': 'Last 12 Months', 'value': '12M'},
                                {'label': 'Last 24 Months', 'value': '24M'},
                                {'label': 'Last 5 Years', 'value': '5Y'},
                                {'label': 'Last 10 Years', 'value': '10Y'}
                            ],
                            value='12M',
                            inline=True,
                            className='form-control',
                            inputStyle={"margin-right": "10px"},
                            labelStyle={"margin-right": "20px"}
                        )
                    ], className='mb-3'),
                    dbc.Button("Submit", id='submit-button', color='primary', className='mt-2'),
                ])
            ]),
        ], width=12, md=3),
        dbc.Col([
            dcc.Tabs(id='tabs', children=[
                dcc.Tab(label='Stock Prices', children=[
                    dbc.Card(
                        dbc.CardBody([
                            dcc.Checklist(
                                id='movag_input',
                                options=['30D Moving Average', '100D Moving Average'],
                                value=[''],
                                inline=True,
                                inputStyle={"margin-right": "10px"},
                                labelStyle={"margin-right": "20px"}
                            ),
                            dcc.Graph(id='stock-graph')
                        ])
                    )
                ]),
                dcc.Tab(label='Stock News', children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(id='stock-news', className='news-container')
                        ])
                    )
                ]),
                dcc.Tab(label='Indexed Comparison', children=[
                    dbc.Card(
                        dbc.CardBody([
                            dcc.RadioItems(
                                id='benchmark-selection',
                                options=[
                                    {'label': 'None', 'value': 'None'},
                                    {'label': 'S&P 500', 'value': '^GSPC'},
                                    {'label': 'NASDAQ 100', 'value': '^NDX'},
                                    {'label': 'SMI', 'value': '^SSMI'}
                                ],
                                value='None',
                                inline=True,
                                className='form-control',
                                inputStyle={"margin-right": "10px"},
                                labelStyle={"margin-right": "20px"}
                            ),
                            dcc.Graph(id='indexed-comparison-graph')
                        ])
                    )
                ]),
                dcc.Tab(label='Investment Simulation', children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.Label("Stock Symbol:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id='simulation-stock-input',
                                    options=[
                                        {'label': 'Apple (AAPL)', 'value': 'AAPL'},
                                        {'label': 'Microsoft (MSFT)', 'value': 'MSFT'},
                                        {'label': 'Google (GOOGL)', 'value': 'GOOGL'},
                                        {'label': 'Tesla (TSLA)', 'value': 'TSLA'},
                                        {'label': 'META (META)', 'value': 'META'},
                                        {'label': 'Netflix (NFLX)', 'value': 'NFLX'},
                                        {'label': 'MSCI WORLD ETF (URTH)', 'value': 'URTH'},
                                        {'label': 'Paypal (PYPL)', 'value': 'PYPL'},
                                        {'label': 'Bitcoin (BTC-USD)', 'value': 'BTC-USD'},
                                        {'label': 'Uber (UBER)', 'value': 'UBER'},
                                    ],
                                    value='AAPL',
                                    className='form-control'
                                ),
                            ], className='mb-3'),
                            html.Div([
                                html.Label("Investment Amount ($):", className="font-weight-bold"),
                                dcc.Input(
                                    id='investment-amount',
                                    type='number',
                                    placeholder='enter Amount',
                                    value=1000,
                                    className='form-control',
                                ),
                            ], className='mb-3'),
                            html.Div([
                                html.Label("Investment Date:", className="font-weight-bold"),
                                dcc.DatePickerSingle(
                                    id='investment-date',
                                    date=pd.to_datetime('2023-01-01'),
                                    className='form-control'
                                ),
                            ], className='mb-3'),
                            dbc.Button("Simulate Investment", id='simulate-button', color='primary', className='mt-2'),
                            html.Div(id='simulation-result', className='mt-4')
                        ])
                    )
                ]),
            ]),
        ], width=12, md=8)
    ], className='mb-4'),
], fluid=True)

# Layout for the About page
about_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.P([
            "This application provides a comprehensive platform for tracking stock market performance and related news. Here are some of the key features:",
            html.Ul([
                html.Li("Track stock prices for multiple companies simultaneously."),
                html.Li("Add individual stock symbols manually."),
                html.Li("View stock prices over a specified date range."),
                html.Li("Fetch and display the latest news articles related to the selected stocks."),
                html.Li("Visualize stock prices with interactive graphs."),
                html.Li("Compare stock performance using  comparison graphs."),
                html.Li("Compare stock performance vs. NASDAQ100, S&P 500 or SMI (Swiss Market Index)"),
                html.Li("Responsive design for use on different devices."),
                html.Li("Historical stock performance simulation in order to derive profit/loss")
            ]),
            "It is built using Dash and Plotly for interactive data visualization. For more information, visit ",
            html.A("Dash documentation", href="https://dash.plotly.com/", target="_blank"),
            "."
        ], className="text-left"))
    ]),
    dbc.Row([
        dbc.Col(html.Figure([
            html.Img(src='/assets/example_stocks.png', className="mt-4"),
            html.Figcaption("An example of the application's dashboard", className="text-left mt-2")
        ], className="text-left"))
    ]),
    dbc.Row([
        dbc.Col(html.Figure([
            html.Img(src='/assets/gif.gif', className="mt-4"),
            html.Figcaption("Get latest Stock news", className="text-left mt-2")
        ], className="text-left"))
    ])
], fluid=True)


# Modify the fetch_news function to update the table style
def fetch_news(api_key, symbols):
    news_content = []
    base_url = "https://newsapi.org/v2/everything"
    
    for symbol in symbols:
        query = f"{symbol} stock"
        response = requests.get(base_url, params={
            'q': query,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 5  # Number of news articles to fetch
        })
        articles = response.json().get('articles', [])
        
        if articles:
            news_content.append(html.H4(f"News for {symbol}", className="mt-4"))
            table_header = [
                html.Thead(html.Tr([
                    html.Th("Title", style={'width': '40%'}),
                    html.Th("Preview", style={'width': '40%'}),
                    html.Th("Source", style={'width': '10%'}),
                    html.Th("Published At", style={'width': '10%'})
                ]))
            ]
            table_body = [html.Tbody([
                html.Tr([
                    html.Td(html.A(article['title'], href=article['url'], target="_blank")),
                    html.Td(article.get('description', 'No summary available')),  # Add summary here
                    html.Td(article['source']['name']),
                    html.Td(article['publishedAt'])
                ]) for article in articles
            ])]
            news_table = dbc.Table(table_header + table_body, bordered=True, className='news-table')
            news_content.append(news_table)
        else:
            news_content.append(html.P(f"No news found for {symbol}."))
    
    return news_content

@app.callback(
    [Output('stock-graph', 'figure'),
      Output('stock-graph', 'style'),
      Output('stock-news', 'children'),
      Output('-comparison-graph', 'figure'),
      Output('individual-stocks-store', 'data'),
      Output('date-picker-range', 'start_date'),
      Output('date-picker-range', 'end_date')],
    [Input('add-stock-button', 'n_clicks'),
      Input('submit-button', 'n_clicks'),
      Input('reset-stocks-button', 'n_clicks'),
      Input('stock-input', 'value'),
      Input('predefined-ranges', 'value'),
      Input('movag_input', 'value'),
      Input('benchmark-selection', 'value'),
      Input('plotly-theme-store', 'data')],
    [State('individual-stock-input', 'value'),
      State('individual-stocks-store', 'data'),
      State('stock-input', 'value'),
      State('date-picker-range', 'start_date'),
      State('date-picker-range', 'end_date')]
)
def update_content(add_n_clicks, submit_n_clicks, reset_n_clicks, stock_input, predefined_range, movag_input, benchmark_selection, plotly_theme, new_stock, individual_stocks, selected_stocks, start_date, end_date):
    ctx = dash.callback_context
    if not ctx.triggered:
        selected_stocks = ['AAPL']
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'add-stock-button' and new_stock:
        new_stock = new_stock.upper().strip()
        if new_stock and new_stock not in individual_stocks:
            individual_stocks.append(new_stock)
    
    if trigger == 'reset-stocks-button':
        individual_stocks = []
    
    selected_stocks = list(set(selected_stocks + individual_stocks))
    
    if not selected_stocks:
        return (px.line(title="Please select at least one stock symbol.", template=plotly_theme),
                {'height': '400px'},
                html.Div("Please select at least one stock symbol."),
                px.line(title="Please select at least one stock symbol.", template=plotly_theme),
                individual_stocks,
                start_date,
                end_date)
    
    today = pd.to_datetime('today')
    if predefined_range == 'YTD':
        start_date = datetime(today.year, 1, 1)
    elif predefined_range == '12M':
        start_date = today - timedelta(days=365)
    elif predefined_range == '24M':
        start_date = today - timedelta(days=730)
    elif predefined_range == '5Y':
        start_date = today - timedelta(days=1825)
    elif predefined_range == '10Y':
        start_date = today - timedelta(days=1825*2)
    else:
        start_date = datetime.strptime(start_date.split('T')[0], '%Y-%m-%d')
        end_date = datetime.strptime(end_date.split('T')[0], '%Y-%m-%d')
    
    end_date = today
    
    data = []
    for symbol in selected_stocks:
        df = yf.download(symbol, start=start_date, end=end_date)
        if not df.empty:
            df.reset_index(inplace=True)
            df['Stock'] = symbol
            df['30D_MA'] = df.groupby('Stock')['Close'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
            df['100D_MA'] = df.groupby('Stock')['Close'].transform(lambda x: x.rolling(window=100, min_periods=1).mean())
            data.append(df)
    
    if not data:
        return (px.line(title="No data found for the given stock symbols and date range.", template=plotly_theme),
                {'height': '400px'},
                html.Div("No news found for the given stock symbols."),
                px.line(title="No data found for the given stock symbols and date range.", template=plotly_theme),
                individual_stocks,
                start_date,
                end_date)
    
    df_all = pd.concat(data)
    
    # Determine the number of rows needed for the graph
    num_stocks = len(selected_stocks)
    num_rows = num_stocks
    graph_height = 400 * num_rows  # Each facet should be 400px in height
    
    
    if '30D Moving Average' in movag_input and '100D Moving Average' in movag_input:
        fig_stock = px.line(df_all, x='Date', y=['Close', '30D_MA','100D_MA'], color='Stock', facet_col='Stock', facet_col_wrap=1, template=plotly_theme)
        fig_stock.update_yaxes(matches=None, title_text=None)
        fig_stock.update_xaxes(title_text=None)
        fig_stock.update_layout(showlegend=False, height=graph_height,margin=dict(l=10, r=10, t=15, b=10))
    
    elif '30D Moving Average' in movag_input:
        fig_stock = px.line(df_all, x='Date', y=['Close', '30D_MA'], color='Stock', facet_col='Stock', facet_col_wrap=1, template=plotly_theme)
        fig_stock.update_yaxes(matches=None, title_text=None)
        fig_stock.update_xaxes(title_text=None)
        fig_stock.update_layout(showlegend=False, height=graph_height,margin=dict(l=10, r=10, t=15, b=10))
    
    elif '100D Moving Average' in movag_input:
        fig_stock = px.line(df_all, x='Date', y=['Close', "100D_MA"], color='Stock', facet_col='Stock', facet_col_wrap=1, template=plotly_theme)
        fig_stock.update_yaxes(matches=None, title_text=None)
        fig_stock.update_xaxes(title_text=None)
        fig_stock.update_layout(showlegend=False, height=graph_height,margin=dict(l=10, r=10, t=15, b=10))
    
    else:
        fig_stock = px.line(df_all, x='Date', y='Close', color='Stock', facet_col='Stock', facet_col_wrap=1, template=plotly_theme)
        fig_stock.update_yaxes(matches=None, title_text=None)
        fig_stock.update_xaxes(title_text=None)
        fig_stock.update_layout(showlegend=False, height=graph_height,margin=dict(l=10, r=10, t=15, b=10))

    
    df_all['Date'] = pd.to_datetime(df_all['Date'])
    df_all.set_index('Date', inplace=True)
    
    # Create an index for each stock
    _data = {}
    for symbol in selected_stocks:
        df_stock = df_all[df_all['Stock'] == symbol].copy()
        df_stock['Index'] = df_stock['Close'] / df_stock['Close'].iloc[0] * 100
        indexed_data[symbol] = df_stock[['Index']]
    
    # Add benchmark data if selected
    if benchmark_selection != 'None':
        benchmark_data = yf.download(benchmark_selection, start=start_date, end=end_date)
        if not benchmark_data.empty:
            benchmark_data.reset_index(inplace=True)
            benchmark_data['Index'] = benchmark_data['Close'] / benchmark_data['Close'].iloc[0] * 100
            benchmark_data.set_index('Date', inplace=True)
            indexed_data[benchmark_selection] = benchmark_data[['Index']]
    
    # Combine all indexed data
    df_indexed = pd.concat(indexed_data, axis=1)
    df_indexed.reset_index(inplace=True)
    df_indexed.columns = ['Date'] + [f'{symbol}_Index' for symbol in indexed_data.keys()]
    
    fig_indexed = px.line(df_indexed, x='Date', y=[f'{symbol}_Index' for symbol in selected_stocks], template=plotly_theme)
    fig_indexed.update_yaxes(matches=None, title_text=None)
    fig_indexed.update_xaxes(title_text=None)
    fig_indexed.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ),legend_title_text=None,margin=dict(l=10, r=10, t=15, b=10))
  

    
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
    
    # Add benchmark line as dotted if selected
    if benchmark_selection != 'None':
        fig_indexed.add_scatter(x=df_indexed['Date'], y=df_indexed[f'{benchmark_selection}_Index'], mode='lines', name=benchmark_selection, line=dict(dash='dot'))
    
    fig_indexed.update_layout(template=plotly_theme)

    load_dotenv()
    api_key = os.getenv('API_KEY')
    
    news_content = fetch_news(api_key, selected_stocks)
    
    return fig_stock, {'height': f'{graph_height}px', 'overflow': 'auto'}, news_content, fig_indexed, individual_stocks, start_date, end_date

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
                margin=dict(t=100,l=10,r=10,b=10)  # Add extra margin on top
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

@app.callback(Output('page-content', 'children'),   
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/about':
        return about_layout
    else:
        return dashboard_layout

@app.callback(
    [Output('theme-store', 'data'),
      Output('plotly-theme-store', 'data')],
    [Input(f'theme-{theme}', 'n_clicks') for theme in themes.keys()]
)
def update_theme(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dbc.themes.YETI, 'plotly_white'
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    theme = button_id.split('-')[1]
    return themes[theme]['dbc'], themes[theme]['plotly']

@app.callback(
    Output('theme-switch', 'href'),
    Input('theme-store', 'data')
)
def update_stylesheet(theme):
    return theme

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Josua's Stock Dashboard</title>
        {%favicon%}
        {%css%}
        <link id="theme-switch" rel="stylesheet" href="{{ external_stylesheets[0] }}">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)







