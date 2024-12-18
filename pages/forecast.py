import dash_bootstrap_components as dbc
from dash import html, dcc, dash
import dash

dash.register_page(
    __name__,
    title="Stocks Forecast - WatchMyStocks Dashboard",
    description="Predict the future of stocks with advanced forecasting tools. Get insights into Microsoft, Apple, and other stocks for up to 2 years."
)


layout = html.Div([
    # Store for persisting forecast data
    dcc.Store(id='forecast-data-store', storage_type='session'),
    # Store for attempt count tracking
    dcc.Store(id='forecast-attempt-store', data=0, storage_type='session'),

    # Container for forecast content and overlay
    html.Div(
        [
            # Main forecast content card
            dbc.Card(
                dbc.CardBody([
                    html.P([
                        "utilize advanced forecasting tools on WatchMyStocks to predict stock price movements for up to ",
                        html.Span(
                            "two years", className="fw-bold text-primary"),
                        ". Gain insights into stocks like Microsoft, Apple, and other market leaders."
                    ], className="fs-5 mb-3"),
                    html.H1("Forecast stock prices", style={
                            "display": "none"}),  # for SEO
                    html.Div([
                        html.Label("Select up to 3 Stocks from Watchlist:",
                                   className="font-weight-bold"),
                        dcc.Dropdown(
                            id='forecast-stock-input',
                            options=[], value=[], multi=True,
                            className='form-control text-dark', searchable=False
                        ),
                        html.Div(id='forecast-stock-warning',
                                 style={'color': 'red'}),
                        html.P(
                            "Adjust the forecast horizon to analyze short or long-term trends:", className="mb-2"),

                        dcc.Slider(
                            id='forecast-horizon-input',
                            # Range from 1 day to 2 years (730 days)
                            min=30, max=365*2, step=30,
                            value=90,  # Default value
                            # Marks at every 30 days
                            marks={i: str(i) for i in range(0, 731, 90)},
                            tooltip={"placement": "bottom",
                                     "always_visible": True}
                        ),

                        # dcc.Input(
                        #     id='forecast-horizon-input', type='number', value=90,
                        #     className='form-control', min=1, max=365*2
                        # ),
                        dbc.Button(
                            "Generate Forecasts", id='generate-forecast-button', color='primary', className='mt-2')
                    ], className='mb-3'),
                    dcc.Markdown('''
                        **Disclaimer:** This forecast is generated using time series forecasting methods.
                        Use cautiously and as one of several sources in decision-making.
                    ''', style={'font-size': '14px', 'color': 'gray'}),
                    dcc.Loading(
                        html.Div(id='forecast-kpi-output', className='mb-3')),
                    dcc.Loading(id="loading-forecast", type="default", children=[
                        dcc.Graph(id='forecast-graph',
                                  config={'displayModeBar': False})
                    ]),
                ])
            ),

            html.Div([
                html.P([
                    "Take advantage of WatchMyStocks' forecasting tools to analyze historical trends and predict future movements. Use this feature to enhance your investment strategy and stay ahead in the market."
                ], className="mt-4")
            ], id='forecast-output'),

            # Paywall overlay specific to forecast content
            html.Div(
                id='forecast-blur-overlay',
                style={
                    'position': 'absolute',  # Positioned within the container
                    'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
                    'background-color': 'rgba(255, 255, 255, 0.8)',
                    'display': 'none',  # Hidden initially
                    'justify-content': 'center', 'align-items': 'center', 'z-index': 10,
                    'backdrop-filter': 'blur(5px)'  # Stronger blur effect
                }
            )
        ],
        style={
            'position': 'relative',  # Restrict overlay to this container
            'overflow': 'hidden'  # Ensure overlay is confined to forecast content area
        }
    )
])

