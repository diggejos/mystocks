import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(
    __name__,
    title="Stock Prices - WatchMyStocks Dashboard",
    path='/prices',
    description="Explore today's stock prices with WatchMyStocks. Access real-time stock updates, historical data, and customizable price charts."
)

layout = html.Div([
    dcc.Store(id='prices-fig-store', storage_type='session'),

    dbc.Card(
        dbc.CardBody([
            html.P([
                "Monitor your favorite stocks and explore ",
                html.Span("real-time stock prices", className="fw-bold text-primary"),
                " to stay updated on today's market trends."
            ], className="fs-5 mb-3"),
            
            dcc.Dropdown(
                id='prices-stock-dropdown',
                options=[],
                value=[],
                multi=True,
                placeholder="Select stocks to display",
                searchable=False,
                className="text-dark",
                style={"margin-bottom": "15px"}
            ),
            
            html.Div([
                html.P("Choose your preferred chart type for real-time and historical stock data:", className="mb-2"),
                dcc.RadioItems(
                    id='chart-type',
                    options=[
                        {'label': 'Line Chart', 'value': 'line'},
                        {'label': 'Candlestick Chart', 'value': 'candlestick'}
                    ],
                    value='line',
                    inline=True,
                    inputStyle={"margin-right": "10px"},
                    labelStyle={"margin-right": "20px"}
                ),
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.P("Add optional overlays to analyze stock data more effectively:", className="mb-2"),
                dcc.Checklist(
                    id='movag_input',
                    options=[
                        {'label': '30-Day Moving Average (Trend Analysis)', 'value': '30D_MA'},
                        {'label': '100-Day Moving Average (Long-Term Trends)', 'value': '100D_MA'},
                        {'label': 'Volume (Trading Activity)', 'value': 'Volume'}
                    ],
                    value=[],
                    inline=True,
                    inputStyle={"margin-right": "10px"},
                    labelStyle={"margin-right": "20px"}
                ),
            ], style={"margin-bottom": "20px"}),
            
            html.Div(id='load-warning', style={'color': 'red', 'margin': '10px 0'}),

            dcc.Loading(
                id="loading-prices",
                type="default",
                children=[
                    dcc.Graph(
                        id='stock-graph',
                        style={'backgroundColor': 'transparent'},
                        config={'displayModeBar': False}
                    )
                ]
            )
        ])
    ),

    html.Div([
        html.P([
            "Leverage WatchMyStocks to customize your experience with interactive ",
            html.Span("price charts", className="fw-bold"),
            " and tools designed to help you make informed decisions."
        ], className="mt-4")
    ], id='prices-output')

], style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
