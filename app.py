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
from dash.exceptions import PreventUpdate
from dash_extensions import DeferScript
from flask import session
from flask_session import Session
import dash_table
from flask import send_from_directory
from flask import render_template


# List of available Bootstrap themes and corresponding Plotly themes
themes = {
    'CYBORG': {'dbc': dbc.themes.CYBORG, 'plotly': 'plotly_dark'},
    'JOURNAL': {'dbc': dbc.themes.JOURNAL, 'plotly': 'simple_white'},
    'MATERIA': {'dbc': dbc.themes.MATERIA, 'plotly': 'simple_white'},
    'MINTY': {'dbc': dbc.themes.MINTY, 'plotly': 'simple_white'},
    'SPACELAB': {'dbc': dbc.themes.SPACELAB, 'plotly': 'simple_white'},
    'DARKLY': {'dbc': dbc.themes.DARKLY, 'plotly': 'plotly_dark'},
    'LITERA': {'dbc': dbc.themes.LITERA, 'plotly': 'plotly_white'},
    'SOLAR': {'dbc': dbc.themes.SOLAR, 'plotly': 'plotly_dark'},
}


# Initialize the Dash app with a default Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
server = app.server

# load robots.txt file for SEO
@server.route('/robots.txt')
def serve_robots_txt():
    return send_from_directory(os.path.join(server.root_path, 'static'), 'robots.txt')

# Define a custom 404 error handler
@app.server.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure the session
load_dotenv()
app.server.config['SECRET_KEY'] =  os.getenv('FLASK_SECRET_KEY') # Use a strong, unique secret key
app.server.config['SESSION_TYPE'] = 'filesystem' 

Session(app.server)

db = SQLAlchemy(server)
# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(server)

@server.route('/sitemap.xml')
def sitemap():
    return send_from_directory(directory='static', path='sitemap.xml')

@server.route('/robots.txt')
def serve_robots():
    return send_from_directory(project_root, 'robots.txt')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(200), nullable=True)  # New field for storing the theme
    watchlists = db.relationship('Watchlist', backref='user', lazy=True)

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stocks = db.Column(db.Text, nullable=False)  # JSON list of stock symbols
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False)  # New field to mark as default
     
# Create the database tables
with server.app_context():
    db.create_all()

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("📈 Dashboard", href="/", active="exact")),
        dbc.NavItem(dbc.NavLink("ℹ️ About", href="/about", active="exact")),
        dbc.NavItem(dbc.NavLink("👤 Profile", href="/profile", active="exact", id='profile-link', style={"display": "none"})),  # New profile link
        dbc.NavItem(dbc.NavLink("📝 Register", href="/register", active="exact", id='register-link')),
        dbc.NavItem(dbc.NavLink("🔐 Login", href="/login", active="exact", id='login-link', style={"display": "block"})),
        dbc.NavItem(dbc.Button("Logout", id='logout-button', color='secondary', style={"display": "none"})),
        html.Div([
            dbc.DropdownMenu(
                children=[dbc.DropdownMenuItem(theme, id=f'theme-{theme}') for theme in themes],
                nav=True,
                in_navbar=True,
                label="🎨 Select Theme",
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

# Create a sticky footer with tabs for mobile view
sticky_footer_mobile = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("📈 Prices", href="#prices", id="footer-prices-tab")),
        dbc.NavItem(dbc.NavLink("📰 News", href="#news", id="footer-news-tab")),
        dbc.NavItem(dbc.NavLink("⚖️ Compare", href="#comparison", id="footer-compare-tab")),
        dbc.NavItem(dbc.NavLink("🌡️ Forecast", href="#forecast", id="footer-forecast-tab")),
        dbc.NavItem(dbc.NavLink("📊 Simulate", href="#simulation", id="footer-simulate-tab")),
        dbc.NavItem(dbc.NavLink("❤️ Recommendations", href="#recommendations", id="footer-recommendations-tab"))
    ],
    pills=True,
    justified=True,
    # className= "footer-nav",
    className="footer-nav flex-nowrap overflow-auto",
    style={"white-space": "nowrap"}
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

floating_chatbot_button = html.Div(
    dbc.Button("💬 ask me", id="open-chatbot-button", color="primary", className="chatbot-button"),
    style={
        "position": "fixed",
        "bottom": "100px",
        "right": "20px",
        "z-index": "1002",
    }
)

financials_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle(id="financials-modal-title")),
        dbc.ModalBody(id="financials-modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-financials-modal", className="ms-auto", n_clicks=0)
        ),
    ],
    id="financials-modal",
    size="lg",
    is_open=False,
)

chatbot_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("🤖 Financio")),
        dbc.ModalBody([
            html.Div(id='chatbot-conversation',
                     style={'border': '1px solid #ccc', 'border-radius': '10px', 'padding': '10px',
                            'height': '400px', 'overflow-y': 'scroll', 'background-color': '#f8f9fa', 'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'}),
            dcc.Textarea(id='chatbot-input',
                         placeholder='Ask your financial question...',
                         style={'width': '100%', 'height': '100px', 'border-radius': '10px', 'border': '1px solid #ccc',
                                'padding': '10px', 'margin-top': '10px', 'resize': 'none', 'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'}),
            dbc.Button("Send", id='send-button', color='primary', className='mt-2'),
            dbc.Button("Clear Conversation", id='clear-button', color='danger', className='mt-2 ms-2'),
        ])
    ],
    id="chatbot-modal",
    size="lg",
    is_open=False,
    className="bg-primary"# Start closed
)

footer = html.Footer([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H5("Direction", style={"display": "none"}),  # Hide the heading
                html.Ul([
                    html.Li(html.A("About MyStocks", href="/about", className="footer-link")),
                    html.Li(html.A("Contact Us", href="mailto:diggelmann.josua@gmail.com?subject=mystocks%20request", className="footer-link")),
                    html.Li(html.A("Dashboard", href="/dashboard", className="footer-link")),
                ], className="list-unstyled")
            ], md=12, className="d-flex justify-content-center")  # Center the column
        ]),
        dbc.Row([
            dbc.Col([
                html.P("© 2024 MyStocks. All rights reserved.", className="text-center")
            ], className="d-flex justify-content-center")
        ])
    ], fluid=True)
], className="footer")

watchlist_management_layout = dbc.Container([
    dcc.Input(id='new-watchlist-name', placeholder="Enter Watchlist Name", className="form-control",disabled=True),
    html.Label(" Saved Watchlists:", className="font-weight-bold",style={"margin-top": "10px"}),
    dcc.Dropdown(id='saved-watchlists-dropdown', placeholder="Select a Watchlist", options=[],clearable=True,disabled=True, style={"margin-top": "10px"}),
    dbc.Button("💾 Watchlist", id='create-watchlist-button', color='primary', className='',disabled=False),
    dbc.Button("X Watchlist", id='delete-watchlist-button', color='danger', className='',disabled=False)
])

app.layout = html.Div([
    dcc.Store(id='conversation-store', data=[]),  # Store to keep the conversation history
    dcc.Store(id='individual-stocks-store', data=['AAPL']),
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
    dcc.Location(id='url-refresh', refresh=True),
    DeferScript(src='assets/script.js'),
    floating_chatbot_button,  # Add the floating button
    chatbot_modal ,
    financials_modal,
    html.Div(sticky_footer_mobile, id="sticky-footer-container"),
    footer
])

