import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(__name__,    title="Stock News - WatchMyStocks Dashboard",
    description="Stay updated with the latest news on your selected stocks. Filter by watchlist to see tailored news for better investment insights.")

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            # html.P("Filter your Stocks from selection here"),
            # html.P([
            #     "Filter Stocks from ",
            #     html.Span(
            #         "Watchlist", className="bg-primary text-white rounded px-2")
            # ], className="fs-5"),
            dcc.Dropdown(
                id='news-stock-dropdown',
                options=[],
                value=[],
                multi=True,
                placeholder="Select stocks to display",
                searchable=False,
                className="text-dark"
            ),
            dcc.Loading(id="loading-news", type="default", children=[
                html.Div(id='stock-news',
                         className='news-container')
            ])
        ])
    ),
    html.Div(id='forecast-output'),

])


