import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
from plotly.subplots import make_subplots
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import json
from flask_migrate import Migrate
import psycopg2
from prophet import Prophet
import re
from dash.dependencies import Input, Output, State, ALL



# List of available Bootstrap themes and corresponding Plotly themes
themes = {
    'YETI': {'dbc': dbc.themes.YETI, 'plotly': 'simple_white'},
    'CERULEAN': {'dbc': dbc.themes.CERULEAN, 'plotly': 'simple_white'},
    'COSMO': {'dbc': dbc.themes.COSMO, 'plotly': 'simple_white'},
    'CYBORG': {'dbc': dbc.themes.CYBORG, 'plotly': 'plotly_dark'},
    'JOURNAL': {'dbc': dbc.themes.JOURNAL, 'plotly': 'simple_white'},
    'LUMEN': {'dbc': dbc.themes.LUMEN, 'plotly': 'simple_white'},
    'MATERIA': {'dbc': dbc.themes.MATERIA, 'plotly': 'simple_white'},
    'MINTY': {'dbc': dbc.themes.MINTY, 'plotly': 'simple_white'},
    'SIMPLEX': {'dbc': dbc.themes.SIMPLEX, 'plotly': 'simple_white'},
    'SKETCHY': {'dbc': dbc.themes.SKETCHY, 'plotly': 'simple_white'},
    'SPACELAB': {'dbc': dbc.themes.SPACELAB, 'plotly': 'simple_white'},
    'VAPOR': {'dbc': dbc.themes.VAPOR, 'plotly': 'plotly_dark'}
}


# Initialize the Dash app with a default Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
server = app.server

server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(server)
# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(server)


# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    watchlist = db.Column(db.Text, nullable=True, default="[]")
    theme = db.Column(db.String(500), nullable=True, default="MATERIA")  # New theme field

    def __init__(self, username, email, password, watchlist="[]", theme="MATERIA"):
        self.username = username
        self.email = email
        self.password = password
        self.watchlist = watchlist
        self.theme = theme
     
# Create the database tables
with server.app_context():
    db.create_all()

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("📈 Dashboard", href="/", active="exact")),
        dbc.NavItem(dbc.NavLink("ℹ️ About", href="/about", active="exact")),
        dbc.NavItem(dbc.NavLink("📝 Register", href="/register", active="exact", id='register-link')),
        dbc.NavItem(dbc.NavLink("🔐 Login", href="/login", active="exact", id='login-link', style={"display": "block"})),
        dbc.NavItem(dbc.Button("↪ Logout", id='logout-button', color='secondary', style={"display": "none"})),
        html.Div([
            dbc.DropdownMenu(
                children=[dbc.DropdownMenuItem(theme, id=f'theme-{theme}') for theme in themes],
                nav=True,
                in_navbar=True,
                label="🎨Select Theme",
                id='theme-dropdown',
            )
        ], id='theme-dropdown-wrapper', n_clicks=0),
    ],
    brand=[
        html.Img(src='/assets/logo_with_transparent_background.png', height='60px'),
        "MySTOCKS"
    ],
    brand_href="/",
    color="primary",
    dark=True,
    className="sticky-top mb-4"
)

overlay = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Access Restricted")),
        dbc.ModalBody("Please register or log in to use this feature."),
        dbc.ModalFooter(
            dbc.Button("Please register or login", href="/login", color="primary", id="overlay-registerP-button")
        ),
    ],
    id="login-overlay",
    is_open=False,  # Initially closed
)

app.layout = html.Div([
    dcc.Store(id='individual-stocks-store', data=[]),
    dcc.Store(id='theme-store', data=dbc.themes.MATERIA),
    dcc.Store(id='plotly-theme-store', data='plotly_white'),
    dcc.Store(id='login-status', data=False),  # Store to track login status
    dcc.Store(id='login-username-store', data=None),  # Store to persist the username
    html.Link(id='theme-switch', rel='stylesheet', href=dbc.themes.BOOTSTRAP),
    navbar,
    overlay,  # Add the overlay to the layout
    dcc.Location(id='url', refresh=False),
    dbc.Container(id='page-content', fluid=True),
    dcc.Store(id='active-tab', data='📈 Prices'), 
    dcc.Store(id='forecast-data-store'),
])

