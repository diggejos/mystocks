
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import dash

dash.register_page(
    __name__,
    title="Stock News - WatchMyStocks Dashboard",
    description="Stay updated with the latest news on your selected stocks. Filter by watchlist to see tailored news for better investment insights."
)

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.P([
                "Access the latest updates with our curated ",
                html.Span("stock news dashboard", className="fw-bold text-primary"),
                ". Stay informed with news tailored to your selected stocks and watchlists."
            ], className="fs-5 mb-3"),

            html.Div([
                html.P("Filter news by selecting stocks or watchlists:", className="mb-2"),
                dcc.Dropdown(
                    id='news-stock-dropdown',
                    options=[],  # Populated dynamically
                    value=[],
                    multi=True,
                    searchable=False,
                    placeholder="Select stocks to display news",
                    className="text-dark",
                    style={"margin-bottom": "15px"}
                ),
            ], style={"margin-bottom": "20px"}),

            dcc.Loading(
                id="loading-news",
                type="default",
                children=[
                    html.Div(
                        id='stock-news',
                        className='news-container',
                        style={"margin-top": "20px"}
                    )
                ]
            ),
        ])
    ),

    html.Div([
        html.P([
            "With WatchMyStocks, gain valuable insights through real-time ",
            html.Span("news updates", className="fw-bold"),
            " tailored to your portfolio and stay ahead in your investment journey."
        ], className="mt-4")
    ], id='news-output')

], style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