dashboard_layout = dbc.Container([
    dbc.Row([
        # Sidebar Filters (for both mobile and desktop)
        dbc.Col([
            html.H1("Stocks monitoring dashboard - MyStocks", style={"display": "none"}), 
            html.H2("Stocks monitoring made easy. Create multiple personal watchlists", style={"display": "none"}), 
            html.Div([
                html.P("Welcome to MyStocks - the ultimate platform for stock monitoring. Track stock prices, analyze market trends, and create personalized watchlists with ease. Our dashboard is designed to provide real-time data, forecasts, and insights tailored to your investment portfolio."),
                html.P("With MyStocks, you can compare stock performance, simulate investments, and access the latest news and analyst recommendations. Whether you're a seasoned trader or a beginner, MyStocks offers tools and features that help you make informed investment decisions."),
                html.P("Create multiple custom watchlists and monitor your stocks with real-time updates. MyStocks allows you to easily manage and organize your investments across different watchlists."),
                html.P("Get access to historical stock data and perform in-depth analysis with our comprehensive charting tools. MyStocks also offers forecasting features, allowing you to predict future stock prices using advanced algorithms."),
                html.P("Our platform also integrates with popular news sources to provide you with up-to-date news and information on your favorite stocks."),
                html.P("MyStocks is your one-stop solution for stock monitoring, forecasting, news aggregation, and personalized investment tools. Try MyStocks today and take control of your investments like never before."),
                html.P("Key Features: Historical Stock Price Tracking, Stock Market News, Profit/Loss Simulation, Analyst Recommendations, Time Series Forecasting, Personalized Watchlist, Stock Performance Comparison, Intelligent Financial Chatbot."),
            ], style={"display": "none"}),  # This text is hidden but available for SEO

            # Toggle button (only visible on mobile)
            dbc.Button(
                "⚙️ Manage your Stocks here", 
                id="toggle-filters-button", 
                color="danger", 
                outline=False, 
                size="sm", 
                className="mobile-only", 
                style={
                    "position": "fixed",  
                    "top": "110px",        
                    "left": "10px",      
                    "z-index": "1001",     
                    "margin-bottom": "15px",
                    "font-weight": "bold"
                }
            ),
            
            html.Div(id="mobile-overlay", className="mobile-overlay", style={"display": "none"}),

            # Offcanvas Filters (for mobile and hidden on desktop)
            dbc.Collapse(
                dbc.Card([
                    dbc.CardBody([
                        html.H2("Filter stocks, create custom watchlist", style={"display": "none"}),  # for SEO

                        html.Div([
                            html.Label("Add Stock Symbol:", className="font-weight-bold"),
                            dcc.Input(
                                id='individual-stock-input',
                                type='text',
                                placeholder='e.g. AAPL',
                                debounce=True,
                                className='form-control'
                            ),
                            dbc.Button("➕ Stock", id='add-stock-button', color='primary', className='small-button'),
                            dbc.Button("Reset all", id='reset-stocks-button', color='danger', className='small-button'),
                            html.Span("🔄", id='refresh-data-icon', style={'cursor': 'pointer', 'font-size': '25px'}, className='mt-2 me-2'),
                        ], className='mb-3'),
                        
                        dcc.Loading(id="loading-watchlist", type="default", children=[
                            html.Div(id='watchlist-summary', className='mb-3')
                        ]),
                        
                        html.Div([
                            html.Label("Select Date Range:", className="font-weight-bold"),
                            dcc.Dropdown(
                                id='predefined-ranges',
                                options=[
                                    {'label': 'Intraday', 'value': '1D_15m'},
                                    {'label': 'Last 5D', 'value': '5D_15m'},
                                    {'label': 'Last Month', 'value': '1M'},
                                    {'label': 'Last 3M', 'value': '3M'},
                                    {'label': 'Year to Date', 'value': 'YTD'},
                                    {'label': 'Last 12M', 'value': '12M'},
                                    {'label': 'Last 24M', 'value': '24M'},
                                    {'label': 'Last 5Y', 'value': '5Y'},
                                    {'label': 'Last 10Y', 'value': '10Y'}
                                ],
                                value='12M',  # Default selection
                                # className='form-control',
                            )
                        ], className='mb-3'),
                    ]),
                    watchlist_management_layout
                ], className="sidebar-card"),
                id="filters-collapse",
                is_open=False  # Initially closed (for mobile use case)
            ),
        ], width=12, md=3, style={"margin-top": "10px"}),

        # Main content area (Tabs for Prices, News, Comparison, etc.)
        dbc.Col([
            dbc.Tabs(
                id="tabs",
                active_tab="prices-tab",  # This should be the id of the active tab
                children=[
                    dbc.Tab(label='📈 Prices', tab_id="prices-tab", children=[
                        dbc.Card(
                            dbc.CardBody([
                                dcc.Dropdown(
                                    id='prices-stock-dropdown',
                                    options=[],  
                                    value=[],  
                                    multi=True,
                                    placeholder="Select stocks to display",
                                    # style={'width': '70%'}
                                ),
                                dcc.RadioItems(
                                    id='chart-type',
                                    options=[
                                        {'label': 'Line Chart', 'value': 'line'},
                                        {'label': 'Candlestick Chart', 'value': 'candlestick'}
                                    ],
                                    value='line',
                                    inline=True,
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
                                dcc.Loading(id="loading-prices", type="default", children=[
                                    dcc.Graph(id='stock-graph', style={'height': '500px', 'backgroundColor': 'transparent'})
                                ])
                            ])
                        )
                    ]),
                    dbc.Tab(label='📰 News', tab_id="news-tab", children=[
                        dbc.Card(
                            dbc.CardBody([
                                dcc.Loading(id="loading-news", type="default", children=[
                                    html.Div(id='stock-news', className='news-container')
                                ])
                            ])
                        )
                    ]),
                    dbc.Tab(label='⚖️ Compare', tab_id="compare-tab", children=[
                        dbc.Card(
                            dbc.CardBody([
                                html.Label("Select Stocks for Comparison:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id='indexed-comparison-stock-dropdown',
                                    options=[],  # Populated dynamically
                                    value=[],  # Default selected stocks
                                    multi=True,
                                    # style={'width': '70%'}
                                    # className='form-control',
                                ),
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
                                    # className='form-control',
                                    inputStyle={"margin-right": "10px"},
                                    labelStyle={"margin-right": "20px"}
                                ),
                                dcc.Loading(id="loading-comparison", type="default", children=[
                                    dcc.Graph(id='indexed-comparison-graph', style={'height': '500px'})
                                ])
                            ])
                        )
                    ]),
                    dbc.Tab(label='🌡️ Forecast', tab_id='forecast-tab', children=[
                        dbc.Card(
                            dbc.CardBody([
                                html.H3("Forecast stocks prices", style={"display": "none"}),  # for SEO purpose (visually hidden)
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
                                    children=[dcc.Graph(id='forecast-graph', style={'height': '500px'})]
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
                     dbc.Tab(label='❤️ Analyst Recommendations', tab_id='recommendations-tab', children=[
                         dbc.Card(
                             dbc.CardBody([
                                 html.H3("Get analyst stock recommendations", style={"display": "none"}),  # for SEO purpose (visually hidden)
                                 dcc.Loading(
                                     id="loading-analyst-recommendations",
                                     type="default",
                                     children=[html.Div(id='analyst-recommendations-content', className='mt-4')]
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
                    dbc.Tab(label='📊 Simulate', tab_id="simulate-tab", children=[
                        dbc.Card(
                            dbc.CardBody([
                                html.Label("Stock Symbol:", className="font-weight-bold"),
                                dcc.Dropdown(
                                    id='simulation-stock-input',
                                    options=[],  
                                    value=[],  
                                    className='form-control',
                                ),
                                html.Label("Investment Amount ($):", className="font-weight-bold"),
                                dcc.Input(
                                    id='investment-amount',
                                    type='number',
                                    value=1000,
                                    className='form-control',
                                ),
                                html.Label("Investment Date:", className="font-weight-bold"),
                                dcc.DatePickerSingle(
                                    id='investment-date',
                                    date=pd.to_datetime('2024-01-01'),
                                    className='form-control'
                                ),
                                dbc.Button("Simulate Investment", id='simulate-button', color='primary', className='mt-2'),
                                dcc.Loading(id="loading-simulation", type="default", children=[
                                    html.Div(id='simulation-result', className='mt-4')
                                ])
                            ])
                        )
                    ]),
                ], className="desktop-tabs bg-secondary" #className="desktop-tabs" 
            )
        ], width=12, md=9, xs=12)
    ], className='mb-4'),
    
    # Welcome section
    dbc.Row([
        dbc.Col([
            html.H3("Welcome to Your Stock Monitoring Dashboard. Save your watchlists, monitoring stocks made easy", className="text-center mb-4", style={"display": "none"}),
            html.P([
                "Track and analyze your favorite stocks with real-time data, forecasts, and personalized recommendations. ",
                html.A("Learn more about the features.", href="/about", className="text-primary")
            ], className="text-center"),
        ], width=12)
    ], className="mb-4")
], fluid=True)

profile_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H1("👩🏻‍💻 User Profile", className="text-center"),

                    # Username field
                    dbc.Label("Username"),
                    dcc.Input(id='profile-username', type='text', disabled=True, className='form-control mb-3'),

                    # Email field
                    dbc.Label("Email"),
                    dcc.Input(id='profile-email', type='email', disabled=True, className='form-control mb-3'),

                    # Current Password field (Required to change the password)
                    dbc.Label("Current Password"),
                    dcc.Input(id='profile-current-password', type='password', disabled=True, placeholder="Enter current password", className='form-control mb-3'),

                    # New Password field
                    dbc.Label("New Password"),
                    dcc.Input(id='profile-password', type='password', disabled=True, placeholder="Enter new password", className='form-control mb-3'),

                    html.Ul([
                        html.Li("At least 8 characters", id='profile-req-length', className='text-muted'),
                        html.Li("At least one uppercase letter", id='profile-req-uppercase', className='text-muted'),
                        html.Li("At least one lowercase letter", id='profile-req-lowercase', className='text-muted'),
                        html.Li("At least one digit", id='profile-req-digit', className='text-muted'),
                        html.Li("At least one special character (!@#$%^&*(),.?\":{}|<>)_", id='profile-req-special', className='text-muted')
                    ], className='mb-3', style={"display": "none"}),  # Initially hidden

                    # Confirm New Password field
                    dbc.Label("Confirm New Password"),
                    dcc.Input(id='profile-confirm-password', type='password', disabled=True, placeholder="Confirm new password", className='form-control mb-3'),

                    # Edit and Save buttons
                    dbc.Button("Edit", id='edit-profile-button', color='primary', className='mt-2'),
                    dbc.Button("Save", id='save-profile-button', color='success', className='mt-2 ms-2', style={"display": "none"}),
                    dbc.Button("Cancel", id='cancel-edit-button', color='danger', className='mt-2 ms-2', style={"display": "none"}),

                    # Output area for messages
                    html.Div(id='profile-output', className='mt-3')
                ])
            ])
        ], width=12, md=6, className="mx-auto")
    ])
], fluid=True)

# Layout for Registration page
register_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # New h3 paragraph with a sentence and link to the About page
                    html.H1("📝 Register", className="text-center mt-4"),
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
                    dbc.Button("Register", id='register-button', color='primary', className='mt-2 w-100'),
                    html.Div(id='register-output', className='mt-3'),
                ])
            ])
        ], width=12, md=6, className="mx-auto")
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Login here", className="text-center mt-5 mb-4"),
            html.P([
                "Successfully registered? ",
                html.A("Login here", href="/login", className="text-primary")
            ], className="text-center"),

            html.H3("Why Register?", className="text-center mt-5 mb-4"),  # Add mt-5 for space above
            html.P([
                "Registering allows you to save your stock watchlist, access personalized recommendations, and more. ",
                html.A("Learn more on the About page.", href="/about", className="text-primary")
            ], className="text-center")
        ], width=12, md=6, className="mx-auto")
    ])
], fluid=True)

