import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash



dash.register_page(
    __name__,
    title="Analyst Recommendations - WatchMyStocks",
    description="Discover expert analyst recommendations tailored to your watchlist. Make informed investment decisions based on professional insights."
)

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.P([
                "Leverage ",
                html.Span("expert analyst recommendations", className="fw-bold text-primary"),
                " tailored to your watchlist. Gain professional insights to make smarter investment decisions."
            ], className="fs-5 mb-3"),

            dcc.Loading(
                id="loading-analyst-recommendations",
                type="default",
                children=[
                    html.Div(
                        id='analyst-recommendations-content',
                        style={"margin-top": "20px"}
                    )
                ]
            ),

            html.Div(
                id='recommendation-blur-overlay',
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
            )
        ])
    ),

    html.Div([
        html.P([
            "Use WatchMyStocks to explore ",
            html.Span("dedicated analyst recommendations", className="fw-bold"),
            " for your selected stocks and stay ahead in the market with professional guidance."
        ], className="mt-4")
    ], id='recommendations-output')

], style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
