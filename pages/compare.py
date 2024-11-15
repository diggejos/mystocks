import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(__name__,title="Stock Comparison - WatchMyStocks",
    description="Compare selected stocks with major benchmarks like S&P 500 and NASDAQ 100. Use our tools to analyze performance trends across stocks and indices.")

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            # html.P([
            #     "Filter Stocks from ",
            #     html.Span(
            #         "Watchlist", className="bg-primary text-white rounded px-2")
            # ], className="fs-5"),
            html.Label(
                "Select Stocks for Comparison:", className="font-weight-bold"),
            dcc.Dropdown(
                id='indexed-comparison-stock-dropdown',
                options=[],  # Populated dynamically
                value=[],
                multi=True,
                searchable=False,
                className="text-dark"
            ),
            dcc.RadioItems(
                id='benchmark-selection',
                options=[
                    {'label': 'None', 'value': 'None'},
                    {'label': 'S&P 500', 'value': '^GSPC'},
                    {'label': 'NASDAQ 100',
                     'value': '^NDX'},
                    {'label': 'SMI', 'value': '^SSMI'}
                ],
                value='None',
                inline=True,
                inputStyle={"margin-right": "10px"},
                labelStyle={"margin-right": "20px"}
            ),
            dcc.Loading(id="loading-comparison", type="default", children=[
                dcc.Graph(
                    id='indexed-comparison-graph', style={'height': '500px'}, config={'displayModeBar': False})
            ])
        ])
    ),
    html.Div(id='comparison-output'),

])

#