# Layout for Login page
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H1("🔐 Login", className="text-center"),
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
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Welcome to MyStocks Dashboard", className="text-center mt-5 mb-4"),  # Add mt-5 for space above
            html.P([
                "Learn more about the application on the ",
                html.A("About page.", href="/about", className="text-primary")
            ], className="text-center")
        ], width=12, md=6, className="mx-auto")
    ])
], fluid=True)

# Enhanced Carousel Component
carousel = dbc.Carousel(
    items=[
        {
            "key": "1",
            "src": "/assets/gif1.gif",
            "alt": "Demo 1",
            "header": "Analyse and Compare Stocks",
            "caption": "Financial indicators, custom time windows, and more."
        },
        {
            "key": "2",
            "src": "/assets/gif4.gif",
            "alt": "Demo 2",
            "header": "Chatbot Advisor",
            "caption": "Ask your personal Chatbot for advice."
        },
        {
            "key": "3",
            "src": "/assets/gif2.gif",
            "alt": "Demo 3",
            "header": "Custom Watchlist",
            "caption": "Save your watchlist and get tailored news updates."
        },
        {
            "key": "4",
            "src": "/assets/gif3.gif",
            "alt": "Demo 4",
            "header": "Timeseries Forecast",
            "caption": "Visualize forecasts and access analyst recommendations."
        }
    ],
    controls=True,
    indicators=True,
    interval=20000,  # Time in ms for each slide
    ride="carousel",
    className="custom-carousel",  # Add custom-carousel class
    id="custom-carousel"
)

# Modernized About Layout
about_layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Div([
            # Hidden H1 for SEO
            html.H1("About MyStock Dashboard", className="text-center mt-4", style={"display": "none"}),

            # Section: Why Choose MyStocks?
            html.Div([
                html.H2("Why Choose MyStocks?", className="text-center mt-5 mb-3"),
                html.P("Comprehensive Data: Access to a wide range of financial data and tools for better decision-making. "
                       "User-Friendly Interface: Simple and intuitive design, making it easy for users at all levels to navigate. "
                       "Advanced Analytics: Leverage sophisticated forecasting and simulation tools to gain a competitive edge. "
                       "Real-Time Updates: Stay informed with up-to-date news and market data.", className="lead text-center"),
            ], style={"padding": "20px", "background-color": "#f8f9fa", "border-radius": "10px"}),

            # Carousel
            html.Div(carousel, className="mt-5 mb-3"),

            # Section: Key Features
            html.Div([
                html.H3("Key Features", className="text-center mt-5 mb-3"),
                html.P("This application provides a comprehensive platform for tracking stock market performance and related news. "
                       "Here are some of the key features:", className="text-center", style={"display": "none"}),
                html.Ul([
                    html.Li("Historical Stock Price Tracking: Compare stock prices over historical periods. Perform indexed comparisons against major indices."),
                    html.Li("Stock Market News: Stay updated with the latest news for your selected stocks from reliable sources."),
                    html.Li("Profit/Loss Simulation: Simulate potential profit and loss scenarios for stocks in your watchlist."),
                    html.Li("Analyst Recommendations: Access buy, sell, and hold ratings from industry experts."),
                    html.Li("Time Series Forecasting: Predict future stock prices using advanced forecasting models."),
                    html.Li("Personalized Watchlist: Register and save your stock watchlist to monitor your favorite stocks."),
                    html.Li("Stock Performance Comparison: Compare stock performance vs. NASDAQ100, S&P 500, or SMI."),
                    html.Li("Intelligent Financial Chatbot: Get instant answers to your stock-related queries."),
                    html.Li("Save and customize your personal watchlist."),
                ], className="checked-list"),
            ], style={"padding": "20px", "background-color": "#ffffff", "border-radius": "10px", "box-shadow": "0px 2px 5px rgba(0,0,0,0.1)"}),
        ], className="mx-auto", style={"max-width": "900px"}))
    ]),
], fluid=True)

def fetch_news(symbols, max_articles=4):
    news_content = []

    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        news = ticker.news  # Fetch news using yfinance

        if news:
            news_content.append(html.H4(f"News for {symbol}", className="mt-4"))

            for idx, article in enumerate(news[:max_articles]):  # Display only the first `max_articles` news articles
                related_tickers = ", ".join(article.get('relatedTickers', []))
                news_card = dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(html.A(article['title'], href=article['link'], target="_blank")),
                            html.Img(src=article['thumbnail']['resolutions'][0]['url'], style={"width": "250px", "height": "auto"})
                            if 'thumbnail' in article else html.Div(),
                            html.P(f"Related Tickers: {related_tickers}" if related_tickers else "No related tickers available."),
                            html.Footer(
                                f"Published at: {datetime.utcfromtimestamp(article['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')}",
                                style={"margin-bottom": "0px", "padding-bottom": "0px"}
                            )
                        ])
                    ), width=12, md=6, className="mb-2"
                )
                news_content.append(news_card)

            if len(news) > max_articles:
                # Add a "Load More" button if there are more articles available
                news_content.append(
                    dbc.Button("Load More", id={'type': 'load-more-button', 'index': symbol}, color='primary', size='sm', className='mb-2')
        
                )
                news_content.append(html.Div(id={'type': 'additional-news', 'index': symbol}))
        else:
            news_content.append(dbc.Col(html.P(f"No news found for {symbol}."), width=12))
    
    return dbc.Row(news_content, className="news-row")

from dash.dependencies import Input, Output, State, MATCH
@app.callback(
    [Output({'type': 'additional-news', 'index': MATCH}, 'children'),
      Output({'type': 'load-more-button', 'index': MATCH}, 'children'),
      Output({'type': 'load-more-button', 'index': MATCH}, 'style')],
    [Input({'type': 'load-more-button', 'index': MATCH}, 'n_clicks')],
    [State({'type': 'load-more-button', 'index': MATCH}, 'id'),
      State({'type': 'additional-news', 'index': MATCH}, 'children')]
)
def load_more_articles(n_clicks, button_id, current_articles):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate

    symbol = button_id['index']
    ticker = yf.Ticker(symbol)
    news = ticker.news

    if not news or len(news) <= 4:
        return dash.no_update, dash.no_update, dash.no_update

    # If current_articles is None, initialize it to an empty list
    if current_articles is None:
        current_articles = []

    max_articles = (n_clicks + 1) * 4  # Increase the max articles by 4 each time the button is clicked
    additional_articles = []

    for article in news[4:max_articles]:
        related_tickers = ", ".join(article.get('relatedTickers', []))
        news_card = dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5(html.A(article['title'], href=article['link'], target="_blank")),
                    html.Img(src=article['thumbnail']['resolutions'][0]['url'], style={"width": "250px", "height": "auto"})
                    if 'thumbnail' in article else html.Div(),
                    html.P(f"Related Tickers: {related_tickers}" if related_tickers else "No related tickers available."),
                    html.Footer(
                        f"Published at: {datetime.utcfromtimestamp(article['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')}",
                        style={"margin-bottom": "0px", "padding-bottom": "0px"}
                    )
                ])
            ),
            xs=12, md=6,  # Full width on mobile, half width on desktop
            className="mb-2"
        )
        additional_articles.append(news_card)

    if max_articles >= len(news):
        # Hide the "Load More" button if all articles have been loaded
        return current_articles + additional_articles, "No more articles", {'display': 'none'}
    
    return current_articles + additional_articles, "Load More", dash.no_update

