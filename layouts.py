import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd



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


def create_navbar(themes):
    return dbc.Navbar(
        dbc.Container(
            [
                # Row for the brand logo with left margin
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.NavbarBrand([
                                html.Img(src='/assets/logo_with_transparent_background.png', height='50px'),
                                "MySTOCKS", 
                            ], href="/", className="ms-3", style={"font-size": "16px"})  # Add margin on the left side of the logo
                        ),
                    ],
                    align="center",
                    className="g-0 flex-grow-1"
                ),
                
                # Fullscreen button (smaller size with size="sm")
                dbc.Row(
                    dbc.Col(
                        dbc.Button("⛶ 🖥️", id='fullscreen-button', color='secondary', size="sm", className="me-2 order-1"),  # Smaller fullscreen button
                        className="d-flex align-items-center"
                    ),
                    align="center",
                    className="g-0 flex-grow-1"
                ),
                
                # NavbarToggler and Collapse aligned to the right
                dbc.NavbarToggler(id="navbar-toggler", className="order-2 me-3"),  # Adjust toggler order and add right margin
                
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("📈 Dashboard", href="/", active="exact")),
                            dbc.NavItem(dbc.NavLink("ℹ️ Demo", href="/about", active="exact")),
                            dbc.NavItem(dbc.NavLink("👤 Profile", href="/profile", active="exact", id='profile-link', style={"display": "none"})),
                            dbc.NavItem(dbc.NavLink("📝 Register", href="/register", active="exact", id='register-link')),
                            dbc.NavItem(dbc.NavLink("🔐 Login", href="/login", active="exact", id='login-link', style={"display": "block"})),
                            # Group Logout button
                            html.Div(
                                [
                                    dbc.Button("Logout", id='logout-button', color='secondary', style={"display": "none"}, className="me-2"),
                                ],
                                className="d-flex align-items-center"
                            ),
                            # Theme selection dropdown
                            html.Div(
                                dbc.DropdownMenu(
                                    children=[dbc.DropdownMenuItem(theme, id=f'theme-{theme}') for theme in themes],
                                    nav=True,
                                    in_navbar=True,
                                    label="🎨 Select Theme",
                                    id='theme-dropdown',
                                ),
                                id='theme-dropdown-wrapper',
                                n_clicks=0,
                                className="d-flex align-items-center",
                            )
                        ],
                        className="ms-auto",  # Align nav items to the right
                        navbar=True
                    ),
                    id="navbar-collapse",
                    is_open=False,  # Initially collapsed on mobile
                    navbar=True,
                    className="order-3"  # Ensure the collapse stays on the far right
                ),
                
                # Separate dcc.Store for fullscreen trigger
                dcc.Store(id="trigger-fullscreen")
            ],
            fluid=True  # Ensure proper responsiveness
        ),
        color="primary",
        dark=True,
        className="sticky-top mb-4"
    )



def create_sticky_footer_mobile():
    return dbc.Nav(
        [
            dbc.NavItem(dbc.NavLink("📰 News", href="#news", id="footer-news-tab")),
            dbc.NavItem(dbc.NavLink("📈 Prices", href="#prices", id="footer-prices-tab")),
            dbc.NavItem(dbc.NavLink("🔥 Hot Stocks", href="#topshots", id="footer-topshots-tab")),
            dbc.NavItem(dbc.NavLink("⚖️ Compare", href="#comparison", id="footer-compare-tab")),
            dbc.NavItem(dbc.NavLink("🌡️ Forecast", href="#forecast", id="footer-forecast-tab")),
            dbc.NavItem(dbc.NavLink("📊 Simulate", href="#simulation", id="footer-simulate-tab")),
            dbc.NavItem(dbc.NavLink("❤️ Recommendations", href="#recommendations", id="footer-recommendations-tab")),
        ],
        pills=True,
        justified=True,
        className="footer-nav flex-nowrap overflow-auto",
        style={"white-space": "nowrap"}
    )