dashboard_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Button("🔽", id="toggle-filters-button", color="primary", outline=True, size="sm", style={"position": "flexible", "top": "15px", "left": "10px"})
            ]),
            dbc.Collapse(
                dbc.Card([  
                    dbc.CardBody([
                        html.Div([
                            html.Label("Add Stock Symbol:", className="font-weight-bold"),
                            dcc.Input(
                                id='individual-stock-input',
                                type='text',
                                placeholder='e.g. AAPL',
                                debounce=True,
                                className='form-control'
                            ),
                            dbc.Button("➕ Stock", id='add-stock-button', color='secondary', className='mt-2 me-2'),
                            dbc.Button("Reset all", id='reset-stocks-button', color='danger', className='mt-2 me-2'),
                            html.Span("🔄", id='refresh-data-icon', style={'cursor': 'pointer', 'font-size': '24px'}, className='mt-2 me-2'),  # Refresh icon
                            dbc.Button("💾 Watchlist", id='save-portfolio-button', color='primary', className='',
                                        disabled=False, style={'margin-top': '10px', 'margin-bottom': '10px', 'width': 'flexible'}),

                        ], className='mb-3'),
                        
                        html.Div([
                            html.Label("Select Date Range:", className="font-weight-bold"),
                            dcc.RadioItems(
                                id='predefined-ranges',
                                options=[
                                    {'label': 'Year to Date', 'value': 'YTD'},
                                    {'label': 'last Month', 'value': '1M'},
                                    {'label': 'last 3 Months', 'value': '3M'},
                                    {'label': 'Last 12 Months', 'value': '12M'},
                                    {'label': 'Last 24 Months', 'value': '24M'},
                                    {'label': 'Last 5 Years', 'value': '5Y'},
                                    {'label': 'Last 10 Years', 'value': '10Y'}
                                ],
                                value='12M',
                                inline=True,
                                className='form-control',
                                inputStyle={"margin-right": "10px"},
                                labelStyle={"margin-right": "20px"}
                            )
                        ], className='mb-3'),
                        
                        html.Div(id='watchlist-summary', className='mb-3')
                    ])
                ]), 
                id="filters-collapse", 
                is_open=True,  # Start with the card open
              style={"margin-top": "20px"}), 
        ], width=12, md=3, style={"margin-top": "-25px"} ),
        dbc.Col([
            dcc.Tabs(id='tabs', value='📈 Prices', children=[
                dcc.Tab(label='📈 Prices', value='📈 Prices', children=[
                    dbc.Card(
                        dbc.CardBody([
                            dcc.RadioItems(
                                id='chart-type',
                                options=[
                                    {'label': 'Line Chart', 'value': 'line'},
                                    {'label': 'Candlestick Chart', 'value': 'candlestick'}
                                ],
                                value='line',
                                inline=True,
                                className='form-control',
                                inputStyle={"margin-right": "10px"},
                                labelStyle={"margin-right": "20px"}
                            ),
                            dcc.Checklist(
                                id='movag_input',
                                options=[
                                    {'label': '30D Moving Average', 'value': '30D_MA'},
                                    {'label': '100D Moving Average', 'value': '100D_MA'},
                                    {'label': 'Volume', 'value': 'Volume'}
                                ],
                                value=[],
                                inline=True,
                                inputStyle={"margin-right": "10px"},
                                labelStyle={"margin-right": "20px"}
                            ),
                            dcc.Graph(id='stock-graph')
                        ])
                    )
                ]),
                dcc.Tab(label='📰 News', value='📰 News', children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(id='stock-news', className='news-container')
                        ])
                    )
                ]),
                dcc.Tab(label='⚖️ Indexed Comparison', value='⚖️ Indexed Comparison', children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.Label("Select Stocks for Comparison:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id='indexed-comparison-stock-dropdown',
                                    options=[],  # This will be populated dynamically
                                    value=[],  # Default selected stocks
                                    multi=True,
                                    className='form-control',
                                    maxHeight=200,
                                ),
                            ], className='mb-3'),
                            dcc.RadioItems(
                                id='benchmark-selection',
                                options=[
                                    {'label': 'None', 'value': 'None'},
                                    {'label': 'S&P 500', 'value': '^GSPC'},
                                    {'label': 'NASDAQ 100', 'value': '^NDX'},
                                    {'label': 'SMI', 'value': '^SSMI'}
                                ],
                                value='None',
                                inline=True,
                                className='form-control',
                                inputStyle={"margin-right": "10px"},
                                labelStyle={"margin-right": "20px"}
                            ),
                            dcc.Graph(id='indexed-comparison-graph')
                        ])
                    )
                ]),

                dcc.Tab(label='🌡️ Forecast', value='🌡️ Forecast', children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.Label("Select up to 3 Stocks:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id='forecast-stock-input',
                                    options=[],  # Options will be populated dynamically
                                    value=[],  # Default selected stocks
                                    multi=True,
                                    className='form-control',
                                ),
                                html.Div(id='forecast-stock-warning', style={'color': 'red'}),
                                html.Label("Forecast Horizon (days):", className="font-weight-bold"),
                                dcc.Input(
                                    id='forecast-horizon-input',
                                    type='number',
                                    value=90,
                                    className='form-control',
                                    min=1,
                                    max=365
                                ),
                                dbc.Button("Generate Forecasts", id='generate-forecast-button', color='primary', className='mt-2')
                            ], className='mb-3'),
                            dcc.Markdown('''
                                **Disclaimer:** This forecast is generated using time series forecasting methods, specifically Facebook Prophet. 
                                While this tool is useful for identifying potential trends based on historical data, stock markets are influenced by 
                                a wide range of unpredictable factors. These predictions should be considered with caution and should not be used 
                                as financial advice. Always conduct your own research or consult with a financial advisor before making investment decisions.
                            ''', style={'font-size': '14px', 'margin-top': '20px', 'color': 'gray'}),
                            
                            dcc.Loading(
                                id="loading-forecast",
                                type="default",
                                children=[dcc.Graph(id='forecast-graph')]
                            ),
                            # Blur overlay for the Forecast tab
                            html.Div(id='forecast-blur-overlay', style={
                                'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
                                'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                'backdrop-filter': 'blur(5px)'
                            }, children=[
                                html.Div([
                                    html.P("Please ", style={'display': 'inline'}),
                                    html.A("log in", href="/login", style={'display': 'inline', 'color': 'blue'}),
                                    html.P(" to view this content.", style={'display': 'inline'}),
                                ], style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'margin-top': '50px'})
                            ])
                        ], style={'position': 'relative'})
                    )
                ]),
                dcc.Tab(label='❤️ Analyst Recommendations', value='❤️ Analyst Recommendations', children=[
                    dbc.Card(
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-analyst-recommendations",
                                children=[
                                    html.Div(id='analyst-recommendations-content', className='mt-4')
                                ],
                                type="default"
                            ),
                            html.Div(id='blur-overlay', style={
                                'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
                                'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                'backdrop-filter': 'blur(5px)'
                            }, children=[
                                html.Div([
                                    html.P("Please ", style={'display': 'inline'}),
                                    html.A("log in", href="/login", style={'display': 'inline', 'color': 'blue'}),
                                    html.P(" to view this content.", style={'display': 'inline'}),
                                ], style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'margin-top': '50px'})
                            ])
                        ], style={'position': 'relative'})
                    )
                ]),
                dcc.Tab(label='📊 Investment Simulation', children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.Label("Stock Symbol:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id='simulation-stock-input',
                                    options=[],
                                    value=[],
                                    className='form-control',
                                ),
                            ], className='mb-3'),
                            html.Div([
                                html.Label("Investment Amount ($):", className="font-weight-bold"),
                                dcc.Input(
                                    id='investment-amount',
                                    type='number',
                                    placeholder='enter Amount',
                                    value=1000,
                                    className='form-control',
                                ),
                            ], className='mb-3'),
                            html.Div([
                                html.Label("Investment Date:", className="font-weight-bold"),
                                dcc.DatePickerSingle(
                                    id='investment-date',
                                    date=pd.to_datetime('2024-01-01'),
                                    className='form-control'
                                ),
                            ], className='mb-3'),
                            dbc.Button("Simulate Investment", id='simulate-button', color='primary', className='mt-2'),
                            html.Div(id='simulation-result', className='mt-4')
                        ])
                    )
                ]),
            ]),
        ], width=12, md=8)
    ], className='mb-4'),
], fluid=True)

