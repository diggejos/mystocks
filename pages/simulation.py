import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(__name__, title="Investment Simulation - WatchMyStocks",
    description="Simulate stock investment outcomes over historical periods. Enter stock symbols, investment amount, and dates to see potential profits and losses.")

layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            # html.P([
            #     "Filter Stocks from ",
            #     html.Span(
            #         "Watchlist", className="bg-primary text-white rounded px-2")
            # ], className="fs-5"),
            html.H3("Simulate stock profits and losses over historical time period", style={
                "display": "none"}),  # for SEO
            html.Label("Stock Symbol:",
                       className="font-weight-bold"),
            dcc.Dropdown(
                id='simulation-stock-input',
                options=[],
                value=[],
                className='form-control text-dark',
                searchable=False,
                multi=False
            ),
            html.Label("Investment Amount ($):",
                       className="font-weight-bold"),
            
            dcc.Slider(
                id='investment-amount',
                min=1000, max=100000, step=1000,  # Range from 1 day to 2 years (730 days)
                value=5000,  # Default value
                marks={i: f'${i//1000}k' for i in range(0, 100001, 10000)},  # Marks every 5,000 formatted as "$5k", "$10k", etc.
                tooltip={"placement": "bottom", "always_visible": False}
            ),
                            
            # dcc.Input(
            #     id='investment-amount',
            #     type='number',
            #     value=1000,
            #     className='form-control',
            # ),
            html.Label("Investment Date:",
                       className="font-weight-bold"),
            dcc.DatePickerSingle(
                id='investment-date',
                date=pd.to_datetime('2024-01-01'),
                className='form-control'
            ),
            dbc.Button(
                "Simulate Investment", id='simulate-button', color='primary', className='mt-2'),
            dcc.Loading(id="loading-simulation", type="default", children=[
                html.Div(id='simulation-result',
                         className='mt-4')
            ])
        ])
    ),
    html.Div(id='simulation-output'),

])
