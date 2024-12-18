
import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(
    __name__,
    title="Hot Stocks - WatchMyStocks",
    description="Discover today's top-performing stocks tailored to your risk tolerance! Get insights on high-profit potential picks backed by key financial KPIs and momentum metrics, ensuring you stay ahead in the market with data-driven recommendations."
)

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.P([
                "Discover the ",
                html.Span("hottest stocks", className="fw-bold text-primary"),
                " to invest in today! Tailored to your risk tolerance, this list is updated weekly, providing insights into high-profit potential picks using advanced financial KPIs and momentum metrics."
            ], className="fs-5 mb-3"),
            
            html.Div([
                html.P("Select your preferred risk tolerance to filter stock recommendations:", className="mb-2"),
                dcc.Dropdown(
                    id='risk-tolerance-dropdown',
                    options=[
                        {'label': 'Low Risk', 'value': 'low'},
                        {'label': 'Medium Risk', 'value': 'medium'},
                        {'label': 'High Risk', 'value': 'high'},
                    ],
                    value='low',  # Default to low risk
                    placeholder="Select Risk Tolerance",
                    clearable=False,
                    searchable=False,
                    className="text-dark",
                    style={"margin-bottom": "15px"}
                ),
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.P("Explore the top-performing stocks tailored to your selection:", className="mb-2"),
                dcc.Loading(
                    id="loading-top-stocks",
                    type="default",
                    children=[
                        html.Div(
                            id='top-stocks-table',
                            style={"margin-top": "20px"}
                        )
                    ]
                ),
            ], style={"margin-bottom": "20px"}),

            html.Div(
                id='topshots-blur-overlay',
                style={
                    'position': 'absolute',
                    'top': 0,
                    'left': 0,
                    'width': '100%',
                    'height': '100%',
                    'background-color': 'rgba(255, 255, 255, 0.8)',
                    'display': 'none',
                    'justify-content': 'center',
                    'align-items': 'center',
                    'z-index': 1000,
                    'backdrop-filter': 'blur(5px)'
                }
            ),
        ])
    ),

    html.Div([
        html.P([
            "Empower your investment strategy with WatchMyStocks’ tailored recommendations for ",
            html.Span("high-performing stocks", className="fw-bold"),
            " backed by comprehensive data analysis."
        ], className="mt-4")
    ], id='hotstocks-output')

], style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
