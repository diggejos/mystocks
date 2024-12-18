import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash



dash.register_page(
    __name__,
    title="Investment Simulation - WatchMyStocks Dashboard",
    description="Simulate stock investment outcomes over historical periods. Enter stock symbols, investment amount, and dates to see potential profits and losses."
)

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.P([
                "Explore how your investments could have performed with our ",
                html.Span("investment simulation tool", className="fw-bold text-primary"),
                ". Input stock symbols, investment amounts, and dates to visualize historical performance and potential outcomes."
            ], className="fs-5 mb-3"),

            html.Div([
                html.P("Enter the stock symbol you'd like to simulate:", className="mb-2"),
                dcc.Dropdown(
                    id='simulation-stock-input',
                    options=[],  # Dynamically populated
                    value=[],
                    multi=False,
                    placeholder="Select or type a stock symbol",
                    className="text-dark",
                    searchable=True,
                    style={"margin-bottom": "15px"}
                ),
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.P("Specify the amount you'd like to invest (in USD):", className="mb-2"),
                dcc.Slider(
                    id='investment-amount',
                    min=1000,
                    max=100000,
                    step=1000,
                    value=5000,
                    marks={i: f'${i // 1000}k' for i in range(000, 100010, 15000)},
                    tooltip={"placement": "bottom", "always_visible": False},
                    className="mb-4"
                ),
            ], style={"margin-bottom": "20px"}),

            html.Div([
                html.P("Choose your investment start date:", className="mb-2"),
                dcc.DatePickerSingle(
                    id='investment-date',
                    date=pd.to_datetime('2024-01-01'),
                    display_format='YYYY-MM-DD',
                    className='form-control text-dark',
                    style={"margin-bottom": "15px"}
                ),
            ], style={"margin-bottom": "20px"}),

            dbc.Button(
                "Simulate Investment",
                id='simulate-button',
                color='primary',
                className='btn btn-lg mt-2'
            ),

            dcc.Loading(
                id="loading-simulation",
                type="default",
                children=[
                    html.Div(
                        id='simulation-result',
                        className='mt-4',
                        style={"font-size": "16px", "line-height": "1.5"}
                    )
                ]
            ),
        ])
    ),

    html.Div([
        html.P([
            "With WatchMyStocks' simulation tools, make smarter investment decisions by understanding ",
            html.Span("historical stock trends", className="fw-bold"),
            " and visualizing potential profits and losses."
        ], className="mt-4")
    ], id='simulation-output')

], style={'width': '100%', 'display': 'flex', 'flex-direction': 'column'})
