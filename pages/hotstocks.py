import dash_bootstrap_components as dbc
import pandas as pd
import utils as ut
from dash import html, dcc, callback, Input, Output
import dash


dash.register_page(__name__,    title="Hot Stocks - WatchMyStocks Dashboard",
    description="Discover today's top-performing stocks tailored to your risk tolerance! Get insights on high-profit potential picks backed by key financial KPIs and momentum metrics, ensuring you stay ahead in the market with data-driven recommendations.")


layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.H3("The hottest stocks to invest in at the moment based on financial KPIs", style={
                "display": "none"}),  # for SEO
            # for SEO
            html.P("Find the hottest stocks at the moment to consider investing in based on financial KPIs. This list is updated once a week. Currently the model looks at all SP500 companies and ranks them accordingly."),
            dcc.Dropdown(
                id='risk-tolerance-dropdown',
                options=[
                    {'label': 'Low Risk', 'value': 'low'},
                    {'label': 'Medium Risk',
                     'value': 'medium'},
                    {'label': 'High Risk',
                     'value': 'high'},
                ],
                value='low',  # Default to medium risk
                placeholder="Select Risk Tolerance",
                clearable=False,
                searchable=False,
                className="text-dark"
            ),
            dcc.Loading(
                id="loading-top-stocks",
                # Placeholder for the stocks table
                children=[
                    html.Div(id='top-stocks-table')],
                type="default"
            ),

            # This Div will dynamically show the appropriate paywall (logged-out, free, or none)
            html.Div(id='topshots-blur-overlay', style={
                'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
                                        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                        'backdrop-filter': 'blur(5px)'
            })
        ])
    ),


    html.Div(id='hotstocks-output'),

])