# Layout for Registration page
register_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("📝 Register", className="text-center"),
                    dcc.Input(id='username', type='text', placeholder='Username', className='form-control mb-3'),
                    dcc.Input(id='email', type='email', placeholder='Email', className='form-control mb-3'),
                    dcc.Input(id='password', type='password', placeholder='Password', className='form-control mb-3'),
                    html.Ul([
                        html.Li("At least 8 characters", id='req-length', className='text-muted'),
                        html.Li("At least one uppercase letter", id='req-uppercase', className='text-muted'),
                        html.Li("At least one lowercase letter", id='req-lowercase', className='text-muted'),
                        html.Li("At least one digit", id='req-digit', className='text-muted'),
                        html.Li("At least one special character (!@#$%^&*(),.?\":{}|<>)_", id='req-special', className='text-muted')
                    ], className='mb-3'),
                    dcc.Input(id='confirm_password', type='password', placeholder='Confirm Password', className='form-control mb-3'),
                    dbc.Button("Register", id='register-button', color='primary', className='mt-2'),
                    html.Div(id='register-output', className='mt-3')
                ])
            ])
        ], width=12, md=6, className="mx-auto")
    ])
], fluid=True)

# Layout for Login page
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("🔐 Login", className="text-center"),
                    dcc.Input(id='login-username', type='text', placeholder='Username', className='form-control mb-3'),
                    dcc.Input(id='login-password', type='password', placeholder='Password', className='form-control mb-3'),
                    dbc.Button("Login", id='login-button', color='primary', className='mt-2 w-100'),
                    html.Div(id='login-output', className='mt-3'),
                    html.Div([
                        html.P("Don't have an account?", className="text-center"),
                        html.A("Register here", href="/register", className="text-center", style={"display": "block"})
                    ], className='mt-3')
                ])
            ])
        ], width=12, md=6, className="mx-auto")
    ])
], fluid=True)

# Layout for the About page
about_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Div([
            html.P([
                "This application provides a comprehensive platform for tracking stock market performance and related news. Here are some of the key features:"
            ], className="text-center"),
            html.Ul([
                html.Li("Track stock prices for multiple companies simultaneously."),
                html.Li("Add individual stock symbols manually."),
                html.Li("View stock prices over a specified date range."),
                html.Li("Fetch and display the latest news articles related to the selected stocks."),
                html.Li("Visualize stock prices with interactive graphs."),
                html.Li("Compare stock performance using indexed comparison graphs."),
                html.Li("Compare stock performance vs. NASDAQ100, S&P 500 or SMI (Swiss Market Index"),
                html.Li("Responsive design for use on different devices.")
            ], className="text-left"),
            html.P([
                "It is built using Dash and Plotly for interactive data visualization. For more information, visit ",
                html.A("Dash documentation", href="https://dash.plotly.com/", target="_blank"),
                "."
            ], className="text-center")
        ], className="mx-auto", style={"max-width": "600px"}))
    ]),
    dbc.Row([
        dbc.Col(html.Figure([
            html.Img(src='/assets/gif.gif', className="img-fluid mt-4", style={"width": "50%", "height": "auto"}),  # Ensure the GIF is responsive
            html.Figcaption("Get latest Stock news", className="text-center mt-2")
        ], className="text-center"))
    ]),
    dbc.Row([
        dbc.Col(html.Div([
            html.H2("About the Author"),
            html.Img(src='/assets/Portrait.png', className="img-fluid rounded-circle mt-4", style={"max-width": "150px", "height": "auto"}),
            html.P("Josua is a professional with 10+ years experience in pricing, marketing, data analysis and revenue management in the airline, consumer goods and publishing industries. He holds an executive master's in international business combined with a bachelor's degree in engineering and management and two executive certificates in data analysis and visualization. With his strong data-driven and business acumen, he strives to optimize performance and bring value to organizations."
                    ),
            html.A(
            html.Img(src='/assets/linkedin.png', className="img-fluid", style={"max-width": "30px", "height": "auto"}),
            href="https://www.linkedin.com/in/diggejos", target="_blank", className="mt-4"
        )
        ], className="text-center", style={"background-color": "#eeeeeeff", "padding": "10px", "border-radius": "10px"}))
    ])

], fluid=True)

def fetch_news(api_key, symbols):
    news_content = []
    base_url = "https://newsapi.org/v2/everything"

    for symbol in symbols:
        query = f"{symbol} stock"
        response = requests.get(base_url, params={
            'q': query,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 5  # Number of news articles to fetch
        })
        articles = response.json().get('articles', [])

        if articles:
            news_content.append(html.H4(f"News for {symbol}", className="mt-4"))
            for article in articles:
                news_card = dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(html.A(article['title'], href=article['url'], target="_blank")),
                            html.Img(src=article['urlToImage'], style={"width": "250px", "height": "auto"})
                            if article['urlToImage'] else html.Div(),
                            html.P(article.get('description', 'No summary available')),
                            html.Footer(
                                f"Source: {article['source']['name']} - Published at: {article['publishedAt']}",
                                style={"margin-bottom": "0px", "padding-bottom": "0px"}
                            )
                        ])
                    ), width=12, md=6, className="mb-2"
                )
                news_content.append(news_card)
        else:
            news_content.append(dbc.Col(html.P(f"No news found for {symbol}."), width=12))
    
    # Wrap the news_content in a Row
    return dbc.Row(news_content, className="news-row")

def fetch_analyst_recommendations(symbol):
    ticker = yf.Ticker(symbol)
    rec = ticker.recommendations
    if rec is not None and not rec.empty:
        return rec.tail(10)  # Fetch the latest 10 recommendations
    return pd.DataFrame()  # Return an empty DataFrame if no data


