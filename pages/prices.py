import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(
    __name__,
    title="Stock Prices - WatchMyStocks Dashboard",
    path='/prices',
    description="Explore real-time and historical stock prices dashboard with various charting options. Choose line or candlestick charts and add moving averages for better insights.",
    keywords="stock prices, real-time stocks, historical stock prices, stock charting, moving average, candlestick charts, dashboard, aapl, msft"
)

layout = html.Div([

    # Invisible SEO Headers
    html.H1("Real-Time and Historical Stock Prices Dashboard", className="invisible-header"),
    html.H2("Explore Stock Charting Options with Moving Averages", className="invisible-header"),
    html.H3("Line and Candlestick Charts for Better Insights", className="invisible-header"),
    
    
    dcc.Store(id='prices-fig-store', storage_type='session'),
    # dcc.Store(id='individual-stocks-store', storage_type='session'),


    dbc.Card(
        dbc.CardBody([
            # html.P([
            #     "Filter Stocks from ",
            #     html.Span("Watchlist", className="bg-primary text-white rounded px-2")
            # ], className="fs-5"),
            dcc.Dropdown(
                id='prices-stock-dropdown',
                options=[],
                value=[],
                multi=True,
                placeholder="Select stocks to display",
                searchable=False,
                className="text-dark"
            ),
            dcc.RadioItems(
                id='chart-type',
                options=[
                    {'label': 'Line Chart',
                     'value': 'line'},
                    {'label': 'Candlestick Chart',
                     'value': 'candlestick'}
                ],
                value='line',
                inline=True,
                inputStyle={"margin-right": "10px"},
                labelStyle={"margin-right": "20px"}
            ),
            dcc.Checklist(
                id='movag_input',
                options=[
                    {'label': '30D Moving Average',
                     'value': '30D_MA'},
                    {'label': '100D Moving Average',
                     'value': '100D_MA'},
                    {'label': 'Volume', 'value': 'Volume'}
                ],
                value=[],
                inline=True,
                inputStyle={"margin-right": "10px"},
                labelStyle={"margin-right": "20px"}
            ),
            
            html.Div(id='load-warning', style={'color': 'red', 'margin': '10px 0'}),

            # dcc.Graph(id='stock-graph', style={'height': '500px', 'backgroundColor': 'transparent'})
            dcc.Loading(id="loading-prices", type="default", children=[
                dcc.Graph(id='stock-graph', style={'backgroundColor': 'transparent'}, config={'displayModeBar': False})
            ])
        ])
    ),


    html.Div(id='prices-output')

],style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
