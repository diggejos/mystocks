import dash_bootstrap_components as dbc
from dash import html, dcc, dash
import dash

# Register the page with relevant metadata for SEO
dash.register_page(
    __name__,
    title="Stocks Forecast - WatchMyStocks Dashboard",
    description="Get forecasted stock prices using advanced time series models. Perfect for financial planning and insights.",
    keywords="stock forecasting, best stock forecast, time series models, stock prices"
)

# Define the layout with meta tags and structured data for SEO
layout = html.Div([
    # Meta tags for improved SEO
    html.Meta(name="viewport", content="width=device-width, initial-scale=1"),
    html.Meta(name="robots", content="index, follow"),
    html.Meta(name="author", content="WatchMyStocks"),

    
    # Structured data (JSON-LD)
    html.Script(type="application/ld+json", children='''
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "Forecast - WatchMyStocks",
            "description": "Get forecasted stock prices using advanced time series models. Perfect for financial planning and insights.",
            "url": "https://mystocksportfolio.io/forecast",
            "publisher": {
                "@type": "Organization",
                "name": "WatchMyStocks"
            }
        }
    '''),

    # Main content
    dcc.Store(id='forecast-data-store', storage_type='session'),  # Store for persisting forecast data
    dcc.Store(id='forecast-attempt-store', data=0, storage_type='session'),  # Store for attempt count tracking

    # Container for forecast content and overlay
    html.Div(
        [
            # Main forecast content card
            dbc.Card(
                dbc.CardBody([
                    html.H1("Forecast stock prices"),  # <h1> for SEO

                    # Forecast input controls
                    html.Div([
                        html.Label("Select up to 3 Stocks:", className="font-weight-bold"),
                        dcc.Dropdown(
                            id='forecast-stock-input',
                            options=[], value=[], multi=True,
                            className='form-control text-dark', searchable=False
                        ),
                        html.Div(id='forecast-stock-warning', style={'color': 'red'}),
                        html.Label("Forecast Horizon (days):", className="font-weight-bold"),
                        dcc.Slider(
                            id='forecast-horizon-input',
                            min=30, max=365*2, step=30,  # Range from 1 month to 2 years
                            value=90,  # Default value
                            marks={i: str(i) for i in range(0, 731, 90)},  # Marks every 3 months
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        dbc.Button("Generate Forecasts", id='generate-forecast-button', color='primary', className='mt-2')
                    ], className='mb-3'),

                    # Disclaimer for SEO and user clarity
                    dcc.Markdown('''
                        **Disclaimer:** This forecast is generated using time series forecasting methods.
                        Use cautiously and as one of several sources in decision-making.
                    ''', style={'font-size': '14px', 'color': 'gray'}),

                    # Loading components for forecast output
                    dcc.Loading(html.Div(id='forecast-kpi-output', className='mb-3')),
                    dcc.Loading(id="loading-forecast", type="default", children=[
                        dcc.Graph(id='forecast-graph', config={'displayModeBar': False})
                    ]),
                ])
            ),

            # Paywall overlay for forecast content
            html.Div(
                id='forecast-blur-overlay',
                style={
                    'position': 'absolute',
                    'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
                    'background-color': 'rgba(255, 255, 255, 0.8)',
                    'display': 'none',
                    'justify-content': 'center', 'align-items': 'center', 'z-index': 10,
                    'backdrop-filter': 'blur(5px)'
                }
            )
        ],
        style={
            'position': 'relative',
            'overflow': 'hidden'
        }
    )
])