def generate_recommendations_heatmap(dataframe):
    # Ensure the periods and recommendations are in the correct order
    periods_order = ['-3m', '-2m', '-1m', '0m']  # Adjust according to your actual periods
    recommendations_order = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
    
    # Reshape the DataFrame to have the recommendations types as rows and the periods as columns
    df_melted = dataframe.melt(id_vars=['period'], 
                                value_vars=recommendations_order,
                                var_name='Recommendation', 
                                value_name='Count')
    
    # Ensure the period and recommendation type columns are categorical with a fixed order
    df_melted['period'] = pd.Categorical(df_melted['period'], categories=periods_order, ordered=True)
    df_melted['Recommendation'] = pd.Categorical(df_melted['Recommendation'], categories=recommendations_order, ordered=True)

    # Pivot the DataFrame to get the correct format for the heatmap
    df_pivot = df_melted.pivot(index='Recommendation', columns='period', values='Count')

    # Create the heatmap using plotly.graph_objects to add text
    fig = go.Figure(data=go.Heatmap(
        z=df_pivot.values,
        x=df_pivot.columns,
        y=df_pivot.index,
        colorscale='RdYlGn',  # Green for high, Red for low
        reversescale=False,
        text=df_pivot.values,  # Show numbers within the cells
        texttemplate="%{text}",  # Format the text to show as is
        hoverinfo="z",
        showscale=False  # Disable the color scale
    ))

    # Update layout for better visuals, ensuring labels and grid lines are visible
    fig.update_layout(
        title=None,
        autosize=True,  # Automatically adjust the size based on the container
        xaxis_title="Period",
        yaxis_title=None,
        height=300,
    
        xaxis=dict(
            autorange=False,
            ticks="",
            showticklabels=True,
            automargin=True,  # Automatically adjust margins to fit labels
            constrain='domain',  # Keep the heatmap within the plot area
            domain=[0,0.85]
        ),
        template='plotly_white',
        margin=dict(l=0, r=0, t=0, b=0),  # Increase left and top margins to avoid cutting off
    )

    return fig

# Add a callback to update the active-tab store
@app.callback(
    Output('active-tab', 'data'),
    Input('tabs', 'value')
)
def update_active_tab(value):
    return value


@app.callback(
    Output('analyst-recommendations-content', 'children'),
    Input('individual-stocks-store', 'data')
)
def update_analyst_recommendations(stock_symbols):
    if not stock_symbols:
        return html.P("Please select stocks to view their analyst recommendations.")
    
    recommendations_content = []
    
    for symbol in stock_symbols:
        df = fetch_analyst_recommendations(symbol)
        if not df.empty:
            fig = generate_recommendations_heatmap(df)
            recommendations_content.append(html.H4(f"{symbol}", className='mt-3'))
            recommendations_content.append(dcc.Graph(figure=fig))
            # Adding the link to the article on how to interpret the ratings
            recommendations_content.append(
                html.P([
                    "For more information on how to interpret these ratings, please visit ",
                    html.A("this article", href="https://finance.yahoo.com/news/buy-sell-hold-stock-analyst-180414724.html", target="_blank"),
                    "."
                ], className='mt-2')
            )
        else:
            recommendations_content.append(html.P(f"No analyst recommendations found for {symbol}."))
    
    return recommendations_content


@app.callback(
    [Output('blur-overlay', 'style'),
     Output('analyst-recommendations-content', 'style')],
    Input('login-status', 'data')
)
def update_recommendations_visibility(login_status):
    if not login_status:
        blur_style = {
            'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
            'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(5px)'
        }
        content_style = {'filter': 'blur(5px)'}
    else:
        blur_style = {'display': 'none'}
        content_style = {'filter': 'none'}
    
    return blur_style, content_style

@app.callback(
    [Output('forecast-stock-input', 'options'),
      Output('simulation-stock-input', 'options')],
    Input('individual-stocks-store', 'data')
)
def update_forecast_simulation_dropdown(individual_stocks):
    if not individual_stocks:
        return [], []
    
    options = [{'label': stock, 'value': stock} for stock in individual_stocks]
    return options, options


@app.callback(
    [Output('forecast-graph', 'figure'),
      Output('forecast-stock-warning', 'children'),
      Output('forecast-data-store', 'data')],
    [Input('generate-forecast-button', 'n_clicks')],
    [State('forecast-stock-input', 'value'),
      State('forecast-horizon-input', 'value'),
      State('predefined-ranges', 'value')]  # Added predefined-ranges state
)
def generate_forecasts(n_clicks, selected_stocks, horizon, predefined_range):
    if n_clicks and selected_stocks:
        if len(selected_stocks) > 3:
            return dash.no_update, "Please select up to 3 stocks only.", dash.no_update

        forecast_figures = []
        today = pd.to_datetime('today')

        for symbol in selected_stocks:
            try:
                df = yf.download(symbol, period='5y')  # Extended the window to 5 years
                if df.empty:
                    raise ValueError(f"No data found for {symbol}")

                df.reset_index(inplace=True)
                df_prophet = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
                model = Prophet()
                model.fit(df_prophet)

                future = model.make_future_dataframe(periods=horizon)
                forecast = model.predict(future)

                # Filtering based on predefined-range for display
                if predefined_range == 'YTD':
                    start_date = datetime(today.year, 1, 1)
                elif predefined_range == '1M':
                    start_date = today - timedelta(days=30)
                elif predefined_range == '3M':
                    start_date = today - timedelta(days=3*30)
                elif predefined_range == '12M':
                    start_date = today - timedelta(days=365)
                elif predefined_range == '24M':
                    start_date = today - timedelta(days=730)
                elif predefined_range == '5Y':
                    start_date = today - timedelta(days=1825)
                else:
                    start_date = pd.to_datetime('2023-01-01')  # Default range if no match

                df_filtered = df[df['Date'] >= start_date]
                forecast_filtered = forecast[forecast['ds'] >= start_date]

                fig = go.Figure()

                # Add forecast mean line
                fig.add_trace(go.Scatter(
                    x=forecast_filtered['ds'], 
                    y=forecast_filtered['yhat'], 
                    mode='lines', 
                    name=f'{symbol} Forecast',
                    line=dict(color='blue')
                ))

                # Add the confidence interval (bandwidth)
                fig.add_trace(go.Scatter(
                    x=forecast_filtered['ds'],
                    y=forecast_filtered['yhat_upper'],
                    mode='lines',
                    name='Upper Bound',
                    line=dict(width=0),
                    showlegend=False
                ))

                fig.add_trace(go.Scatter(
                    x=forecast_filtered['ds'],
                    y=forecast_filtered['yhat_lower'],
                    fill='tonexty',  # Fill to the next trace (yhat_upper)
                    mode='lines',
                    name='Lower Bound',
                    line=dict(width=0),
                    fillcolor='rgba(0, 100, 255, 0.2)',  # Light blue fill
                    showlegend=False
                ))

                # Add historical data
                fig.add_trace(go.Scatter(
                    x=df_filtered['Date'], 
                    y=df_filtered['Close'], 
                    mode='lines', 
                    name=f'{symbol} Historical',
                    line=dict(color='green')
                ))

                # Update layout for the plotly_white theme
                fig.update_layout(
                    template='plotly_white',
                    title=f"Stock Price Forecast for {symbol}",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=600,
                    showlegend=False
                )

                forecast_figures.append(fig)

            except Exception as e:
                fig = go.Figure()
                fig.add_annotation(text=f"Could not generate forecast for {symbol}: {e}", showarrow=False)
                forecast_figures.append(fig)

        if not forecast_figures:
            return dash.no_update, dash.no_update, dash.no_update

        # Combine all forecasts into subplots
        combined_fig = make_subplots(
            rows=len(forecast_figures), cols=1,
            shared_xaxes=True, 
            subplot_titles=selected_stocks
        )

        for i, fig in enumerate(forecast_figures):
            for trace in fig['data']:
                combined_fig.add_trace(trace, row=i+1, col=1)

        combined_fig.update_layout(
            template='plotly_white',
            title=None,
            height=400 * len(forecast_figures),
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        return combined_fig, "", combined_fig

    return go.Figure(), "", dash.no_update

@app.callback(
    Output('forecast-graph', 'figure', allow_duplicate=True),
    [Input('active-tab', 'data')],
    [State('forecast-data-store', 'data')],
    prevent_initial_call=True
)
def display_stored_forecast(active_tab, stored_forecast):
    if active_tab == '🌡️ Forecast' and stored_forecast:
        return stored_forecast
    return dash.no_update

@app.callback(
    [Output('forecast-blur-overlay', 'style'),
     Output('forecast-graph', 'style')],
    Input('login-status', 'data')
)
def update_forecast_visibility(login_status):
    if not login_status:
        blur_style = {
            'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
            'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(5px)'
        }
        content_style = {'filter': 'blur(5px)'}
    else:
        blur_style = {'display': 'none'}
        content_style = {'filter': 'none'}
    
    return blur_style, content_style

@app.callback(
    Output('register-output', 'children'),
    [Input('register-button', 'n_clicks')],
    [State('username', 'value'),
     State('email', 'value'),
     State('password', 'value'),
     State('confirm_password', 'value')]
)
def register_user(n_clicks, username, email, password, confirm_password):
    if n_clicks:
        if not username:
            return dbc.Alert("Username is required.", color="danger")
        if not email:
            return dbc.Alert("Email is required.", color="danger")
        if not password:
            return dbc.Alert("Password is required.", color="danger")
        if password != confirm_password:
            return dbc.Alert("Passwords do not match.", color="danger")
        
        # Validate the password
        password_error = validate_password(password)
        if password_error:
            return dbc.Alert(password_error, color="danger")

        # If validation passes, hash the password and save the user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return dbc.Alert("Registration successful!", color="success")
        except Exception as e:
            return dbc.Alert(f"Error: {str(e)}", color="danger")
    return dash.no_update

@app.callback(
    [Output('req-length', 'className'),
     Output('req-uppercase', 'className'),
     Output('req-lowercase', 'className'),
     Output('req-digit', 'className'),
     Output('req-special', 'className')],
    Input('password', 'value')
)
def update_password_requirements(password):
    if password is None:
        password = ""

    length_class = 'text-muted' if len(password) < 8 else 'text-success'
    uppercase_class = 'text-muted' if not re.search(r"[A-Z]", password) else 'text-success'
    lowercase_class = 'text-muted' if not re.search(r"[a-z]", password) else 'text-success'
    digit_class = 'text-muted' if not re.search(r"\d", password) else 'text-success'
    special_class = 'text-muted' if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password) else 'text-success'

    return length_class, uppercase_class, lowercase_class, digit_class, special_class