def create_modal_register():
    return html.Div([
        # Store to track if modal has been shown
        dcc.Store(id='modal-shown-store', data=False),
        
        # Interval to trigger modal after a certain time
        dcc.Interval(id='register-modal-timer', interval=30*1000, n_intervals=0),  # 30 seconds
        
        # Register modal with header, body, and footer
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Don't Miss Out!")),
                dbc.ModalBody("Register now for free to unlock all features: Save your personal watchlist(s), get analyst recommendations and more."),
                dbc.ModalFooter(
                    dbc.Button("Register", href="/register", color="primary", className="ms-auto", id="close-register-modal-button"),
                ),
            ],
            id="register-modal",
            is_open=False,  # Initially closed
            backdrop="static",  # Prevent closing by clicking outside
            keyboard=False  # Prevent closing with escape key
        )
    ])


def create_overlay():
    return dbc.Modal(
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


def create_floating_chatbot_button():
    return html.Div(
        dbc.Button("💬 ask me", id="open-chatbot-button", color="primary", className="chatbot-button"),
        style={
            "position": "fixed",
            "bottom": "100px",
            "right": "20px",
            "z-index": "1002",
        }
    )

def create_financials_modal():
    return dbc.Modal(
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


def create_chatbot_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("🤖 Financio")),
            dbc.ModalBody([
                html.Div(id='chatbot-conversation',
                         style={
                             'border': '1px solid #ccc',
                             'border-radius': '10px',
                             'padding': '10px',
                             'height': '400px',
                             'overflow-y': 'scroll',
                             'background-color': '#f8f9fa',
                             'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                         }),
                dcc.Textarea(id='chatbot-input',
                             placeholder='Ask your financial question...',
                             style={
                                 'width': '100%',
                                 'height': '100px',
                                 'border-radius': '10px',
                                 'border': '1px solid #ccc',
                                 'padding': '10px',
                                 'margin-top': '10px',
                                 'resize': 'none',
                                 'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                             }),
                dbc.Button("Send", id='send-button', color='primary', className='mt-2'),
                dbc.Button("Clear Conversation", id='clear-button', color='danger', className='mt-2 ms-2'),
            ])
        ],
        id="chatbot-modal",
        size="lg",
        is_open=False,
        className="bg-primary"  # Start closed
    )


def create_footer():
    return html.Footer(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H5("Direction", style={"display": "none"}),  # Hide the heading
                    html.Ul([
                        html.Li(html.A("About MyStocks", href="/about", className="footer-link")),
                        html.Li(html.A("Contact Us", href="mailto:mystocks.monitoring@gmail.com?subject=mystocks%20request", className="footer-link")),
                        html.Li(html.A("Dashboard", href="/dashboard", className="footer-link")),
                    ], className="list-unstyled")
                ], md=12, className="d-flex justify-content-center")  # Center the column
            ]),
            html.A(
                html.Img(src="/assets/X-Logo.png", alt="Share on X", style={"width": "30px", "height": "auto"}),
                href="https://twitter.com/share?url=https://mystocksportfolio.io&text=Check out MyStocks!",
                target="_blank",
                style={"margin-right": "10px"}
            ),
            html.A(
                html.Img(src="/assets/linkedin.png", alt="Share on LinkedIn", style={"width": "30px", "height": "30px"}),
                href="https://www.linkedin.com/sharing/share-offsite/?url=https://mystocksportfolio.io",
                target="_blank",
                style={"margin-right": "10px"}
            ),
            dbc.Row([
                dbc.Col([
                    html.P("© 2024 MyStocks. All rights reserved.", className="text-center")
                ], className="d-flex justify-content-center")
            ])
        ], fluid=True),
        className="footer"
    )


def create_watchlist_management_layout():
    return dbc.Container([
        html.Label("Saved Watchlists:", className="font-weight-bold", style={"margin-top": "10px"}),
        html.Div([
            dcc.Dropdown(
                id='saved-watchlists-dropdown',
                placeholder="Select a Watchlist",
                options=[],
                disabled=True,
                searchable=False,
                style={"margin-bottom": "10px"}
            )
        ]),
        dcc.Input(
            id='new-watchlist-name',
            placeholder="Enter Watchlist Name",
            className="form-control",
            disabled=True
        ),
        dbc.Button("💾 save", id='create-watchlist-button', color='primary', className='', disabled=False),
        dbc.Button("X delete", id='delete-watchlist-button', color='danger', className='', disabled=False)
    ])


