import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(__name__, title="Analyst Recommendations - WatchMyStocks",
    description="Get dedicated analyst recommendations based on your watchlist selection")

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            # html.P([
            #     "Find your Stocks from ",
            #     html.Span(
            #         "Watchlist", className="bg-primary text-white rounded px-2")
            # ], className="fs-5"),
            html.H3("Get analyst stock recommendations", style={
                "display": "none"}),  # for SEO
            dcc.Loading(
                id="loading-analyst-recommendations",
                type="default",
                children=[
                    html.Div(id='analyst-recommendations-content', className='mt-4')]
            ),
            html.Div(id='recommendation-blur-overlay', style={
                'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
                'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                    'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                    'backdrop-filter': 'blur(5px)'
            })

        ])
    ),

    html.Div(id='recommendations-output'),

])