def validate_password(password):
    # Check for minimum length
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    
    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    
    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    
    # Check for at least one digit
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    
    # Check for at least one special character
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password):
        return "Password must contain at least one special character."
    
    # If all conditions are met
    return None

@app.callback(
    [Output('login-output', 'children'),
     Output('login-status', 'data', allow_duplicate=True),
     Output('login-link', 'style', allow_duplicate=True),
     Output('logout-button', 'style', allow_duplicate=True),
     Output('login-username-store', 'data'),  # Store the username
     Output('login-password', 'value')],
    [Input('login-button', 'n_clicks'),
     Input('url', 'pathname')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def handle_login(login_clicks, pathname, username, password):
    if pathname == '/login':  # Ensure this callback only runs on the login page
        if login_clicks:
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                return (dbc.Alert("Login successful!", color="success"),
                        True,
                        {"display": "none"},
                        {"display": "block"},
                        username,  # Save the username in the store
                        None)  # Clear password input
            else:
                return (dbc.Alert("Invalid username or password.", color="danger"),
                        False,
                        {"display": "block"},
                        {"display": "none"},
                        dash.no_update,
                        None)
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    [Output('login-status', 'data', allow_duplicate=True),
      Output('login-link', 'style', allow_duplicate=True),
      Output('logout-button', 'style', allow_duplicate=True)],
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call='initial_duplicate'  # Prevent initial call for duplicates
)
def handle_logout(logout_clicks):
    if logout_clicks:
        return False, {"display": "block"}, {"display": "none"}
    return dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output('theme-dropdown', 'disabled'),
    Input('login-status', 'data')
)
def update_dropdown_status(login_status):
    return not login_status  # Disable dropdown if not logged in

@app.callback(
    Output('login-overlay', 'is_open'),
    [Input('theme-dropdown-wrapper', 'n_clicks'),
     Input('save-portfolio-button', 'n_clicks')],
    [State('login-status', 'data')]
)
def show_overlay_if_logged_out(theme_n_clicks, save_n_clicks, login_status):
    # Ensure no NoneType errors
    theme_n_clicks = theme_n_clicks or 0
    save_n_clicks = save_n_clicks or 0
    
    # Debugging print to see if the callback is triggered
    print(f"Save Button Clicks: {save_n_clicks}, Theme Dropdown Clicks: {theme_n_clicks}, Logged In: {login_status}")
    
    # Show the overlay if the user is not logged in and clicks on either element
    if (theme_n_clicks > 0 or save_n_clicks > 0) and not login_status:
        return True  # Show overlay
    return False  # Don't show overlay

@app.callback(
    Output('save-portfolio-button', 'className'),
    Input('login-status', 'data')
)
def style_save_button(login_status):
    if not login_status:
        return 'grayed-out'  # Apply the grayed-out class when logged out
    return ''  # No class when logged in


def fetch_stock_data_watchlist(symbol):
    """Fetch latest stock data for a given symbol."""
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5d")
        if len(hist) < 2:
            return None, None, None
        latest_close = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2]
        change_percent = ((latest_close - previous_close) / previous_close) * 100
        return previous_close, latest_close, change_percent
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None, None, None
    

