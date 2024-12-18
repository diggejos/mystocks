import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash



dash.register_page(
    __name__,
    title="Stock Comparison - WatchMyStocks",
    description="Compare stocks against market indices and competitors. Discover opportunities using WatchMyStocks' smart comparison tools."
)

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.P([
                "Leverage WatchMyStocks to ",
                html.Span("compare stock performance", className="fw-bold text-primary"),
                " against major indices like S&P 500 and NASDAQ 100 or benchmark them against competitors."
            ], className="fs-5 mb-3"),

            html.Div([
                html.P("Select stocks to include in your comparison:", className="mb-2"),
                dcc.Dropdown(
                    id='indexed-comparison-stock-dropdown',
                    options=[],  # Populated dynamically
                    value=[],
                    multi=True,
                    searchable=False,
                    placeholder="Select stocks for comparison",
                    className="text-dark",
                    style={"margin-bottom": "15px"}
                ),
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.P("Choose a benchmark index to compare your selected stocks against:", className="mb-2"),
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
                    inputStyle={"margin-right": "10px"},
                    labelStyle={"margin-right": "20px"}
                ),
            ], style={"margin-bottom": "20px"}),

            dcc.Loading(
                id="loading-comparison",
                type="default",
                children=[
                    dcc.Graph(
                        id='indexed-comparison-graph',
                        style={'backgroundColor': 'transparent'},
                        config={'displayModeBar': False}
                    )
                ]
            )
        ])
    ),

    html.Div([
        html.P([
            "With WatchMyStocks' powerful comparison tools, you can gain unique insights by visualizing stock performance trends ",
            html.Span("against market benchmarks", className="fw-bold"),
            " or other stocks in your portfolio."
        ], className="mt-4")
    ], id='comparison-output')

], style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