def create_dashboard_layout(watchlist_management_layout):
    return dbc.Container([
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
                        "top": "90px",
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
                                dcc.Dropdown(
                                    id='stock-suggestions-input',
                                    options=[],
                                    placeholder="Enter Company or Symbol",
                                    className='custom-dropdown',
                                    multi=False,
                                    searchable=True,
                                    style={
                                        'border': '2px solid var(--bs-danger)',
                                        'border-radius': '5px',
                                        'padding': '0px',
                                    }
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
                                    id='predefined-ranges', searchable=False,
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
                                )
                            ], className='mb-3'),
                        ]),
                        watchlist_management_layout
                    ], className="sidebar-card"),
                    id="filters-collapse",
                    is_open=False  # Initially closed (for mobile use case)
                ),
            ], width=12, md=3, style={"margin-top": "10px", "buttom":"50px"}),

            # Main content area (Tabs for Prices, News, Comparison, etc.)
            dbc.Col([
                dbc.Tabs(
                    id="tabs",
                    active_tab="news-tab",
                    children=[
                        dbc.Tab(label='📰 News', tab_id="news-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    dcc.Dropdown(
                                        id='news-stock-dropdown',
                                        options=[],  
                                        value=[],  
                                        multi=True,
                                        placeholder="Select stocks to display",
                                        searchable=False
                                    ),
                                    dcc.Loading(id="loading-news", type="default", children=[
                                        html.Div(id='stock-news', className='news-container')
                                    ])
                                ])
                            )
                        ]),
                        dbc.Tab(label='📈 Prices', tab_id="prices-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    dcc.Dropdown(
                                        id='prices-stock-dropdown',
                                        options=[],  
                                        value=[],  
                                        multi=True,
                                        placeholder="Select stocks to display",
                                        searchable=False
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
                        dbc.Tab(label='🔥 Hot Stocks', tab_id="topshots-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.H3("The hottest stocks to invest in at the moment based on financial KPIs", style={"display": "none"}),  # for SEO
                                    html.P("Find the hottest stocks at the moment to consider investing in based on financial KPIs. This list is updated once a week. Currently the model looks at all SP500 companies and ranks them accordingly."),  # for SEO
                                    dcc.Dropdown(
                                        id='risk-tolerance-dropdown',
                                        options=[
                                            {'label': 'Low Risk', 'value': 'low'},
                                            {'label': 'Medium Risk', 'value': 'medium'},
                                            {'label': 'High Risk', 'value': 'high'},
                                        ],
                                        value='medium',  # Default to medium risk
                                        placeholder="Select Risk Tolerance",
                                        clearable=False
                                    ),
                                    dcc.Loading(
                                        id="loading-top-stocks",
                                        children=[html.Div(id='top-stocks-table')],
                                        type="default"
                                    ),
                        
                                    html.Div(id='topshots-blur-overlay', style={
                                        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
                                        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                        'backdrop-filter': 'blur(5px)'
                                    }, children=[
                                        html.Div(
                                            className="bg-primary",  # Add Bootstrap class for background color
                                            children=[
                                                # Call to action (Sign-up prompt) moved to the top
                                                html.P("Please ", style={'display': 'inline'}),
                                                html.A("log in", href="/login", style={'display': 'inline', 'color': 'blue', 'text-decoration': 'underline'}),
                                                html.P(" or ", style={'display': 'inline'}),
                                                html.A("sign up", href="/register", style={'display': 'inline', 'color': 'blue', 'text-decoration': 'underline'}),
                                                html.P(" to view this content.", style={'display': 'inline', 'margin-bottom': '20px'}),
                        
                                                # List of benefits with checkmarks
                                                html.P("By signing up, you’ll unlock:", style={'text-align': 'center', 'font-size': '18px', 'font-weight': 'bold', 'margin-top': '20px'}),
                                                html.Ul([
                                                    html.Li("🔥 top-performing stocks based on financial KPIs", style={'font-size': '16px', 'text-align': 'left'}),
                                                    html.Li("📈 Weekly updates on the hottest stocks", style={'font-size': '16px', 'text-align': 'left'}),
                                                    html.Li("💼 Recommendations based on your risk profile", style={'font-size': '16px', 'text-align': 'left'}),
                                                ], style={'list-style-type': '"✔️ "', 'margin-top': '20px'}),
                                            ], style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'margin-top': '-350px', 'color': 'white', 'padding': '30px'}
                                        )
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
                                        value=[],  
                                        multi=True,
                                        searchable=False
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
                                    html.H3("Forecast stocks prices", style={"display": "none"}),  # for SEO
                                    html.Div([
                                        html.Label("Select up to 3 Stocks:", className="font-weight-bold"),
                                        dcc.Dropdown(
                                            id='forecast-stock-input',
                                            options=[],  
                                            value=[],  
                                            multi=True,
                                            className='form-control',
                                            searchable=False
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
                                        These predictions should be considered with caution and should not be used as financial advice.
                                    ''', style={'font-size': '14px', 'margin-top': '20px', 'color': 'gray'}),
                                    dcc.Loading(
                                        id="loading-forecast",
                                        type="default",
                                        children=[dcc.Graph(id='forecast-graph', style={'height': '500px'})]
                                    ),
                                    html.Div(id='forecast-blur-overlay', style={
                                        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
                                        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                        'backdrop-filter': 'blur(5px)'
                                    },  children=[
                                        html.Div(
                                            className="bg-primary",  # Add Bootstrap class for background color
                                            children=[
                                                # Call to action (Sign-up prompt) moved to the top
                                                html.P("Please ", style={'display': 'inline'}),
                                                html.A("log in", href="/login", style={'display': 'inline', 'color': 'blue', 'text-decoration': 'underline'}),
                                                html.P(" or ", style={'display': 'inline'}),
                                                html.A("sign up", href="/register", style={'display': 'inline', 'color': 'blue', 'text-decoration': 'underline'}),
                                                html.P(" to view this content.", style={'display': 'inline', 'margin-bottom': '20px'}),
                        
                                                # List of benefits with checkmarks
                                                html.P("By signing up, you’ll unlock:", style={'text-align': 'center', 'font-size': '18px', 'font-weight': 'bold', 'margin-top': '20px'}),
                                                html.Ul([
                                                    html.Li("🌡️ time series forecast", style={'font-size': '16px', 'text-align': 'left'}),
                                                    html.Li("📈 Perform up to 3 forecasts simultaneously", style={'font-size': '16px', 'text-align': 'left'}),
                                                    html.Li("⏱️ Choose your individual forecast horizon", style={'font-size': '16px', 'text-align': 'left'}),
                                                ], style={'list-style-type': '"✔️ "', 'margin-top': '20px'}),
                                            ], style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'margin-top': '-350px', 'color': 'white', 'padding': '30px'}
                                        )
                                    ])
                                ])
                                   
                            )
                        ]),
                        dbc.Tab(label='❤️ Recommendations', tab_id='recommendations-tab', children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.H3("Get analyst stock recommendations", style={"display": "none"}),  # for SEO
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
                                        html.Div(
                                            className="bg-primary",  # Add Bootstrap class for background color
                                            children=[
                                                # Call to action (Sign-up prompt) moved to the top
                                                html.P("Please ", style={'display': 'inline'}),
                                                html.A("log in", href="/login", style={'display': 'inline', 'color': 'blue', 'text-decoration': 'underline'}),
                                                html.P(" or ", style={'display': 'inline'}),
                                                html.A("sign up", href="/register", style={'display': 'inline', 'color': 'blue', 'text-decoration': 'underline'}),
                                                html.P(" to view this content.", style={'display': 'inline', 'margin-bottom': '20px'}),
                        
                                                # List of benefits with checkmarks
                                                html.P("By signing up, you’ll unlock:", style={'text-align': 'center', 'font-size': '18px', 'font-weight': 'bold', 'margin-top': '20px'}),
                                                html.Ul([
                                                    html.Li("💸 sell, hold and buy analyst recommendations ", style={'font-size': '16px', 'text-align': 'left'}),
                                                    html.Li("📈 historical change of recommendations ", style={'font-size': '16px', 'text-align': 'left'}),
                                                    html.Li("🔎 get recommendations for your watchlist", style={'font-size': '16px', 'text-align': 'left'}),
                                                ], style={'list-style-type': '"✔️ "', 'margin-top': '20px'}),
                                            ], style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'margin-top': '-350px', 'color': 'white', 'padding': '30px'}
                                        )
                                    ])
                                ])
                            )
                        ]),
                        dbc.Tab(label='📊 Simulate', tab_id="simulate-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.H3("Simulate stock profits and losses over historical time period", style={"display": "none"}),  # for SEO
                                    html.Label("Stock Symbol:", className="font-weight-bold"),
                                    dcc.Dropdown(
                                        id='simulation-stock-input',
                                        options=[],  
                                        value=[],  
                                        className='form-control',
                                        searchable=False
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
                        ])

                    ], className="desktop-tabs bg-secondary"
                )
            ], width=12, md=9, xs=12)
        ], className='mb-4'),

        # Welcome section
        dbc.Row([
            dbc.Col([
                html.H3("Welcome to Your Stock Monitoring Dashboard. Save your watchlists, monitoring stocks made easy", className="text-center mb-4", style={"display": "none"}),
                html.P([
                    "Track and analyze your favorite stocks with real-time data, forecasts, and personalized recommendations. ",
                    html.A("Learn more about the features.", href="/about", className="text-primary"),
                    html.Br(),  # Line break
                    " Want to save your personal Watchlist or get access to forecasts and analyst recommendations?",
                    html.A(" Register for free.", href="/register", className="text-primary"),
                ], className="text-center"),
            ], width=12)
        ], className="mb-4")
    ], fluid=True)



def create_profile_layout():
    return dbc.Container([
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

                        # Password requirement list
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
             

def create_register_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Registration form fields
                        html.H1("📝 Register", className="text-center mt-4"),
                        dcc.Input(id='username', type='text', placeholder='Username', className='form-control mb-3'),
                        dcc.Input(id='email', type='email', placeholder='Email', className='form-control mb-3'),
                        dcc.Input(id='password', type='password', placeholder='Password', className='form-control mb-3'),
                        
                        # Password requirements
                        html.Ul([
                            html.Li("At least 8 characters", id='req-length', className='text-muted'),
                            html.Li("At least one uppercase letter", id='req-uppercase', className='text-muted'),
                            html.Li("At least one lowercase letter", id='req-lowercase', className='text-muted'),
                            html.Li("At least one digit", id='req-digit', className='text-muted'),
                            html.Li("At least one special character (!@#$%^&*(),.?\":{}|<>)_", id='req-special', className='text-muted')
                        ], className='mb-3'),

                        # Confirm password
                        dcc.Input(id='confirm_password', type='password', placeholder='Confirm Password', className='form-control mb-3'),

                        # Register button
                        dbc.Button("Register", id='register-button', color='primary', className='mt-2 w-100'),
                        html.Div(id='register-output', className='mt-3'),
                    ])
                ])
            ], width=12, md=6, className="mx-auto")
        ]),
        dbc.Row([
            dbc.Col([
                # Login link
                html.H3("Login here", className="text-center mt-5 mb-4"),
                html.P([
                    "Successfully registered? ",
                    html.A("Login here", href="/login", className="text-primary")
                ], className="text-center"),

                # Why Register section
                html.H3("Why Register?", className="text-center mt-5 mb-4"),
                html.P([
                    "Registering allows you to save your stock watchlist, access personalized recommendations, and more. ",
                    html.A("Learn more on the About page.", href="/about", className="text-primary")
                ], className="text-center")
            ], width=12, md=6, className="mx-auto")
        ])
    ], fluid=True)


def create_login_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        # Login form fields
                        html.H1("🔐 Login", className="text-center"),
                        dcc.Input(id='login-username', type='text', placeholder='Username', className='form-control mb-3'),
                        dcc.Input(id='login-password', type='password', placeholder='Password', className='form-control mb-3'),
                        
                        # Login button
                        dbc.Button("Login", id='login-button', color='primary', className='mt-2 w-100'),
                        html.Div(id='login-output', className='mt-3'),

                        # Register link
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
                # Welcome section
                html.H3("Welcome to MyStocks Dashboard", className="text-center mt-5 mb-4"),
                html.P([
                    "Learn more about the application on the ",
                    html.A("About page.", href="/about", className="text-primary")
                ], className="text-center")
            ], width=12, md=6, className="mx-auto")
        ])
    ], fluid=True)


 
def create_carousel():
    return dbc.Carousel(
        items=[
            {
                "key": "1",
                "src": "/assets/gif1.gif",
                "alt": "Demo 1",
                "header": "Analyse and compare Stocks",
                "caption": "Financial indicators, custom time windows, and more."
            },
            {
                "key": "2",
                "src": "/assets/gif4.gif",
                "alt": "Demo 2",
                "header": "Save your Watchlist(s)",
                "caption": "Create your Account, save your Watchlist(s) and your custom Theme."
            },
            {
                "key": "3",
                "src": "/assets/gif2.gif",
                "alt": "Demo 3",
                "header": "Get latest Stock News",
                "caption": "Get tailored News Updates."
            },
            {
                "key": "4",
                "src": "/assets/gif3.gif",
                "alt": "Demo 4",
                "header": "Stock Forecasts and Recommendations",
                "caption": "Visualize forecasts and access analyst recommendations."
            },
            {
                "key": "5",
                "src": "/assets/gif5.gif",
                "alt": "Demo 5",
                "header": "Gen AI powered Chatbot",
                "caption": "Chat with your financial advisor bot powered by Chat GPT-3.5 Turbo."
            }
        ],
        controls=True,
        indicators=True,
        interval=20000,  # Time in ms for each slide
        ride="carousel",
        className="custom-carousel",
        id="custom-carousel"
    )
    

def create_about_layout(create_carousel):
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.Div([
                # Hidden H1 for SEO
                html.H1("MyStock Dashboard Demo", className="text-center mt-4", style={"display": "none"}),

                # Section: Why Choose MyStocks?
                html.Div([
                    html.H2("Why Choose MyStocks?", className="text-center mt-5 mb-3", style={"color": "black"}),
                    html.P("Comprehensive Data: Access to a wide range of financial data and tools for better decision-making. "
                           "User-Friendly Interface: Simple and intuitive design, making it easy for users at all levels to navigate. "
                           "Advanced Analytics: Leverage sophisticated forecasting and simulation tools to gain a competitive edge. "
                           "Real-Time Updates: Stay informed with up-to-date news and market data.", className="lead text-center"),
                ], style={"padding": "20px", "background-color": "#f8f9fa", "border-radius": "10px"}),

                # Carousel
                html.Div(create_carousel, className="custom-carousel"),

                # Section: Key Features
                html.Div([
                    html.H3("Key Features", className="text-center mt-5 mb-3", style={"color": "black"}),
                    html.P("This application provides a comprehensive platform for tracking stock market performance and related news. "
                           "Here are some of the key features:", className="text-center", style={"display": "none"}),

                    # Key features list
                    html.Ul([
                        html.Li("Historical Stock Price Tracking: Compare stock prices over historical periods. Perform indexed comparisons against major indices."),
                        html.Li("Stock Market News: Stay updated with the latest news for your selected stocks from reliable sources."),
                        html.Li("Profit/Loss Simulation: Simulate potential profit and loss scenarios for stocks in your watchlist."),
                        html.Li("Analyst Recommendations: Access buy, sell, and hold ratings from industry experts."),
                        html.Li("Time Series Forecasting: Predict future stock prices using advanced forecasting models."),
                        html.Li("Personalized Watchlist(s): Register and save your stock watchlist(s) to monitor your favorite stocks."),
                        html.Li("Stock Performance Comparison: Compare stock performance vs. NASDAQ100, S&P 500, or SMI."),
                        html.Li("Intelligent Financial Chatbot: Get instant answers to your stock-related queries."),
                        html.Li("Select and save your custom Theme"),
                    ], className="checked-list"),
                ], style={"padding": "20px", "background-color": "#ffffff", "border-radius": "10px", "box-shadow": "0px 2px 5px rgba(0,0,0,0.1)"}),

                # Call to action
                html.P([
                    "Don't have an account yet? ",
                    html.A("Register here", href="/register", className="text-center", style={"color": "blue", "text-decoration": "underline"}),
                    " to access more features!"
                ], style={
                    "font-size": "24px",  # Increase text size
                    "font-weight": "bold",  # Make it bold
                    "text-align": "center",  # Center the text
                    "margin": "20px 0"  # Add some margin around the paragraph
                })
            ], className="mx-auto", style={"max-width": "800px"}))
        ])
    ], fluid=True)

watchlist_management_layout = create_watchlist_management_layout()
dashboard_layout = create_dashboard_layout(watchlist_management_layout)
login_layout = create_login_layout()
register_layout = create_register_layout()
carousel_layout = create_carousel()
about_layout = create_about_layout(carousel_layout)
profile_layout = create_profile_layout()
                
                    