def generate_watchlist_table(watchlist):
    rows = []
    for i, stock in enumerate(watchlist):
        prev_close, latest_close, change_percent = fetch_stock_data_watchlist(stock)
        if prev_close is not None:
            # Determine the color based on the change percentage
            color = 'green' if change_percent > 0 else 'red' if change_percent < 0 else 'black'
            rows.append(
                html.Tr([
                    html.Td(stock),
                    html.Td(f"{latest_close:.2f}"),
                    html.Td(f"{change_percent:.2f}%", style={"color": color}),  # Apply the color styling here
                    html.Td(dbc.Button("X", color="danger", size="sm", id={'type': 'remove-stock', 'index': i}))
                ])
            )
        else:
            rows.append(
                html.Tr([
                    html.Td(stock),
                    html.Td("N/A"),
                    html.Td("N/A"),
                    html.Td(dbc.Button("X", color="danger", size="sm", id={'type': 'remove-stock', 'index': i}))
                ])
            )

    return dbc.Table(
        children=[
            html.Thead(html.Tr([html.Th("Stock Symbol"), 
                                html.Th("Latest"), 
                                html.Th("Change (%)"), 
                                html.Th("")])),
            html.Tbody(rows)
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        size="sm",
    )



@app.callback(
    [Output('save-portfolio-button', 'children'),
      Output('login-overlay', 'is_open', allow_duplicate=True)],
    Input('save-portfolio-button', 'n_clicks'),
    [State('individual-stocks-store', 'data'),
      State('theme-store', 'data'),
      State('login-status', 'data'),
      State('login-username-store', 'data')],
    prevent_initial_call=True
)
def save_portfolio(n_clicks, individual_stocks, selected_theme, login_status, username):
    if n_clicks:
        if login_status and username:
            user = User.query.filter_by(username=username).first()
            if user:
                try:
                    user.watchlist = json.dumps(individual_stocks)
                    user.theme = selected_theme  # Save the selected theme
                    db.session.commit()
                    return "Portfolio and Theme Saved!", False
                except Exception as e:
                    return f"Error saving portfolio: {str(e)}", False
        else:
            return dash.no_update, True  # Show the login overlay when not logged in
    return dash.no_update, False



@app.callback(
    Output('individual-stocks-store', 'data', allow_duplicate=True),
    Input('login-status', 'data'),
    State('login-username', 'value'),
    prevent_initial_call='initial_duplicate'
)
def load_watchlist(login_status, username):
    if login_status and username:
        user = User.query.filter_by(username=username).first()
        if user and user.watchlist:
            return json.loads(user.watchlist)  # Load the watchlist from the database
    return []

@app.callback(
    Output('theme-store', 'data', allow_duplicate=True),
    Input('login-status', 'data'),
    State('login-username-store', 'data'),
    prevent_initial_call=True
)
def load_user_theme(login_status, username):
    if login_status and username:
        user = User.query.filter_by(username=username).first()
        if user and user.theme:
            return user.theme
    return 'MATERIA'  # Default theme if none is found

@app.callback(
    [Output('individual-stocks-store', 'data'),
     Output('watchlist-summary', 'children'),
     Output('stock-graph', 'figure'),
     Output('stock-graph', 'style'),
     Output('stock-news', 'children'),
     Output('indexed-comparison-graph', 'figure'),
     Output('indexed-comparison-stock-dropdown', 'options'),
     Output('indexed-comparison-stock-dropdown', 'value'),
     Output('individual-stock-input', 'value')],
    [Input('add-stock-button', 'n_clicks'),
     Input('reset-stocks-button', 'n_clicks'),
     Input('refresh-data-icon', 'n_clicks'),  # New input for refresh button
     Input({'type': 'remove-stock', 'index': ALL}, 'n_clicks'),
     Input('chart-type', 'value'),
     Input('movag_input', 'value'),
     Input('benchmark-selection', 'value'),
     Input('predefined-ranges', 'value'),
     Input('indexed-comparison-stock-dropdown', 'value')],
    [State('individual-stock-input', 'value'),
     State('individual-stocks-store', 'data'),
     State('plotly-theme-store', 'data')],
    prevent_initial_call=True
)
def update_watchlist_and_graphs(add_n_clicks, reset_n_clicks, refresh_n_clicks, remove_clicks, chart_type, movag_input, benchmark_selection, predefined_range, selected_comparison_stocks, new_stock, individual_stocks, plotly_theme):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    trigger = ctx.triggered[0]['prop_id']

    if 'add-stock-button' in trigger and new_stock:
        new_stock = new_stock.upper().strip()
        if new_stock and new_stock not in individual_stocks:
            individual_stocks.append(new_stock)
    elif 'reset-stocks-button' in trigger:
        individual_stocks = []
        
    elif 'refresh-data-button' in trigger:
        # Refresh button clicked, so just update the data
        pass
    
    elif 'remove-stock' in trigger:
        index_to_remove = json.loads(trigger.split('.')[0])['index']
        if 0 <= index_to_remove < len(individual_stocks):
            individual_stocks.pop(index_to_remove)

    # Ensure benchmark is not treated as an individual stock
    if benchmark_selection in individual_stocks:
        individual_stocks.remove(benchmark_selection)

    # Update dropdown options and values
    options = [{'label': stock, 'value': stock} for stock in individual_stocks]
    if selected_comparison_stocks:
        selected_comparison_stocks = [stock for stock in selected_comparison_stocks if stock in individual_stocks]
    else:
        selected_comparison_stocks = individual_stocks[:5]  # Select up to 5 stocks by default

    if not individual_stocks and benchmark_selection == 'None':
        return (
            individual_stocks,
            generate_watchlist_table(individual_stocks),
            px.line(title="Please add at least one stock symbol.", template=plotly_theme),
            {'height': '400px'},
            html.Div("Please add at least one stock symbol."),
            px.line(title="Please add at least one stock symbol.", template=plotly_theme),
            options,
            selected_comparison_stocks,
            ""
        )

    today = pd.to_datetime('today')

    # Determine the start date based on the selected predefined range
    if predefined_range == 'YTD':
        start_date = datetime(today.year, 1, 1)
    elif predefined_range == '1M':
        start_date = today - timedelta(days=30)
    elif predefined_range == '3M':
        start_date = today - timedelta(days=3 * 30)
    elif predefined_range == '12M':
        start_date = today - timedelta(days=365)
    elif predefined_range == '24M':
        start_date = today - timedelta(days=730)
    elif predefined_range == '5Y':
        start_date = today - timedelta(days=1825)
    elif predefined_range == '10Y':
        start_date = today - timedelta(days=3650)
    else:
        start_date = pd.to_datetime('2024-01-01')

    end_date = today

    data = []
    for symbol in individual_stocks:
        df = yf.download(symbol, start=start_date, end=end_date)
        if not df.empty:
            df.reset_index(inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])  # Ensure Date is in datetime format
            df.set_index('Date', inplace=True)
            df = df.tz_localize(None)  # Drop any timezone info if not needed
            df['Stock'] = symbol
            df['30D_MA'] = df.groupby('Stock')['Close'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
            df['100D_MA'] = df.groupby('Stock')['Close'].transform(lambda x: x.rolling(window=100, min_periods=1).mean())
            data.append(df)

    if not data and benchmark_selection == 'None':
        return (
            individual_stocks,
            generate_watchlist_table(individual_stocks),
            px.line(title="No data found for the given stock symbols and date range.", template=plotly_theme),
            {'height': '400px'},
            html.Div("No news found for the given stock symbols."),
            px.line(title="No data found for the given stock symbols and date range.", template=plotly_theme),
            options,
            selected_comparison_stocks,
            ""
        )

    df_all = pd.concat(data) if data else pd.DataFrame()

    # Create an index for each stock
    indexed_data = {}
    for symbol in individual_stocks:
        if symbol in df_all['Stock'].unique():
            df_stock = df_all[df_all['Stock'] == symbol].copy()
            df_stock['Index'] = df_stock['Close'] / df_stock['Close'].iloc[0] * 100
            indexed_data[symbol] = df_stock[['Index']].rename(columns={"Index": symbol})

    # Add benchmark index to the indexed data if selected
    if benchmark_selection != 'None':
        benchmark_data = yf.download(benchmark_selection, start=start_date, end=end_date)
        if not benchmark_data.empty:
            benchmark_data.reset_index(inplace=True)
            benchmark_data['Index'] = benchmark_data['Close'] / benchmark_data['Close'].iloc[0] * 100

    # Combine all indexed data
    if indexed_data:
        df_indexed = pd.concat(indexed_data, axis=1)
        df_indexed.reset_index(inplace=True)
        df_indexed.columns = ['Date'] + [symbol for symbol in indexed_data.keys()]
        df_indexed['Date'] = pd.to_datetime(df_indexed['Date'], errors='coerce')

        # Filter the data based on selected stocks from the dropdown
        df_indexed_filtered = df_indexed[['Date'] + selected_comparison_stocks]

        # Create indexed comparison figure
        fig_indexed = px.line(df_indexed_filtered, x='Date', y=selected_comparison_stocks, template=plotly_theme)
        fig_indexed.update_yaxes(matches=None, title_text=None)
        fig_indexed.update_xaxes(title_text=None)
        fig_indexed.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            font=dict(size=10)
        ), legend_title_text=None, margin=dict(l=10, r=10, t=15, b=10))

        fig_indexed.add_shape(
            type='line',
            x0=df_indexed['Date'].min(),
            y0=100,
            x1=df_indexed['Date'].max(),
            y1=100,
            line=dict(
                color="Black",
                width=2,
                dash="dot"
            )
        )

        # Add benchmark line as dotted if selected
        if benchmark_selection != 'None':
            fig_indexed.add_scatter(x=benchmark_data['Date'], y=benchmark_data['Index'], mode='lines',
                                    name=benchmark_selection, line=dict(dash='dot'))

    else:
        fig_indexed = px.line(title="No data available.", template=plotly_theme)

    # Determine the number of rows needed for the stock graph
    num_stocks = len(individual_stocks)
    graph_height = 400 * num_stocks  # Each facet should be 400px in height

    # Create the stock graph with the correct layout
    fig_stock = make_subplots(
        rows=num_stocks,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,  # Keep this small to maintain consistent spacing
        subplot_titles=individual_stocks,
        row_heights=[1] * num_stocks,
        specs=[[{"secondary_y": True}]] * num_stocks
    )

    for i, symbol in enumerate(individual_stocks):
        df_stock = df_all[df_all['Stock'] == symbol]

        if chart_type == 'line':
            fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['Close'], name=f'{symbol} Close',
                                           line=dict(color='blue')), row=i + 1, col=1)

            # Get the most recent price and percentage change
            last_close = df_stock['Close'].iloc[-2]
            latest_close = df_stock['Close'].iloc[-1]
            change_percent = ((latest_close - last_close) / last_close) * 100

            # Add the last available data point as a marker
            fig_stock.add_trace(go.Scatter(
                x=[df_stock.index[-1]],
                y=[latest_close],
                mode='markers',
                marker=dict(color='red', size=10),
                name=f'{symbol} Last Price'
            ), row=i + 1, col=1)

            # Add annotations for the latest price and percentage change
            latest_timestamp = df_stock.index[-1]
            fig_stock.add_annotation(
                x=latest_timestamp,
                y=latest_close,
                text=f"{latest_close:.2f} ({change_percent:.2f}%)<br>{latest_timestamp.strftime('%Y-%m-%d')}",
                showarrow=True,
                arrowhead=None,
                ax=20,  # Adjusted to position the annotation to the right
                ay=-40,
                row=i + 1,
                col=1,
                font=dict(color="blue", size=12),
                bgcolor='white'
            )

            fig_stock.add_shape(
                type="line",
                x0=df_stock.index.min(),
                x1=df_stock.index.max(),
                y0=latest_close,
                y1=latest_close,
                line=dict(
                    color="red",
                    width=2,
                    dash="dot"
                ),
                row=i + 1, col=1
            )
        elif chart_type == 'candlestick':
            fig_stock.add_trace(go.Candlestick(
                x=df_stock.index,
                open=df_stock['Open'],
                high=df_stock['High'],
                low=df_stock['Low'],
                close=df_stock['Close'],
                name=f'{symbol} Candlestick'), row=i + 1, col=1)

            fig_stock.update_xaxes(rangeslider={'visible': False}, row=i + 1, col=1)

        if 'Volume' in movag_input:
            fig_stock.add_trace(go.Bar(x=df_stock.index, y=df_stock['Volume'], name=f'{symbol} Volume',
                                       marker=dict(color='gray'), opacity=0.3), row=i + 1, col=1, secondary_y=True)
            fig_stock.update_yaxes(showgrid=False, secondary_y=True, row=i + 1, col=1)

        if '30D_MA' in movag_input:
            fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['30D_MA'], name=f'{symbol} 30D MA',
                                           line=dict(color='green')), row=i + 1, col=1)

        if '100D_MA' in movag_input:
            fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['100D_MA'], name=f'{symbol} 100D MA',
                                           line=dict(color='red')), row=i + 1, col=1)

    fig_stock.update_layout(template=plotly_theme, height=graph_height, showlegend=False,
                            margin=dict(l=40, r=40, t=40, b=40))
    fig_stock.update_yaxes(title_text=None, secondary_y=False)
    fig_stock.update_yaxes(title_text=None, secondary_y=True, showgrid=False)

    load_dotenv()
    api_key = os.getenv('API_KEY')

    news_content = fetch_news(api_key, individual_stocks)

    return individual_stocks, generate_watchlist_table(individual_stocks), fig_stock, {
        'height': f'{graph_height}px', 'overflow': 'auto'}, news_content, fig_indexed, options, selected_comparison_stocks, ""