def fetch_analyst_recommendations(symbol):
    ticker = yf.Ticker(symbol)
    rec = ticker.recommendations
    if rec is not None and not rec.empty:
        return rec.tail(10)  # Fetch the latest 10 recommendations
    return pd.DataFrame()  # Return an empty DataFrame if no data

def generate_recommendations_heatmap(dataframe, plotly_theme):
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
        template= plotly_theme,
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
import dash_table

def format_number(value):
    """Format the number into thousands (K), millions (M), or billions (B)."""
    if pd.isnull(value):
        return "N/A"
    elif value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value <= -1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value <= -1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 100_000:
        return f"{value / 1_000:.1f}K"
    elif value <= -100_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:.0f}"

def create_financials_table(data):
    # Transpose the financials data
    data = data.T
    data.index = pd.to_datetime(data.index).year
    
    # Format numbers as thousands, millions, or billions
    data = data.applymap(format_number)

    # Transpose again to switch rows and columns, then reverse the rows
    data = data.T.reset_index()
    data.columns.name = None  # Remove the name of the index column
    data = data.iloc[::-1]  # Reverse the order of the rows
    
    # Ensure all column names are strings
    data.columns = data.columns.astype(str)
    
    # Limit to the latest 4 years
    data = data.iloc[:, :5]  # [:, :5] to include the 'index' column plus 4 years

    # Create Dash DataTable for displaying financial data
    financials_table = dash_table.DataTable(
        data=data.to_dict('records'),
        columns=[{"name": str(i), "id": str(i)} for i in data.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
        style_header={'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},  # Apply this style to odd rows
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
    )

    return dbc.Container([
        html.Hr(),
        financials_table
    ])

def create_company_info(info):
    """Generate a simple table of company info."""
    info_table = dbc.Table(
        [
            html.Tbody([
                html.Tr([html.Th("Company Name"), html.Td(info.get("longName", "N/A"))]),
                html.Tr([html.Th("Sector"), html.Td(info.get("sector", "N/A"))]),
                html.Tr([html.Th("Industry"), html.Td(info.get("industry", "N/A"))]),
                html.Tr([html.Th("Market Cap"), html.Td(format_number(info.get("marketCap", None)))]),
                html.Tr([html.Th("Revenue"), html.Td(format_number(info.get("totalRevenue", None)))]),
                html.Tr([html.Th("Gross Profits"), html.Td(format_number(info.get("grossProfits", None)))]),
                html.Tr([html.Th("EBITDA"), html.Td(format_number(info.get("ebitda", None)))]),
                html.Tr([html.Th("Net Income"), html.Td(format_number(info.get("netIncomeToCommon", None)))]),
                html.Tr([html.Th("Dividend Yield"), html.Td(f"{info.get('dividendYield', 'N/A'):.2%}" if info.get("dividendYield") else "N/A")]),
            ])
        ],
        bordered=True,
        striped=True,
        hover=True,
    )

    return dbc.Container([
        # html.H5("Company Information"),
        html.Hr(),
        info_table
    ])


@app.callback(
    [Output('financials-modal', 'is_open'),
     Output('financials-modal-title', 'children'),
     Output('financials-modal-body', 'children')],
    [Input({'type': 'stock-symbol', 'index': ALL}, 'n_clicks')],
    [State('individual-stocks-store', 'data'),
     State('financials-modal', 'is_open')]
)
def display_financials_modal(n_clicks, watchlist, is_open):
    ctx = dash.callback_context

    # Prevent the modal from opening if no click or all n_clicks are None
    if not ctx.triggered or not watchlist or not any(n_clicks):
        raise PreventUpdate

    # Get the ID of the triggered button
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'stock-symbol' not in triggered_id:
        raise PreventUpdate  # Ensure the modal only opens when a stock symbol is clicked

    # Extract the index from the triggered ID
    index = json.loads(triggered_id)['index']
    stock_symbol = watchlist[index]

    # Fetch financials data
    ticker = yf.Ticker(stock_symbol)
    financials = ticker.financials
    balance_sheet = ticker.balance_sheet
    cashflow = ticker.cashflow
    info = ticker.info

    if financials is not None and not financials.empty:
        income_statement_content = create_financials_table(financials)
        balance_sheet_content = create_financials_table(balance_sheet)
        cashflow_content = create_financials_table(cashflow)
        company_info_content = create_company_info(info)
        
        # Create tabs for the modal
        modal_content = dbc.Tabs([
            dbc.Tab(company_info_content, label="Company Info"),
            dbc.Tab(balance_sheet_content, label="Balance Sheet"),
            dbc.Tab(income_statement_content, label="Income Statement"),
            dbc.Tab(cashflow_content, label="Cash Flow"),
        ], active_tab="tab-0")  # Set the first tab as active by default
    else:
        modal_content = html.P("No financial data available for this stock.")

    return True, f"Financials for {stock_symbol}", modal_content


@app.callback(
    Output('financials-modal', 'is_open', allow_duplicate=True),
    [Input('close-financials-modal', 'n_clicks')],
    [State('financials-modal', 'is_open')],
    prevent_initial_call=True
)
def close_financials_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

def get_stock_performance(symbols):
    performance_data = {}
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        # Fetch historical data
        hist = ticker.history(period="1y")
        # Fetch basic stock info
        info = ticker.info
        
        # Fetch performance-related data
        performance_data[symbol] = {
            "latest_close": hist['Close'].iloc[-1] if not hist.empty else None,
            "one_year_return": (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100 if not hist.empty else None,
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
        }

    return performance_data

@app.callback(
    [Output("chatbot-modal", "is_open"),
     Output("conversation-store", "data", allow_duplicate=True),
     Output("chatbot-conversation", "children", allow_duplicate=True)],
    [Input("open-chatbot-button", "n_clicks"),
     Input("clear-button", "n_clicks")],
    [State("chatbot-modal", "is_open"),
     State('conversation-store', 'data'),
     State('login-username-store', 'data'),
     State('saved-watchlists-dropdown', 'value'),  # New: get the selected watchlist
     State('individual-stocks-store', 'data')],  # New: get stocks from the selected watchlist
    prevent_initial_call=True
)
def toggle_or_clear_chatbot(open_click, clear_click, is_open, conversation_history, username, selected_watchlist, watchlist_stocks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, conversation_history, dash.no_update

    if ctx.triggered[0]["prop_id"] in ["open-chatbot-button.n_clicks", "clear-button.n_clicks"]:
        if ctx.triggered[0]["prop_id"] == "open-chatbot-button.n_clicks" and is_open:
            # Close modal if it's already open
            return not is_open, conversation_history, dash.no_update

        watchlist_message = ""
        personalized_greeting = "Hello! My name is Financio, your financial advisor 🤖."
        
        if username:
            if selected_watchlist and watchlist_stocks:
                # Generate the stock performance summaries for the selected watchlist
                performance_data = get_stock_performance(watchlist_stocks)
                performance_summaries = [
                    f"{symbol}: Latest - ${data['latest_close']:.2f}" 
                    for symbol, data in performance_data.items()
                ]
                watchlist_message = f"Here are the stocks on your selected watchlist and their performance: {'; '.join(performance_summaries)}."
            else:
                watchlist_message = "You currently don't have a watchlist selected."

            # Personalize greeting
            personalized_greeting = f"Hello, {username}! My name is Financio, your financial advisor 🤖."
        else:
            watchlist_message = "You're not logged in, so I don't have access to your watchlist."

        # Initialize the conversation with a personalized message
        conversation_history = [{"role": "system", "content": "You are a helpful stock financial advisor."}]
        introduction_message = f"{personalized_greeting} How can I assist you today? {watchlist_message}"
        conversation_history.append({"role": "assistant", "content": introduction_message})

        conversation_display = [
            html.Div(
                [
                    html.Span("🤖", className="robot-avatar", style={"margin-right": "10px"}),
                    html.Span(f"{introduction_message}", className='chatbot-text'),
                ],
                className="chatbot-response fade-in"
            )
        ]
        return True, conversation_history, conversation_display

    return is_open, conversation_history, dash.no_update

@app.callback(
    [Output('conversation-store', 'data'),
     Output('chatbot-conversation', 'children'),
     Output('chatbot-input', 'value')],
    [Input('send-button', 'n_clicks')],
    [State('chatbot-input', 'value'),
     State('conversation-store', 'data'),
     State('login-username-store', 'data'),
     State('saved-watchlists-dropdown', 'value'),  # New: get the selected watchlist
     State('individual-stocks-store', 'data')],  # New: get stocks from the selected watchlist
    prevent_initial_call=True
)
def manage_chatbot_interaction(send_clicks, user_input, conversation_history, username, selected_watchlist, watchlist_stocks):
    from openai import OpenAI
    from dotenv import load_dotenv
    import os
    load_dotenv()
    open_api_key = os.getenv('OPEN_API_KEY')

    client = OpenAI(api_key=open_api_key)

    # Define the system message
    system_message = {"role": "system", "content": "You are a helpful stock financial advisor."}

    if conversation_history is None:
        conversation_history = [system_message]

    if send_clicks and send_clicks > 0 and user_input:
        # Append the user's message to the conversation history
        conversation_history.append({"role": "user", "content": user_input})

        # Respond with stock performance if requested and the user is logged in
        if "performance" in user_input.lower() and username:
            if selected_watchlist and watchlist_stocks:
                performance_data = get_stock_performance(watchlist_stocks)
                performance_summaries = [
                    f"{symbol}: Latest Close - ${data['latest_close']:.2f}" if data['latest_close'] is not None else f"{symbol}: Latest Close - N/A"
                    for symbol, data in performance_data.items()
                ]
                response = f"Here is the performance data for the stocks in your selected watchlist: {'; '.join(performance_summaries)}."
            else:
                response = "You don't have a watchlist selected to show performance data."
        else:
            # Use OpenAI to generate a response for other queries
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation_history,
            )
            response = completion.choices[0].message.content

        # Append the chatbot's response to the conversation history
        conversation_history.append({"role": "assistant", "content": response})

        # Update the conversation display
        conversation_display = []
        for message in conversation_history:
            if message["role"] == "user":
                conversation_display.append(html.P(f"YOU: {message['content']}", className='user'))
            elif message["role"] == "assistant":
                conversation_display.append(
                    html.Div(
                        [
                            html.Span("🤖", className="robot-avatar", style={"margin-right": "10px"}),
                            html.Span(f"{message['content']}", className='chatbot-text'),
                        ],
                        className="chatbot-response fade-in"
                    )
                )

        return conversation_history, conversation_display, ""  # Clear input box after response

    return conversation_history, dash.no_update, dash.no_update


@app.callback(
    Output('analyst-recommendations-content', 'children'),
    Input('individual-stocks-store', 'data')
)
def update_analyst_recommendations(stock_symbols):
    if not stock_symbols:
        return html.P("Please select stocks to view their analyst recommendations.")
    
    recommendations_content = []
    
    # Add the text to be displayed at the top
    recommendations_content.append(
        html.P([
            "For more information on how to interpret these ratings, please visit ",
            html.A("this article", href="https://finance.yahoo.com/news/buy-sell-hold-stock-analyst-180414724.html", target="_blank"),
            "."
        ], className='mt-2')
    )
    
    for symbol in stock_symbols:
        df = fetch_analyst_recommendations(symbol)
        if not df.empty:
            fig = generate_recommendations_heatmap(df)
            recommendations_content.append(html.H4(f"{symbol}", className='mt-3'))
            recommendations_content.append(dcc.Graph(figure=fig))
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
    [Input('generate-forecast-button', 'n_clicks'),
     Input('plotly-theme-store', 'data')],
    [State('forecast-stock-input', 'value'),
     State('forecast-horizon-input', 'value'),
     State('predefined-ranges', 'value')]  # Added predefined-ranges state
)
def generate_forecasts(n_clicks, plotly_theme, selected_stocks, horizon, predefined_range):
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
                    start_date = pd.to_datetime('2024-01-01')  # Default range if no match

                df_filtered = df[df['Date'] >= start_date]
                forecast_filtered = forecast[forecast['ds'] >= start_date]

                fig = go.Figure()
                fig.update_layout(template=plotly_theme)

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

                fig.update_layout(
                    title=f"Stock Price Forecast for {symbol}",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=600,
                    showlegend=False,
                    template=plotly_theme  # Ensure theme is applied
                )

                forecast_figures.append(fig)

            except Exception as e:
                fig = go.Figure()
                fig.update_layout(template=plotly_theme)
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
            template=plotly_theme,  # Apply theme to combined figure
            title=None,
            height=400 * len(forecast_figures),
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        return combined_fig, "", combined_fig

    # Ensure the default empty figure also uses the plotly theme
    empty_fig = go.Figure()
    empty_fig.update_layout(template=plotly_theme)

    return empty_fig, "", dash.no_update


@app.callback(
    [Output('filters-collapse', 'is_open'),
     Output('mobile-overlay', 'style')],
    [Input('toggle-filters-button', 'n_clicks')],
    [State('filters-collapse', 'is_open')]
)
def toggle_sidebar(n_clicks, is_open):
    if n_clicks:
        # Toggle the sidebar and the overlay
        new_is_open = not is_open
        overlay_style = {"display": "block"} if new_is_open else {"display": "none"}
        return new_is_open, overlay_style
    return is_open, {"display": "none"}

@app.callback(
    Output('tabs', 'active_tab'),
    [Input('footer-prices-tab', 'n_clicks'),
     Input('footer-news-tab', 'n_clicks'),
     Input('footer-compare-tab', 'n_clicks'),
     Input('footer-forecast-tab', 'n_clicks'),
     Input('footer-simulate-tab', 'n_clicks'),
     Input('footer-recommendations-tab', 'n_clicks')],
    [State('tabs', 'active_tab')]
)
def switch_tabs_footer_to_tabs(n_clicks_footer_prices, n_clicks_footer_news, n_clicks_footer_comparison, n_clicks_footer_forecast, 
                               n_clicks_footer_simulation, n_clicks_footer_recommendation, current_tab):
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_tab  # No tab change if nothing is clicked
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'footer-prices-tab':
        return 'prices-tab'
    elif triggered_id == 'footer-news-tab':
        return 'news-tab'
    elif triggered_id == 'footer-compare-tab':
        return 'compare-tab'
    elif triggered_id == 'footer-forecast-tab':
        return 'forecast-tab'
    elif triggered_id == 'footer-simulate-tab':
        return 'simulate-tab'
    elif triggered_id == 'footer-recommendations-tab':
        return 'recommendations-tab'
    
    return current_tab


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
    [Output('login-status', 'data', allow_duplicate=True),
     Output('login-username-store', 'data', allow_duplicate=True),
     Output('login-link', 'style', allow_duplicate=True),
     Output('logout-button', 'style', allow_duplicate=True),
     Output('profile-link', 'style', allow_duplicate=True),
     Output('theme-store', 'data', allow_duplicate=True),
     Output('plotly-theme-store', 'data', allow_duplicate=True),
     Output('page-content', 'children'),  # Redirect by changing the content
     Output('url', 'pathname')],  # Use this to redirect on login success
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def handle_login(login_clicks, username, password):
    if login_clicks:
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # Set session values and return dashboard content + redirection
            session['logged_in'] = True
            session['username'] = username

            user_theme = user.theme if user.theme else 'MATERIA'
            plotly_theme = themes.get(user_theme, {}).get('plotly', 'plotly_white')

            return (True, username, {"display": "none"}, {"display": "block"}, {"display": "block"},
                    themes[user_theme]['dbc'], plotly_theme, dashboard_layout, '/')  # Redirect to '/'
        else:
            return (False, None, {"display": "block"}, {"display": "none"}, {"display": "none"},
                    dbc.themes.MATERIA, 'plotly_white', login_layout, dash.no_update)
    
    # If no clicks yet, ensure to return 9 values:
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    [Output('profile-username', 'value'),
     Output('profile-email', 'value')],
    [Input('url', 'pathname')],
    [State('login-status', 'data'),
     State('login-username-store', 'data')]
)
def display_profile(pathname, login_status, username):
    if pathname == '/profile' and login_status and username:
        user = User.query.filter_by(username=username).first()
        if user:
            return user.username, user.email
    raise PreventUpdate

@app.callback(
    [Output('profile-username', 'disabled'),
     Output('profile-email', 'disabled'),
     Output('profile-current-password', 'disabled'),
     Output('profile-password', 'disabled'),
     Output('profile-confirm-password', 'disabled'),
     Output('edit-profile-button', 'style'),
     Output('save-profile-button', 'style'),
     Output('cancel-edit-button', 'style'),
     Output('profile-req-length', 'style'),
     Output('profile-req-uppercase', 'style'),
     Output('profile-req-lowercase', 'style'),
     Output('profile-req-digit', 'style'),
     Output('profile-req-special', 'style'),
     Output('profile-output', 'children')],
    [Input('edit-profile-button', 'n_clicks'),
     Input('save-profile-button', 'n_clicks'),
     Input('cancel-edit-button', 'n_clicks')],
    [State('profile-username', 'value'),
     State('profile-email', 'value'),
     State('profile-current-password', 'value'),
     State('profile-password', 'value'),
     State('profile-confirm-password', 'value'),
     State('login-username-store', 'data')]
)
def handle_profile_actions(edit_clicks, save_clicks, cancel_clicks, username, email, current_password, new_password, confirm_password, current_username):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'edit-profile-button':
        # Enable editing
        return (False, False, False, False, False,
                {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                "")

    elif triggered_id == 'save-profile-button':
        # Save logic
        if not username or not email:
            return (False, False, False, False, False,
                    {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    dbc.Alert("Username and Email are required.", color="danger"))
        
        # Verify the current password before allowing any password change
        user = User.query.filter_by(username=current_username).first()
        if user and not bcrypt.check_password_hash(user.password, current_password):
            return (False, False, False, False, False,
                    {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                    dbc.Alert("Current password is incorrect.", color="danger"))

        if new_password and new_password != confirm_password:
            return (False, False, False, False, False,
                    {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                    dbc.Alert("New passwords do not match.", color="danger"))

        # Validate the new password
        if new_password:
            password_error = validate_password(new_password)
            if password_error:
                return (False, False, False, False, False,
                        {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                        {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                        dbc.Alert(password_error, color="danger"))
        
        # Update user information
        if user:
            user.username = username
            user.email = email
            if new_password:
                user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            session['username'] = username
            return (True, True, True, True, True,
                    {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    dbc.Alert("Profile updated successfully!", color="success"))
        
    elif triggered_id == 'cancel-edit-button':
        # Cancel editing
        return (True, True, True, True, True,
                {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                "")

    raise PreventUpdate

@app.callback(
    [Output('profile-req-length', 'className'),
     Output('profile-req-uppercase', 'className'),
     Output('profile-req-lowercase', 'className'),
     Output('profile-req-digit', 'className'),
     Output('profile-req-special', 'className')],
    Input('profile-password', 'value')
)
def update_profile_password_requirements(password):
    return update_password_requirements(password)

@app.callback(
    [Output('login-status', 'data', allow_duplicate=True),
     Output('login-link', 'style', allow_duplicate=True),
     Output('logout-button', 'style', allow_duplicate=True),
     Output('profile-link', 'style', allow_duplicate=True),
     Output('individual-stocks-store', 'data', allow_duplicate=True),
     Output('theme-store', 'data', allow_duplicate=True),
     Output('plotly-theme-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],  # Redirect on logout
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def handle_logout(logout_clicks):
    if logout_clicks:
        session.pop('logged_in', None)
        session.pop('username', None)
        return False, {"display": "block"}, {"display": "none"}, {"display": "none"}, ['AAPL'], dbc.themes.MATERIA, 'plotly_white', '/login'  # Redirect to login
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('login-status', 'data'),
     Output('login-username-store', 'data'),
     Output('login-link', 'style'),
     Output('logout-button', 'style'),
     Output('profile-link', 'style')],  # Add output for profile link
    [Input('url', 'pathname')]
)
def check_session(pathname):
    logged_in = session.get('logged_in', False)
    username = session.get('username', None)

    if logged_in and username:
        return True, username, {"display": "none"}, {"display": "block"}, {"display": "block"}  # Show profile link
    else:
        return False, None, {"display": "block"}, {"display": "none"}, {"display": "none"}  # Hide profile link


@app.callback(
    Output('theme-dropdown', 'disabled'),
    Input('login-status', 'data')
)
def update_dropdown_status(login_status):
    return not login_status  # Disable dropdown if not logged in

@app.callback(
    Output('login-overlay', 'is_open'),
    [Input('theme-dropdown-wrapper', 'n_clicks'),
      Input('create-watchlist-button', 'n_clicks'),
      Input('delete-watchlist-button', 'n_clicks')],
    [State('login-status', 'data')]
)
def show_overlay_if_logged_out(theme_n_clicks, create_n_clicks, delete_n_clicks, login_status):
    # Ensure no NoneType errors
    theme_n_clicks = theme_n_clicks or 0
    create_n_clicks = create_n_clicks or 0
    delete_n_clicks = delete_n_clicks or 0

    # Show the overlay if the user is not logged in and clicks on either element
    if (theme_n_clicks > 0  or create_n_clicks > 0 or delete_n_clicks > 0) and not login_status:
        return True  # Show overlay
    return False  # Don't show overlay

@app.callback(
    [
     Output('create-watchlist-button', 'className'),
     Output('delete-watchlist-button', 'className')],
    Input('login-status', 'data')
)
def style_save_button(login_status):
    if not login_status:
        return 'grayed-out','grayed-out'  # Apply the grayed-out class when logged out
    return 'small-button','small-button'  # No class when logged in

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
                    html.Td(html.A(stock, href="#", id={'type': 'stock-symbol', 'index': i}, 
                                   style={"text-decoration": "none", "color": "blue"}), 
                            style={"verticalAlign": "middle"}),  # Vertically center the link
                    html.Td(f"{latest_close:.2f}", style={"verticalAlign": "middle"}),  # Vertically center the text
                    html.Td(f"{change_percent:.2f}%", style={"color": color, "verticalAlign": "middle"}),  # Vertically center the text
                    html.Td(dbc.Button("X", color="danger", size="sm", id={'type': 'remove-stock', 'index': i}),
                            style={"verticalAlign": "middle"})  # Vertically center the button
                ])
            )
        else:
            rows.append(
                html.Tr([
                    html.Td(stock, style={"verticalAlign": "middle"}),  # Vertically center the text
                    html.Td("N/A", style={"verticalAlign": "middle"}),  # Vertically center the text
                    html.Td("N/A", style={"verticalAlign": "middle"}),  # Vertically center the text
                    html.Td(dbc.Button("X", color="danger", size="sm", id={'type': 'remove-stock', 'index': i}),
                            style={"verticalAlign": "middle"})  # Vertically center the button
                ])
            )

    return dbc.Table(
        children=[
            html.Thead(html.Tr([html.Th("Symbol"), html.Th("Latest"), html.Th("Change (%)"), html.Th("")])),
            html.Tbody(rows)
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        size="sm",
        className="custom-table"  # Apply the custom class for the table
    )


@app.callback(
    [Output('new-watchlist-name', 'disabled',allow_duplicate=True),
      Output('saved-watchlists-dropdown', 'disabled',allow_duplicate=True),
      Output('create-watchlist-button', 'disabled',allow_duplicate=True),
      Output('delete-watchlist-button', 'disabled',allow_duplicate=True)],
    [Input('login-status', 'data')],
    prevent_initial_call='initial_duplicate'
)
def update_watchlist_management_layout(login_status):
    if login_status:
        return False, False, False, False  # Enable the components when logged in
    else:
        return True, True, False, False  # Keep them disabled when logged out


@app.callback(
    [Output('saved-watchlists-dropdown', 'options'),
     Output('saved-watchlists-dropdown', 'value'),
     Output('new-watchlist-name', 'value')],
    [Input('login-status', 'data'),
     Input('create-watchlist-button', 'n_clicks'),
     Input('delete-watchlist-button', 'n_clicks')],
    [State('new-watchlist-name', 'value'),
     State('individual-stocks-store', 'data'),
     State('saved-watchlists-dropdown', 'value'),
     State('theme-store', 'data'),  # Get the selected theme (name, not URL)
     State('login-username-store', 'data')]
)
def manage_watchlists(login_status, create_clicks, delete_clicks, new_watchlist_name, stocks, selected_watchlist_id, selected_theme, username):
    if not username or not login_status:
        return [], None, ''  # Clear the dropdown and inputs if not logged in
    
    user = User.query.filter_by(username=username).first()

    # Handle watchlist deletion
    if delete_clicks and selected_watchlist_id:
        watchlist = Watchlist.query.get(selected_watchlist_id)
        if watchlist and watchlist.user_id == user.id:
            db.session.delete(watchlist)
            db.session.commit()
            selected_watchlist_id = None  # Clear the selected watchlist

    # Handle watchlist creation or update
    elif create_clicks:
        if selected_watchlist_id:
            watchlist = Watchlist.query.get(selected_watchlist_id)
            if watchlist and watchlist.user_id == user.id:
                watchlist.stocks = json.dumps(stocks)  # Update the existing watchlist
                db.session.commit()
        elif new_watchlist_name:
            new_watchlist = Watchlist(user_id=user.id, name=new_watchlist_name, stocks=json.dumps(stocks))
            db.session.add(new_watchlist)
            db.session.commit()

        # Save the theme **name** to the user profile, not the URL
        if user:
            # Make sure only the theme name is saved
            for theme_name, theme_info in themes.items():
                if theme_info['dbc'] == selected_theme:
                    user.theme = theme_name  # Save the theme name like 'JOURNAL'
                    break
            db.session.commit()

    # Load and return updated watchlist options for the user
    watchlists = Watchlist.query.filter_by(user_id=user.id).all()
    watchlist_options = [{'label': w.name, 'value': w.id} for w in watchlists]

    return watchlist_options, selected_watchlist_id, ''


@app.callback(
    Output('individual-stocks-store', 'data'),
    [Input('url', 'pathname'),  # Triggers when the page is loaded/refreshed
     Input('saved-watchlists-dropdown', 'value'),
     Input('login-status', 'data')],
    [State('login-username-store', 'data')],
    prevent_initial_call=False  # Ensure this runs on page load
)
def load_watchlist(pathname, watchlist_id, login_status, username):
    # Check if the user is logged in and a username is provided
    if login_status and username:
        user = User.query.filter_by(username=username).first()
        
        if watchlist_id:
            # Load the selected watchlist from the dropdown
            watchlist = db.session.get(Watchlist, watchlist_id)
            if watchlist:
                return json.loads(watchlist.stocks)
        
        # If no specific watchlist is selected, load the default or most recent watchlist
        default_watchlist = Watchlist.query.filter_by(user_id=user.id, is_default=True).first()
        if default_watchlist:
            return json.loads(default_watchlist.stocks)

        # If no default, load the most recent watchlist
        recent_watchlist = Watchlist.query.filter_by(user_id=user.id).order_by(Watchlist.id.desc()).first()
        if recent_watchlist:
            return json.loads(recent_watchlist.stocks)
    
    # If not logged in or no watchlist is selected, return AAPL as the default stock
    return ['AAPL']

from dash import dcc, html, Input, Output, State, callback_context, ALL
from datetime import datetime, timedelta

@app.callback(
    [Output('individual-stocks-store', 'data', allow_duplicate=True),
     Output('watchlist-summary', 'children'),
     Output('stock-graph', 'figure'),
     Output('stock-graph', 'style'),
     Output('stock-news', 'children'),
     Output('indexed-comparison-graph', 'figure'),
     Output('indexed-comparison-stock-dropdown', 'options'),
     Output('indexed-comparison-stock-dropdown', 'value'),
     Output('prices-stock-dropdown', 'options'),
     Output('prices-stock-dropdown', 'value'),
     Output('individual-stock-input', 'value')],
    [Input('add-stock-button', 'n_clicks'),
     Input('reset-stocks-button', 'n_clicks'),
     Input('refresh-data-icon', 'n_clicks'),
     Input({'type': 'remove-stock', 'index': ALL}, 'n_clicks'),
     Input('chart-type', 'value'),
     Input('movag_input', 'value'),
     Input('benchmark-selection', 'value'),
     Input('predefined-ranges', 'value'),
     Input('indexed-comparison-stock-dropdown', 'value'),
     Input('prices-stock-dropdown', 'value'),
     Input('saved-watchlists-dropdown', 'value'),
     Input('plotly-theme-store', 'data')],  # Added the plotly theme store as an Input
    [State('individual-stock-input', 'value'),
     State('individual-stocks-store', 'data')],
    prevent_initial_call='initial_duplicate'
)
def update_watchlist_and_graphs(add_n_clicks, reset_n_clicks, refresh_n_clicks, remove_clicks, chart_type, movag_input, benchmark_selection, predefined_range, selected_comparison_stocks, selected_prices_stocks, selected_watchlist, plotly_theme, new_stock, individual_stocks):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    trigger = ctx.triggered[0]['prop_id']

    # Check if the watchlist dropdown triggered the update
    if 'saved-watchlists-dropdown' in trigger and selected_watchlist:
        # Load the selected watchlist from the database
        watchlist = db.session.get(Watchlist, selected_watchlist)
        if watchlist:
            individual_stocks = json.loads(watchlist.stocks)
            selected_prices_stocks = individual_stocks[:5]
            selected_comparison_stocks = individual_stocks[:5]

    # Handle other triggers (add stock, reset stock, remove stock, etc.)
    if 'add-stock-button' in trigger and new_stock:
        new_stock = new_stock.upper().strip()
        if new_stock and new_stock not in individual_stocks:
            individual_stocks.append(new_stock)
    elif 'reset-stocks-button' in trigger:
        individual_stocks = []
    elif 'refresh-data-icon' in trigger:
        pass
    elif 'remove-stock' in trigger:
        index_to_remove = json.loads(trigger.split('.')[0])['index']
        if 0 <= index_to_remove < len(individual_stocks):
            individual_stocks.pop(index_to_remove)

    if benchmark_selection in individual_stocks:
        individual_stocks.remove(benchmark_selection)

    options = [{'label': stock, 'value': stock} for stock in individual_stocks]

    # Update selected stocks for Prices and Indexed Comparison dropdowns
    if selected_comparison_stocks:
        selected_comparison_stocks = [stock for stock in selected_comparison_stocks if stock in individual_stocks]
    else:
        selected_comparison_stocks = individual_stocks[:5]

    if selected_prices_stocks:
        selected_prices_stocks = [stock for stock in selected_prices_stocks if stock in individual_stocks]
    else:
        selected_prices_stocks = individual_stocks[:5]

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
            options,
            selected_prices_stocks,
            ""
        )

    today = pd.to_datetime('today')

    if predefined_range == '5D_15m':
        start_date = today - timedelta(days=5)
        interval = '15m'
    elif predefined_range == '1D_15m':
        start_date = today - timedelta(hours=24)
        interval = '5m'
    elif predefined_range == 'YTD':
        start_date = datetime(today.year, 1, 1)
        interval = '1d'
    elif predefined_range == '1M':
        start_date = today - timedelta(days=30)
        interval = '1d'
    elif predefined_range == '3M':
        start_date = today - timedelta(days=3 * 30)
        interval = '1d'
    elif predefined_range == '12M':
        start_date = today - timedelta(days=365)
        interval = '1d'
    elif predefined_range == '24M':
        start_date = today - timedelta(days=730)
        interval = '1d'
    elif predefined_range == '5Y':
        start_date = today - timedelta(days=1825)
        interval = '1d'
    elif predefined_range == '10Y':
        start_date = today - timedelta(days=3650)
        interval = '1d'
    else:
        start_date = pd.to_datetime('2024-01-01')
        interval = '1d'

    end_date = today
    
    data = []
    for symbol in individual_stocks:
        try:
            df = yf.download(symbol, start=start_date, end=end_date, interval=interval)
    
            if predefined_range in ['1D_15m'] and df.empty:
                print(f"No intraday data found for {symbol} in the last 24 hours. Skipping.")
                continue

            df.reset_index(inplace=True)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            else:
                df['Datetime'] = pd.to_datetime(df['Datetime'])
                df.set_index('Datetime', inplace=True)

            df = df.tz_localize(None)
            df['Stock'] = symbol
            df['30D_MA'] = df['Close'].rolling(window=30, min_periods=1).mean()
            df['100D_MA'] = df['Close'].rolling(window=100, min_periods=1).mean()
            data.append(df)
        
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            continue
    
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
            options,
            selected_prices_stocks,
            ""
        )
    
    # df_all = pd.concat(data) if data else pd.DataFrame()
    
    if data:
        common_index = pd.date_range(start=start_date, end=end_date, freq=interval)
        data = [df.reindex(common_index, method='pad') for df in data]
        df_all = pd.concat(data)
    else:
        df_all = pd.DataFrame()

    
    indexed_data = {}
    for symbol in individual_stocks:
        if symbol in df_all['Stock'].unique():
            df_stock = df_all[df_all['Stock'] == symbol].copy()
            df_stock['Index'] = df_stock['Close'] / df_stock['Close'].iloc[0] * 100
            indexed_data[symbol] = df_stock[['Index']].rename(columns={"Index": symbol})
    
    if benchmark_selection != 'None':
        benchmark_data = yf.download(benchmark_selection, start=start_date, end=end_date, interval=interval)
        if not benchmark_data.empty:
            benchmark_data.reset_index(inplace=True)
            benchmark_data['Index'] = benchmark_data['Close'] / benchmark_data['Close'].iloc[0] * 100
    
    if indexed_data:
        df_indexed = pd.concat(indexed_data, axis=1)
        df_indexed.reset_index(inplace=True)
        df_indexed.columns = ['Date'] + [symbol for symbol in indexed_data.keys()]
        df_indexed['Date'] = pd.to_datetime(df_indexed['Date'], errors='coerce')
        
        available_stocks = [stock for stock in selected_comparison_stocks if stock in df_indexed.columns]
        if not available_stocks:
            return (
                individual_stocks,
                generate_watchlist_table(individual_stocks),
                px.line(title="Selected stocks are not available in the data.", template=plotly_theme),
                {'height': '400px'},
                html.Div("No data found for the selected comparison stocks."),
                px.line(title="Selected stocks are not available in the data.", template=plotly_theme),
                options,
                selected_comparison_stocks,
                options,
                selected_prices_stocks,
                ""
            )
    
        df_indexed_filtered = df_indexed[['Date'] + available_stocks]
    
        fig_indexed = px.line(df_indexed_filtered, x='Date', y=available_stocks, template=plotly_theme)
        fig_indexed.update_yaxes(matches=None, title_text=None)
        fig_indexed.update_xaxes(title_text=None)
        fig_indexed.update_layout(template=plotly_theme, legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            font=dict(size=10),
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
    
        if benchmark_selection != 'None':
            fig_indexed.add_scatter(x=benchmark_data['Date'], y=benchmark_data['Index'], mode='lines',
                                    name=benchmark_selection, line=dict(dash='dot'))
    
    else:
        fig_indexed = px.line(title="No data available.", template=plotly_theme)

    df_prices_filtered = df_all[df_all['Stock'].isin(selected_prices_stocks)]
    num_stocks = len(selected_prices_stocks)
    graph_height = 400 * num_stocks

    fig_stock = make_subplots(
        rows=num_stocks,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.05,
        subplot_titles=selected_prices_stocks,
        row_heights=[1] * num_stocks,
        specs=[[{"secondary_y": True}]] * num_stocks,
    )

    for i, symbol in enumerate(selected_prices_stocks):
        df_stock = df_prices_filtered[df_prices_filtered['Stock'] == symbol]

        if not df_stock.empty and len(df_stock) > 1:
            if chart_type == 'line':
                fig_stock.add_trace(go.Scatter(x=df_stock.index, y=df_stock['Close'], name=f'{symbol} Close',
                                                line=dict(color='blue')), row=i + 1, col=1)

                last_close = df_stock['Close'].iloc[-2]
                latest_close = df_stock['Close'].iloc[-1]
                change_percent = ((latest_close - last_close) / last_close) * 100

                fig_stock.add_trace(go.Scatter(
                    x=[df_stock.index[-1]],
                    y=[latest_close],
                    mode='markers',
                    marker=dict(color='red', size=10),
                    name=f'{symbol} Last Price'
                ), row=i + 1, col=1)

                latest_timestamp = df_stock.index[-1]
                fig_stock.add_annotation(
                    x=latest_timestamp,
                    y=latest_close,
                    text=f"{latest_close:.2f} ({change_percent:.2f}%)<br>{latest_timestamp.strftime('%Y-%m-%d')}",
                    showarrow=True,
                    arrowhead=None,
                    ax=20,
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

    news_content = fetch_news(individual_stocks)

    return (
        individual_stocks,
        generate_watchlist_table(individual_stocks),
        fig_stock,
        {'height': f'{graph_height}px', 'overflow': 'auto'},
        news_content,
        fig_indexed,
        options,
        selected_comparison_stocks,
        options,
        selected_prices_stocks,
        ""
    )


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
    [Output('page-content', 'children',allow_duplicate=True),
     Output('register-link', 'style'),
     Output('sticky-footer-container', 'style')],
    [Input('url', 'pathname'),
     Input('login-status', 'data')],
    prevent_initial_call=True
)
def display_page(pathname, login_status):
    pages_without_footer = ['/about', '/login', '/register', '/profile']
    footer_style = {"display": "block"} if pathname not in pages_without_footer else {"display": "none"}

    if pathname == '/about':
        return about_layout, {"display": "block"} if not login_status else {"display": "none"}, footer_style
    elif pathname == '/register':
        return register_layout, {"display": "block"} if not login_status else {"display": "none"}, footer_style
    elif pathname == '/login' and not login_status:
        return login_layout, {"display": "block"} if not login_status else {"display": "none"}, footer_style
    elif pathname == '/profile' and login_status:
        return profile_layout, {"display": "none"}, footer_style
    else:
        return dashboard_layout, {"display": "block"} if not login_status else {"display": "none"}, footer_style


@app.callback(
    [Output('tab-prices', 'className'),
     Output('tab-news', 'className'),
     Output('tab-comparison', 'className'),
     Output('tab-forecast', 'className'),
     Output('tab-simulation', 'className'),
     Output('tab-reccommendation', 'className')],
    [Input('tabs', 'value')]
)
def update_active_tab_class(current_tab):
    # Determine which tab is active and apply the "active" class accordingly
    return [
        "nav-link active" if current_tab == '📈 Prices' else "nav-link",
        "nav-link active" if current_tab == '📰 News' else "nav-link",
        "nav-link active" if current_tab == '⚖️ Compare' else "nav-link",
        "nav-link active" if current_tab == '🌡️ Forecast' else "nav-link",
        "nav-link active" if current_tab == '📊 Simulate' else "nav-link",
        "nav-link active" if current_tab == '❤️ Reccomendations' else "nav-link"
    ]



@app.callback(
    [Output('theme-store', 'data'),
     Output('plotly-theme-store', 'data')],
    [Input(f'theme-{theme}', 'n_clicks') for theme in themes.keys()],
    [State('login-status', 'data'),
     State('login-username-store', 'data')]
)
def update_theme(*args, login_status=None, username=None):
    ctx = dash.callback_context

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        theme = button_id.split('-')[1]
        print(f"Selected theme: {theme}")
        print(f"DBC Theme: {themes[theme]['dbc']}, Plotly Theme: {themes[theme]['plotly']}")
        return themes[theme]['dbc'], themes[theme]['plotly']

    if login_status and username:
        user = User.query.filter_by(username=username).first()
        if user and user.theme:
            print(f"User's saved theme: {user.theme}")
            return themes[user.theme]['dbc'], themes[user.theme]['plotly']

    print("Using default theme")
    return dbc.themes.MATERIA, 'plotly_white'


@app.callback(
    Output('theme-switch', 'href'),
    Input('theme-store', 'data')
)
def update_stylesheet(theme):
    return theme

@app.callback(
    Output('plotly-theme-store', 'data',allow_duplicate=True),
    [Input('theme-store', 'data')],
    prevent_initial_call=True
)
def update_plotly_theme(theme):
    if theme == dbc.themes.CYBORG or theme == dbc.themes.DARKLY:
        return 'plotly_dark'
    elif theme == dbc.themes.SOLAR:
        return 'plotly_dark'
    return 'plotly_white'


app.index_string = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-9BR02FMBX1"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
        
          gtag('config', 'G-9BR02FMBX1');
        </script>
        <!-- Google Tag Manager -->
        <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
        new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        })(window,document,'script','dataLayer','GTM-T6SPT9FD');</script>
        <!-- End Google Tag Manager -->
        {%metas%}
        <title>Stocks monitoring and recommendation made easy - MyStocks</title>
        <meta name="description" content="Track and forecast stock prices, visualize trends, get stock recommendations, and chat with an AI financial advisor. Save your watchlist today!">
        <meta name="keywords" content="stock, stocks, stock dashboard, finance, stock forecasting, stock news, stocks monitoring, stocks recommendations, finance, financial advisor">
        <meta name="author" content="myStocksportoflio">
        <meta property="og:title" content="Stocks monitoring and recommendation made easy - MyStocks" />
        <meta property="og:description" content="Stocks monitoring, recommendations, news and more" />
        <meta property="og:image" content="https://mystocksportfolio.io/assets/logo_with_transparent_background.png" />
        <meta property="og:url" content="https://mystocksportfolio.io/" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://mystocksportfolio.io/" />
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
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "WebSite",
          "url": "https://mystocksportfolio.io/",
          "name": "myStocksportoflio",
          "description": "Track and forecast stock prices, visualize trends, get stock recommendations, and chat with an AI financial advisor.",
          "publisher": {
            "@type": "Organization",
            "name": "MyStocks"
          }
        }
        </script>
        
    </head>
    <body>
        <!-- Google Tag Manager (noscript) -->
        <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-T6SPT9FD"
        height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        <!-- End Google Tag Manager (noscript) -->
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