@app.callback(Output('simulation-result', 'children'),
              Input('simulate-button', 'n_clicks'),
              State('simulation-stock-input', 'value'),
              State('investment-amount', 'value'),
              State('investment-date', 'date'),
              State('plotly-theme-store', 'data'))

def simulate_investment(n_clicks, stock_symbol, investment_amount, investment_date, plotly_theme):
    if n_clicks and stock_symbol and investment_amount and investment_date:
        investment_date = pd.to_datetime(investment_date)
        end_date = pd.to_datetime('today')
        data = yf.download(stock_symbol, start=investment_date, end=end_date)
        if not data.empty:
            initial_price = data['Close'].iloc[0]
            current_price = data['Close'].iloc[-1]
            shares_bought = investment_amount / initial_price
            current_value = shares_bought * current_price
            profit = current_value - investment_amount

            # Create waterfall chart
            fig_waterfall = go.Figure(go.Waterfall(
                name="Investment Analysis",
                orientation="v",
                measure=["absolute", "relative", "total"],
                x=["Initial Investment", "Profit/Loss", "Current Value"],
                y=[investment_amount, profit, current_value],
                text=[f"${investment_amount:.2f}", f"${profit:.2f}", f"${current_value:.2f}"],
                textposition="inside",
                insidetextfont={"color": "white"},
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "red"}},
                increasing={"marker": {"color": "green"}},
                totals={"marker": {"color": "grey"}}
            ))
            fig_waterfall.update_layout(
                showlegend=False,
                template=plotly_theme,
                yaxis=dict(visible=False),
                margin=dict(t=100,l=10,r=10,b=10)  
            )

            return html.Div([
                html.P(f"Initial Investment Amount: ${investment_amount:.2f}", className='mb-2'),
                html.P(f"Shares Bought: {shares_bought:.2f}", className='mb-2'),
                html.P(f"Current Value: ${current_value:.2f}", className='mb-2'),
                html.P(f"Profit: ${profit:.2f}", className='mb-2'),
                dcc.Graph(figure=fig_waterfall)
            ])
        else:
            return html.Div([
                html.P(f"No data available for {stock_symbol} from {investment_date.strftime('%Y-%m-%d')}", className='mb-2')
            ])
    return dash.no_update


@app.callback(
    [Output('page-content', 'children'),
      Output('register-link', 'style')],
    [Input('url', 'pathname'),
      Input('login-status', 'data')]
)
def display_page(pathname, login_status):
    if pathname == '/about':
        return about_layout, {"display": "block"} if not login_status else {"display": "none"}
    elif pathname == '/register':
        return register_layout, {"display": "block"} if not login_status else {"display": "none"}
    elif pathname == '/login' and not login_status:
        return login_layout, {"display": "block"} if not login_status else {"display": "none"}
    else:
        return dashboard_layout, {"display": "block"} if not login_status else {"display": "none"}

@app.callback(
    [Output('theme-store', 'data'),
     Output('plotly-theme-store', 'data')],
    [Input(f'theme-{theme}', 'n_clicks') for theme in themes.keys()],
    [State('login-status', 'data'),
     State('login-username-store', 'data')]
)
def update_theme(*args, login_status=None, username=None):
    ctx = dash.callback_context

    # Check if any theme button was clicked
    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0].startswith('theme-'):
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        theme = button_id.split('-')[1]
        return themes[theme]['dbc'], themes[theme]['plotly']

    # If no theme button was clicked, load the user's theme
    if login_status and username:
        user = User.query.filter_by(username=username).first()
        if user and user.theme:
            return themes[user.theme]['dbc'], themes[user.theme]['plotly']

    # Default theme if no selection was made or user not logged in
    return dbc.themes.MATERIA, 'plotly_white'

@app.callback(
    Output('theme-switch', 'href'),
    Input('theme-store', 'data')
)
def update_stylesheet(theme):
    return theme

# Callback to handle the collapse toggle and emoji change
@app.callback(
    [Output("filters-collapse", "is_open"),
     Output("toggle-filters-button", "children")],
    [Input("toggle-filters-button", "n_clicks")],
    [State("filters-collapse", "is_open")]
)
def toggle_filters_visibility(n_clicks, is_open):
    if n_clicks:
        is_open = not is_open  # Toggle the state
    # Change the emoji based on the collapse state
    emoji = "🔽" if not is_open else "🔼"
    return is_open, emoji

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Josua's Stock Dashboard</title>
        <meta name="description" content="Track and forecast stock prices, visualize trends, and get the latest stock news with MyStock's Stock Dashboard.">
        <meta name="keywords" content="stock, stocks, stock dashboard, finance, stock forecasting, stock news">
        <meta name="author" content="myStock">
        <meta property="og:title" content="myStock Dashboard" />
        <meta property="og:description" content="Get the latest stock news, forecasts, and more." />
        <meta property="og:image" content="https://mystocks-m9xp.onrender.com/assets/og-image.png" />
        <meta property="og:url" content="https://mystocks-m9xp.onrender.com/" />
        <meta name="twitter:card" content="summary_large_image" />
        {%favicon%}
        {%css%}
        <link id="theme-switch" rel="stylesheet" href="{{ external_stylesheets[0] }}">
        <style>
            .news-row > .col-md-6 {
                flex: 0 0 50%;
                max-width: 50%;
            }
            @media (max-width: 768px) {
                .news-row > .col-md-6 {
                    flex: 0 0 100%;
                    max-width: 100%;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)

