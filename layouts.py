import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
# from auth_callbacks import show_overlay_if_logged_out
import utils as ut



themes = {
    'Lightmode': {'dbc': dbc.themes.SPACELAB, 'plotly': 'simple_white'},
    'Darkmode': {'dbc': dbc.themes.DARKLY, 'plotly': 'plotly_dark'}
}


def create_navbar(themes):
    return dbc.Navbar(
        dbc.Container(
            [
                # Row for the brand logo with left margin
                dbc.Row(
                    dbc.Col(
                        dbc.NavbarBrand(
                            [
                                html.Img(src='/assets/logo_with_transparent_background.png', height='42px', width='45px', alt="WacthMyStocks Logo"),  # Logo visible on all devices
                                html.Span("WatchMyStocks", className="ms-2 desktop-only", style={"font-size": "16px"})  # Text only on desktop
                            ],
                            href="/", 
                            className="d-flex align-items-center"  # Ensures logo and text are aligned in a single line
                        )
                    ),
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
                dbc.NavbarToggler(id="navbar-toggler", className="order-2 me-3 toggler-icon"),  # Adjust toggler order and add right margin
                
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("📈 Dashboard", href="/", active="exact")),
                            # dbc.NavItem(dbc.NavLink("📈 Dashboard", href="/dashboard#prices", active="exact")),

                            # About Dropdown with Demo, FAQs, and Blog
                            dbc.DropdownMenu(
                                label="ℹ️ About",  # Dropdown label
                                nav=True,
                                children=[
                                    dbc.DropdownMenuItem("Demo", href="/demo"),
                                    dbc.DropdownMenuItem("FAQs", href="/faqs"),
                                    dbc.DropdownMenuItem("Blog", href="/blog")  # New Blog item
                                ],
                            ),
                            
                            dbc.NavItem(dbc.NavLink("👤 Profile", href="/profile", active="exact", id='profile-link', style={"display": "none"})),
                            dbc.NavItem(dbc.NavLink("📝 Sign up", href="/register", active="exact", id='register-link')),
                            dbc.NavItem(dbc.NavLink("🔐 Login", href="/login", active="exact", id='login-link', style={"display": "block"})),
                            
                            # Theme selection dropdown
                            html.Div(
                                dbc.DropdownMenu(
                                    children=[dbc.DropdownMenuItem(theme, id=f'theme-{theme}') for theme in themes],
                                    nav=True,
                                    in_navbar=True,
                                    label="🎨 Select Theme",
                                    id='theme-dropdown',
                                    disabled=False
                                ),
                                id='theme-dropdown-wrapper',
                                n_clicks=0,
                                className="d-flex align-items-center",
                            ),
                            
                            # Logout button
                            html.Div(
                                [
                                    dbc.Button("Logout", id='logout-button', color='secondary', style={"display": "none"}, className="me-2"),
                                ],
                                className="d-flex align-items-center"
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


import dash_bootstrap_components as dbc

# Fancy FAQ layout with hover effects, icons, and gradient styling
faq_layout = html.Div(
    [
        html.H1("Frequently Asked Questions", className="text-center my-4", style={"color": "#007bff"}),  # Modern Heading
        
        # Question 1
        html.Div([
            dbc.Button([
                html.Span("❓ ", style={"margin-right": "10px"}),  # Icon
                "What is WatchMyStocks?"
            ], id="faq-q1", color="light", className="mb-3 p-3 text-start", style={"width": "100%", "border": "none", "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "background": "linear-gradient(90deg, #007bff 0%, #00c2ff 100%)", "color": "white", "font-size": "18px"}),
            dbc.Collapse(
                dbc.Card(dbc.CardBody("WatchMyStocks is a stock monitoring and recommendation platform that helps users track their investments and receive data-driven stock suggestions. Moreover, as registered users can save their watchlist(s) and get dedicated news based on the stocks in the watchlist.")),
                id="collapse-q1",
                is_open=False
            )
        ]),

        # Question 2
        html.Div([
            dbc.Button([
                html.Span("📋 ", style={"margin-right": "10px"}),  # Icon
                "How can I create a watchlist?"
            ], id="faq-q2", color="light", className="mb-3 p-3 text-start", style={"width": "100%", "border": "none", "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "background": "linear-gradient(90deg, #007bff 0%, #00c2ff 100%)", "color": "white", "font-size": "18px"}),
            dbc.Collapse(
                dbc.Card(dbc.CardBody(
                    dcc.Markdown([
                        "To create a watchlist, sign up for a free or premium account, go to the dashboard, then move to Stock Selection, add your stocks, enter a Watchlist name and save it. ",
                        "[Sign up now](https://mystocksportfolio.io/register)"
                    ])
                )),
                id="collapse-q2",
                is_open=False
            )
        ]),

        # Question 3
        html.Div([
            dbc.Button([
                html.Span("💡 ", style={"margin-right": "10px"}),  # Icon
                "What features are included in the premium plan?"
            ], id="faq-q3", color="light", className="mb-3 p-3 text-start", style={"width": "100%", "border": "none", "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "background": "linear-gradient(90deg, #007bff 0%, #00c2ff 100%)", "color": "white", "font-size": "18px"}),
            dbc.Collapse(
                dbc.Card(dbc.CardBody("The premium plan offers advanced stock forecasting capabilities, along with a daily updated 'Hot Stocks' section. In this section, you'll discover the most promising investment opportunities, tailored to your risk tolerance. The data-driven stock selection is based on a comprehensive analysis of key performance indicators (KPIs) and market trends, providing insights into stocks with the greatest potential for growth.")),
                id="collapse-q3",
                is_open=False
            )
        ]),

        # Question 4
        html.Div([
            dbc.Button([
                html.Span("❌ ", style={"margin-right": "10px"}),  # Icon
                "How can I cancel my subscription?"
            ], id="faq-q4", color="light", className="mb-3 p-3 text-start", style={"width": "100%", "border": "none", "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "background": "linear-gradient(90deg, #007bff 0%, #00c2ff 100%)", "color": "white", "font-size": "18px"}),
            dbc.Collapse(
                dbc.Card(dbc.CardBody("To cancel your subscription, navigate to the 'Profile' page, and you will find the option to cancel your premium plan.")),
                id="collapse-q4",
                is_open=False
            )
        ]),

        # Question 5
        html.Div([
            dbc.Button([
                html.Span("📱 ", style={"margin-right": "10px"}),  # Icon
                "Can I use WatchMyStocks on mobile?"
            ], id="faq-q5", color="light", className="mb-3 p-3 text-start", style={"width": "100%", "border": "none", "box-shadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "background": "linear-gradient(90deg, #007bff 0%, #00c2ff 100%)", "color": "white", "font-size": "18px"}),
            dbc.Collapse(
                dbc.Card(dbc.CardBody("Yes, WatchMyStocks is mobile-friendly and can be accessed on any mobile browser.")),
                id="collapse-q5",
                is_open=False
            )
        ]),
    ],
    style={"max-width": "800px", "margin": "0 auto", "padding": "20px"}
)


blog_layout = dbc.Container(
    [
        dbc.Row([

            # Mobile TOC toggle button on top
            html.Div(
                dbc.Button("Table of Contents", id="toc-toggle", color="primary", className="d-lg-none mt-4 mb-2"),
                className="text-center"
            ),
            dbc.Collapse(
                html.Div(
                    html.Ul([
                        html.Li(html.A("The Power of Compounding in Long-Term Investments", href="/blog/article-compounding")),
                        html.Li(html.A("Diversification: The Key to Reducing Investment Risk", href="/blog/article-diversification")),
                        # Add more articles here
                    ], className="toc-list", style={
                        "list-style-type": "none", "padding-left": "0", "text-align": "left",
                        "font-size": "16px", "color": "#007bff"
                    }),
                    className="bg-light p-3",
                    style={"max-width": "300px", "border-radius": "5px", "margin": "0 auto"}
                ),
                id="toc-collapse",
                is_open=False  # Initially collapsed on mobile
            ),

            # Table of Contents on the Left (Visible only on larger screens)
            dbc.Col(
                html.Div(
                    [
                        html.H2("Table of Contents", className="text-center my-4"),
                        html.Ul([
                            html.Li(html.A("The Power of Compounding in Long-Term Investments", href="/blog/article-compounding")),
                            html.Li(html.A("Diversification: The Key to Reducing Investment Risk", href="/blog/article-diversification")),
                            # Add more articles here
                        ], className="toc-list", style={
                            "list-style-type": "none", "padding-left": "0", "text-align": "left",
                            "font-size": "16px", "color": "#007bff"
                        })
                    ],
                    className="table-of-contents",
                    style={"position": "sticky", "top": "20px"}  # Sticky TOC that stays in view
                ),
                width=3,  # Left column for TOC takes 3/12th of the width
                className="d-none d-lg-block",  # Show only on large screens
                style={"border-right": "1px solid #e0e0e0", "padding-right": "20px"}  # Optional divider
            ),
            
            # Blog content centered, max width 900px
            dbc.Col(
                html.Div(
                    [
                        # First Blog Article
                        ut.create_blog_post(
                            title="The Power of Compounding in Long-Term Investments",
                            date="October 01, 2024",
                            author="WatchMyStocks",
                            image_src="/assets/compounding.png",
                            content_file="compounding_blog_content.md",
                            cta_text="Sign up for free",
                            cta_href="/register-free",
                            article_id="article-compounding"
                        ),

                        # Second Blog Article
                        ut.create_blog_post(
                            title="Diversification: The Key to Reducing Investment Risk",
                            date="July 15, 2024",
                            author="WatchMyStocks",
                            image_src="/assets/diversification.png",
                            content_file="diversification_blog_content.md",
                            cta_text="Sign up for free",
                            cta_href="/register-free",
                            article_id="article-diversification"
                        ),
                    
                        # Add more articles as needed
                    ],
                    style={
                        "max-width": "900px",  # Limit the blog content width
                        "margin": "0 auto"  # Center the content
                    }
                ),
                width=12, lg=9  # Full width for mobile, 9/12th for larger screens
            )
        ]),
        
    ],
    fluid=True,
    className="blog-layout"
)


def create_sticky_footer_mobile():
    return html.Div(
        [
            # Footer navigation bar
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("🌡️ Forecast", href="#forecast", id="footer-forecast-tab")),
                    dbc.NavItem(dbc.NavLink("📈 Prices", href="#prices", id="footer-prices-tab")),
                    dbc.NavItem(dbc.NavLink("🔥 Hot Stocks", href="#topshots", id="footer-topshots-tab")),
                    dbc.NavItem(dbc.NavLink("📰 News", href="#news", id="footer-news-tab")),
                    dbc.NavItem(dbc.NavLink("⚖️ Compare", href="#comparison", id="footer-compare-tab")),
                    dbc.NavItem(dbc.NavLink("❤️ Recommendations", href="#recommendations", id="footer-recommendations-tab")),
                    dbc.NavItem(dbc.NavLink("📊 Simulate", href="#simulation", id="footer-simulate-tab")),
                ],
                pills=True,
                justified=True,
                className="footer-nav flex-nowrap overflow-auto",
                style={"white-space": "nowrap"},
            ),
            
            # Right gradient for visual indication
            html.Div(
                className="footer-gradient-right"
            )
        ],
        className="footer-nav-wrapper"
    )


def create_modal_register():
    return html.Div([
        # Store to track if modal has been shown
        dcc.Store(id='modal-shown-store', data=False),
        
        # Interval to trigger modal after a certain time
        dcc.Interval(id='register-modal-timer', interval=120*1000, n_intervals=0),  # 7 seconds
        
        # Register modal with header, body, and footer
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("🚀 Unlock Your Full Potential!"),
                    className="bg-primary text-white text-center"
                ),
                dbc.ModalBody([
                    html.Div(
                        [
                            html.H4("Why Register?", className="text-center mb-4"),
                            html.Ul([
                                html.Li("🔒 Personalized Watchlists"),
                                html.Li("📈 Analyst recommendations"),
                                html.Li("🚀 Stock suggestions based on KPIs"),
                            ], className="benefits-list", style={"line-height": "1.8", "font-size": "1rem", "text-align": "left"}),
                            html.P("Don't miss out on these powerful tools designed for smart investors!", 
                                   className="text-center mt-4")
                        ],
                        className="modal-content-container"
                    )
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Sign Up for Free",
                        href="/register-free",
                        color="success",
                        className="ms-auto register-button text-center",
                        id="close-register-modal-button",
                        # style={"font-size": "1.2rem", "padding": "0.8rem 1.5rem"}
                    ),
                ),
            ],
            id="register-modal",
            is_open=False,  # Initially closed
            backdrop="static",  # Prevent closing by clicking outside
            keyboard=False,  # Prevent closing with escape key
            className="stylish-modal"
        )
    ])


def create_overlay():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Access Restricted")),
            dbc.ModalBody("Please register or log in to save watchlist or change themes"),
            dbc.ModalFooter(
                dbc.Button("Please register or login", href="/register-free", color="primary", id="overlay-registerP-button")
            ),
        ],
        id="login-overlay",
        is_open=False,  # Initially closed
    )


def create_floating_chatbot_button():
    return html.Div(
        dbc.Button("💬", id="open-chatbot-button", color="primary", className="chatbot-button"),
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
        className="bg-primary" , # Start closed
        style={
            "z-index": "2000",
        }    
    )


def create_footer():
    return html.Footer(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H5("Direction", style={"display": "none"}),  # Hide the heading
                    html.Ul([
                        html.Li(html.A("About WatchMyStocks", href="/about", className="footer-link")),
                        html.Li(html.A("Contact Us", href="mailto:mystocks.monitoring@gmail.com?subject=mystocks%20request", className="footer-link")),
                        html.Li(html.A("Dashboard", href="/dashboard", className="footer-link")),
                    ], className="list-unstyled")
                ], md=12, className="d-flex justify-content-center")  # Center the column
            ]),
            html.A(
                html.Img(src="/assets/X-Logo.png", alt="Share on X", style={"width": "30px", "height": "25px"}),
                href="https://twitter.com/share?url=https://mystocksportfolio.io&text=Check out WatchMyStocks!",
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
                    html.P("© 2024 WatchMyStocks. All rights reserved.", className="text-center")
                ], className="d-flex justify-content-center")
            ])
        ], fluid=True,style={"height": "180px"}),
        className="footer"
    )




def paywall_logged_out():
    return html.Div(
        className="bg-light bg-primary-with-shadow",
        children=[
            html.Div([
                html.P("Sign up to Premium to unlock this content...", style={'display': 'inline', 'margin-bottom': '20px', 'font-size': '18px'}),
            ], style={'text-align': 'center', 'margin-top': '30px'}),
            
            html.P("By signing up, you’ll unlock:", style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold'}),

            html.Ul([
                html.Li("🔥 Access to top-performing stocks based on KPIs", style={'font-size': '16px'}),
                html.Li("📈 Weekly updates on the hottest stocks", style={'font-size': '16px'}),
                html.Li("💼 Personalized recommendations based on your risk profile", style={'font-size': '16px'}),
            ], style={'list-style-type': '"✔️ "', 'margin-top': '20px', 'text-align': 'left', 'font-weight': 'normal'}),
            
            html.Div([
                dbc.Button("Sign Up", href="/register", color="success", size="lg", className="mt-3 me-3"),
                dbc.Button("Log In", href="/login", color="secondary", size="lg", className="mt-3"),
            ], style={'text-align': 'center'}),
        ],
        style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'padding': '10px', 'color': 'black', 'background-color': '#007bff'}
    )


def paywall_free_user():
    return html.Div(
        className="bg-light bg-primary-with-shadow",
        children=[
            html.P("Unlock premium features to access this content!", style={'font-size': '24px', 'font-weight': 'bold', 'text-align': 'center', 'margin-top': '30px'}),

            html.P("Upgrade to premium and you’ll unlock:", style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold'}),

            html.Ul([
                html.Li("🔥 Top-performing stocks based on financial KPIs", style={'font-size': '16px'}),
                html.Li("📈 Weekly updates on the hottest stocks", style={'font-size': '16px'}),
                html.Li("💼 Personalized recommendations based on your risk profile", style={'font-size': '16px'}),
            ], style={'list-style-type': '"✔️ "', 'margin-top': '20px', 'text-align': 'left','font-weight': 'normal'}),
            
            html.Div([
                dbc.Button("Upgrade to Premium", href="/register", color="success", size="lg", className="mt-3"),
            ], style={'text-align': 'center'}),
        ],
        style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'padding': '10px', 'color': 'black', 'background-color': '#ffc107'}
    )

def paywall_logged_out_forecast():
    return html.Div(
        className="bg-light bg-primary-with-shadow",
        children=[
            html.Div([
                html.P("Sign up to Premium to unlock this content...", style={'display': 'inline', 'margin-bottom': '20px', 'font-size': '18px'}),

            ], style={'text-align': 'center', 'margin-top': '0px'}),
            
            html.P("By signing up, you’ll unlock:", style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold'}),

            html.Ul([
                html.Li("🌡️ time series forecast", style={'font-size': '16px', 'text-align': 'left'}),
                html.Li("📈 Perform up to 3 forecasts simultaneously", style={'font-size': '16px', 'text-align': 'left'}),
                html.Li("⏱️ Choose your individual forecast horizon", style={'font-size': '16px', 'text-align': 'left'}),
            ], style={'list-style-type': '"✔️ "', 'margin-top': '20px', 'text-align': 'left','font-weight': 'normal'}),
            
            html.Div([
                dbc.Button("Sign Up", href="/register", color="success", size="lg", className="mt-3 me-3"),
                dbc.Button("Log In", href="/login", color="secondary", size="lg", className="mt-3"),
            ], style={'text-align': 'center'}),
        ],
        style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'padding': '10px', 'color': 'black', 'background-color': '#007bff', 'margin-top': '100px'}
    )


def paywall_free_user_forecast():
    return html.Div(
        className="bg-light bg-primary-with-shadow",
        children=[
            html.P("Unlock premium features to access this content!", style={'font-size': '24px', 'font-weight': 'bold', 'text-align': 'center', 'margin-top': '30px'}),

            html.P("Upgrade to premium and you’ll unlock:", style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold'}),

            html.Ul([
                html.Li("🌡️ time series forecast", style={'font-size': '16px', 'text-align': 'left'}),
                html.Li("📈 Perform up to 3 forecasts simultaneously", style={'font-size': '16px', 'text-align': 'left'}),
                html.Li("⏱️ Choose your individual forecast horizon", style={'font-size': '16px', 'text-align': 'left'}),
            ], style={'list-style-type': '"✔️ "', 'margin-top': '20px', 'text-align': 'left','font-weight': 'normal'}),
            
            html.Div([
                dbc.Button("Upgrade to Premium", href="/register", color="success", size="lg", className="mt-3"),
            ], style={'text-align': 'center'}),
        ],
        style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'padding': '10px', 'color': 'black', 'background-color': '#ffc107', 'margin-top': '100px'}
    )


def paywall_recommendation():
    return html.Div(
        className="bg-light bg-primary-with-shadow",
        children=[
            html.Div([
                html.P("Sign up for free, no credit card", style={'display': 'inline', 'margin-bottom': '20px', 'font-size': '18px'}),
            ], style={'text-align': 'center', 'margin-top': '30px'}),
            
            html.P("By signing up, you’ll unlock:", style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold'}),

            html.Ul([
                html.Li("💸 sell, hold and buy analyst recommendations ", style={'font-size': '16px', 'text-align': 'left'}),
                html.Li("📈 historical change of recommendations ", style={'font-size': '16px', 'text-align': 'left'}),
                html.Li("🔎 get recommendations for your watchlist", style={'font-size': '16px', 'text-align': 'left'}),
            ], style={'list-style-type': '"✔️ "', 'margin-top': '20px', 'text-align': 'left','font-weight': 'normal'}),
            
            html.Div([
                dbc.Button("Sign Up for free", href="/register-free", color="success", size="lg", className="mt-3 me-3"),
                dbc.Button("Log In", href="/login", color="secondary", size="lg", className="mt-3"),
            ], style={'text-align': 'center'}),
        ],
        style={'text-align': 'center', 'font-size': '20px', 'font-weight': 'bold', 'padding': '10px', 'color': 'black', 'background-color': '#007bff'}
    )



def create_watchlist_management_layout():
    return dbc.Container([
        # Clickable watchlist area
        html.Div(
            id="clickable-watchlist-area",
            children=[
                dcc.Dropdown(
                    id='saved-watchlists-dropdown',
                    placeholder="Select a saved Watchlist",
                    options=[],
                    disabled=False,
                    searchable=False,
                    style={"margin-bottom": "10px"}
                ),
                dbc.Button("💾 Save", id='create-watchlist-button', color='primary', className="small-button"),
                dbc.Button("X Delete", id='delete-watchlist-button', color='danger', className="small-button", style={"margin-left": "10px"}),

                # Store components to manage modal trigger and clicks
                dcc.Store(id='save-button-clicks', data=0),
            ]
        ),
        
        # Modal for save confirmation
        dbc.Modal([
            dbc.ModalHeader("Save Watchlist"),
            dbc.ModalBody([
                html.Div(id="overwrite-warning", style={"color": "red"}),
                dcc.Input(
                    id='new-watchlist-name',
                    placeholder="Enter Watchlist Name",
                    className="form-control",
                    style={"margin-bottom": "10px", "display": "none"}
                )
            ]),
            dbc.ModalFooter([
                dbc.Button("Save", id='confirm-save-watchlist', color='primary'),
                dbc.Button("Cancel", id='cancel-save-watchlist', color='secondary', className="ml-auto")
            ]),
            
            # dcc.Store(id='save-modal-triggered', data=False)  # Store to control save modal
            dcc.Store(id='save_modal_triggered', data=False)


        ], id="save-watchlist-modal", is_open=False),

        # Delete confirmation modal
        dbc.Modal(
            [
                dbc.ModalHeader("Confirm Delete"),
                dbc.ModalBody("Are you sure you want to delete this watchlist?"),
                dbc.ModalFooter([
                    dbc.Button("Yes, Delete", id="confirm-delete-watchlist", color="danger"),
                    dbc.Button("Cancel", id="cancel-delete-watchlist", color="secondary"),
                ])
            ],
            id="delete-watchlist-modal",
            is_open=False
        )
    ])



# def create_watchlist_management_layout():
#     return dbc.Container([
#         # Clickable watchlist area
#         html.Div(
#             id="clickable-watchlist-area",
#             children=[
#                 dcc.Dropdown(
#                     id='saved-watchlists-dropdown',
#                     placeholder="Select a saved Watchlist",
#                     options=[],
#                     disabled=False,
#                     searchable=False,
#                     style={"margin-bottom": "10px"}
#                 ),
#                 dbc.Button("💾 Save", id='create-watchlist-button', color='primary', className="small-button"),
#                 dbc.Button("X Delete", id='delete-watchlist-button', color='danger', className="small-button", style={"margin-left": "10px"}),

#                 # Store component to track clicks
#                 dcc.Store(id='save-button-clicks', data=0)
#             ]
#         ),
        
#         # Modal for save confirmation
#         dbc.Modal([
#             dbc.ModalHeader("Save Watchlist"),
#             dbc.ModalBody([
#                 html.Div(id="overwrite-warning", style={"color": "red"}),
#                 dcc.Input(
#                     id='new-watchlist-name',
#                     placeholder="Enter Watchlist Name",
#                     className="form-control",
#                     style={"margin-bottom": "10px", "display": "none"}
#                 )
#             ]),
#             dbc.ModalFooter([
#                 dbc.Button("Save", id='confirm-save-watchlist', color='primary'),
#                 dbc.Button("Cancel", id='cancel-save-watchlist', color='secondary', className="ml-auto")
#             ])
#         ], id="save-watchlist-modal", is_open=False),

#         # Delete confirmation modal
#         dbc.Modal(
#             [
#                 dbc.ModalHeader("Confirm Delete"),
#                 dbc.ModalBody("Are you sure you want to delete this watchlist?"),
#                 dbc.ModalFooter([
#                     dbc.Button("Yes, Delete", id="confirm-delete-watchlist", color="danger"),
#                     dbc.Button("Cancel", id="cancel-delete-watchlist", color="secondary"),
#                 ])
#             ],
#             id="delete-watchlist-modal",
#             is_open=False
#         )
#     ])




def create_dashboard_layout(watchlist_management_layout):
    return dbc.Container([
        dbc.Row([
            # Sidebar Filters (for both mobile and desktop)
            dbc.Col([
                # First Card (for stock input, buttons, and date range)
                dbc.Card([
                    dbc.CardBody([

                        html.H1("Stocks monitoring dashboard - WatchMyStocks", style={"display": "none"}),
                        html.H2("Stocks monitoring made easy", style={"display": "none"}),
                        html.H2("Create your personal watchlist", style={"display": "none"}),
                        html.H3("Apple Stock, aaple", style={"display": "none"}),
                        html.H3("Microsoft Stock, msft", style={"display": "none"}),


                        # The stock suggestions input, buttons, and date range will always be visible
                        html.Div([
                            html.H5([
                                "Add Stock to ",
                                html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                            ],className="text-dark"),
                            # Stock suggestions input (always visible)
                            dcc.Dropdown(
                                id='stock-suggestions-input',
                                options=[],
                                placeholder="Enter Company or Symbol",
                                className='custom-dropdown text-dark',
                                multi=False,
                                searchable=True,
                                style={
                                    'border': '2px solid var(--bs-danger)',
                                    'border-radius': '5px',
                                    'padding': '0px',
                                }
                            ),

                            # Buttons (always visible)
                            # html.Div([
                            #     # dbc.Button("Add Stock", id='add-stock-button', color='primary', className='small-button'),
                            # ], className='mb-3'),
                            
                            # Date range selector (always visible)
                            
                            html.Div(id="date-range-container",style={'display': 'none'}, children=[
                                html.Hr(),
                                html.Label([
                                    "Select ",
                                    html.Span("Date Range", className="bg-success text-white rounded px-2")
                                ], className="text-dark"),
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
                                    value='12M', className="text-dark"
                                )
                            ]),
                        ],style={'margin-top': '15px'}) ,
                           

                        # Mobile-specific overlay for watchlist and other filters
                        dbc.Button(
                            id="toggle-filters-button",
                            color="info",
                            outline=False,
                            size="sm",
                            className="mobile-only toggler-icon align-items-center",
                            style={
                                "position": "fixed",
                                "top": "73px",
                                "left": "10px",
                                "z-index": "1001",
                                "font-weight": "bold",
                                "font-size": "18px",
                            },
                            children= html.Span(["  Manage ", html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                                ]),
                        )

                    ], className="sidebar-card-body"),       
                    
                ], className="sidebar-card"),  # Apply the same styling as the second card

                # Mobile overlay for other filters
                html.Div(id="mobile-overlay", className="mobile-overlay", style={"display": "none"}),

                dcc.Store(id='button-state', data=False),  # False means closed, True means open

                # Second Card (for the filters collapse)
                dbc.Collapse(
                    dbc.Card([
                        dbc.CardBody([
                                html.H5([
                                    "Manage ",
                                    html.Span("Watchlist", className="bg-warning text-white rounded px-2")
                                ]),
                                dbc.Button("Reset all", id='reset-stocks-button', color='danger', className='small-button'),
                                html.Span("🔄", id='refresh-data-icon', style={'cursor': 'pointer', 'font-size': '25px'}, className='mt-2 me-2'),

                            # Watchlist filters and management layout
                            dcc.Loading(id="loading-watchlist", type="default", children=[
                                html.Div(id='watchlist-summary', className='mb-3')
                            ]),

                        ]),
                        watchlist_management_layout
                    ], className="filters-collapse"),  # Use the same class for consistency
                    id="filters-collapse",
                    is_open=False  # Initially closed on mobile
                ),

            ], width=12, md=3, style={"margin-top": "10px", "buttom": "50px"}),
                          
                            

            # Main content area (Tabs for Prices, News, Comparison, etc.)
            dbc.Col([
                dbc.Tabs(
                    id="tabs",
                    active_tab="prices-tab",
                    children=[

                        dbc.Tab(label='🌡️ Forecast', tab_id='forecast-tab',children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.P([
                                        "Filter Stocks from ",
                                        html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                    ], className="fs-5"),
                                    html.H3("Forecast stocks prices", style={"display": "none"}),  # for SEO
                                    html.Div([
                                        html.Label("Select up to 3 Stocks:", className="font-weight-bold"),
                                        dcc.Dropdown(
                                            id='forecast-stock-input',
                                            options=[],  
                                            value=[],  
                                            multi=True,
                                            className='form-control text-dark',
                                            searchable=False,
                                        ),
                                        html.Div(id='forecast-stock-warning', style={'color': 'red'}),
                                        html.Label("Forecast Horizon (days):", className="font-weight-bold"),
                                        dcc.Slider(
                                            id='forecast-horizon-input',
                                            min=30, max=365*2, step=30,  # Range from 1 day to 2 years (730 days)
                                            value=90,  # Default value
                                            marks={i: str(i) for i in range(0, 731, 90)},  # Marks at every 30 days
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        ),
                        
                                        dbc.Button("Generate Forecasts", id='generate-forecast-button', color='primary', className='mt-2')
                                    ], className='mb-3'),
                                    dcc.Markdown('''
                                        **Disclaimer:** This forecast is generated using time series forecasting methods, specifically Facebook Prophet. 
                                        These predictions should be considered with caution and should not be used as your single source of financial advice.
                                    ''', style={'font-size': '14px', 'margin-top': '20px', 'color': 'gray'}),
                                    
                                    dcc.Loading(
                                        html.Div(id='forecast-kpi-output', className='mb-3')
                                    ), 
                                    
                                    dcc.Loading(
                                        id="loading-forecast",
                                        type="default",
                                        children=[dcc.Graph(id='forecast-graph', config={'displayModeBar': False})]
                                    ),
                                    html.Div(id='forecast-blur-overlay', style={
                                        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
                                        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                        'backdrop-filter': 'blur(5px)'
                                    })  
                      
                                ])
                                   
                            )
                        ]),
                        dbc.Tab(label='📈 Prices', tab_id="prices-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.P([
                                        "Filter Stocks from ",
                                        html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                    ], className="fs-5"),
                                    dcc.Dropdown(
                                        id='prices-stock-dropdown',
                                        options=[],  
                                        value=[],  
                                        multi=True,
                                        placeholder="Select stocks to display",
                                        searchable=False,
                                        className="text-dark"
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
                                    
                                    # dcc.Graph(id='stock-graph', style={'height': '500px', 'backgroundColor': 'transparent'})
                                    dcc.Loading(id="loading-prices", type="default", children=[
                                        dcc.Graph(id='stock-graph', style={'min-height': '1000px', 'backgroundColor': 'transparent'},config={'displayModeBar': False})
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
                                        value='low',  # Default to medium risk
                                        placeholder="Select Risk Tolerance",
                                        clearable=False,
                                        searchable=False,
                                        className="text-dark"
                                    ),
                                    dcc.Loading(
                                        id="loading-top-stocks",
                                        children=[html.Div(id='top-stocks-table')],  # Placeholder for the stocks table
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
                            )
                        ]),
                        dbc.Tab(label='📰 News', tab_id="news-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    # html.P("Filter your Stocks from selection here"),
                                    html.P([
                                        "Filter Stocks from ",
                                        html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                    ], className="fs-5"),
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
                                        html.Div(id='stock-news', className='news-container')
                                    ])
                                ])
                            )
                        ]),
                        dbc.Tab(label='⚖️ Compare', tab_id="compare-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.P([
                                        "Filter Stocks from ",
                                        html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                    ], className="fs-5"),
                                    html.Label("Select Stocks for Comparison:", className="font-weight-bold"),
                                    dcc.Dropdown(
                                        id='indexed-comparison-stock-dropdown',
                                        options=[],  # Populated dynamically
                                        value=[],  
                                        multi=True,
                                        searchable=False,
                                        className="text-dark"
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
                                        dcc.Graph(id='indexed-comparison-graph', style={'height': '500px'},config={'displayModeBar': False})
                                    ])
                                ])
                            )
                        ]),
                        dbc.Tab(label='❤️ Recommendations', tab_id='recommendations-tab', children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.P([
                                        "Find your Stocks from ",
                                        html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                    ], className="fs-5"),
                                    html.H3("Get analyst stock recommendations", style={"display": "none"}),  # for SEO
                                    dcc.Loading(
                                        id="loading-analyst-recommendations",
                                        type="default",
                                        children=[html.Div(id='analyst-recommendations-content', className='mt-4')]
                                    ),
                                    html.Div(id='recommendation-blur-overlay', style={
                                        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%', 
                                        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'none',
                                        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                                        'backdrop-filter': 'blur(5px)'
                                    })
                                  
                                ])
                            )
                        ]),

                        dbc.Tab(label='📊 Simulate', tab_id="simulate-tab", children=[
                            dbc.Card(
                                dbc.CardBody([
                                    html.P([
                                        "Filter Stocks from ",
                                        html.Span("Watchlist", className="bg-primary text-white rounded px-2")
                                    ], className="fs-5"),
                                    html.H3("Simulate stock profits and losses over historical time period", style={"display": "none"}),  # for SEO
                                    html.Label("Stock Symbol:", className="font-weight-bold"),
                                    dcc.Dropdown(
                                        id='simulation-stock-input',
                                        options=[],  
                                        value=[],  
                                        className='form-control text-dark',
                                        searchable=False,
                                    ),
                                    html.Label("Investment Amount ($):", className="font-weight-bold"),
                                    dcc.Slider(
                                        id='investment-amount',
                                        min=1000, max=100000, step=1000,  # Range from 1 day to 2 years (730 days)
                                        value=5000,  # Default value
                                        marks={i: f'${i//1000}k' for i in range(0, 100001, 10000)},  # Marks every 5,000 formatted as "$5k", "$10k", etc.
                                        tooltip={"placement": "bottom", "always_visible": False}
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

                    ], className="desktop-tabs bg-light sticky-tabs fs-7",                           
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

                        dbc.Label("Username"),
                        dcc.Input(id='profile-username', type='text', disabled=True, className='form-control mb-3'),

                        dbc.Label("Email"),
                        dcc.Input(id='profile-email', type='email', disabled=True, className='form-control mb-3'),

                        dbc.Label("Subscription Status"),
                        html.Div(id='profile-subscription', className='form-control mb-3'),

                        dbc.Button("Change Password", id='toggle-password-fields', color='link', className='mb-3', style={"display": "none"}),
                        
                        html.Div([
                            dbc.Label("Current Password"),
                            dcc.Input(id='profile-current-password', type='password', placeholder="Enter current password", className='form-control mb-3'),

                            dbc.Label("New Password"),
                            dcc.Input(id='profile-password', type='password', placeholder="Enter new password", className='form-control mb-3'),

                            # Updated Password requirement list - no special character requirement
                            html.Ul([
                                html.Li("At least 8 characters", id='profile-req-length', className='text-muted'),
                                html.Li("At least one uppercase letter", id='profile-req-uppercase', className='text-muted'),
                                html.Li("At least one lowercase letter", id='profile-req-lowercase', className='text-muted'),
                                html.Li("At least one digit", id='profile-req-digit', className='text-muted')
                            ], className='mb-3'),

                            dbc.Label("Confirm New Password"),
                            dcc.Input(id='profile-confirm-password', type='password', placeholder="Confirm new password", className='form-control mb-3'),
                            
                        ], id='password-fields-container', style={"display": "none"}),

                        dbc.Col(dbc.Button("Cancel Subscription", id="cancel-subscription-btn", color="danger", className="ml-auto")),
                        dbc.Modal(
                            [
                                dbc.ModalHeader("Confirm Cancelation"),
                                dbc.ModalBody([
                                    html.P("Are you sure you want to cancel your subscription? You will lose access to the following features:"),
                                    html.Ul([
                                        html.Li("🔒 Personalized Watchlists"),
                                        html.Li("📈 Analyst recommendations"),
                                        html.Li("🚀 Stock suggestions based on KPIs")
                                    ])
                                ]),
                                dbc.ModalFooter([
                                    dbc.Button("No, Keep Subscription", id="close-cancel-modal-btn", className="ml-auto"),
                                    dbc.Button("Yes, Cancel Subscription", id="confirm-cancel-btn", color="bg-secondary")
                                ])
                            ],
                            id="cancel-subscription-modal",
                            centered=True
                        ),

                        html.Div(id="subscription-status", className="mt-4"),

                        html.Div([
                            dbc.Button("Edit", id='edit-profile-button', color='primary', className='me-2'),
                            dbc.Button("Save", id='save-profile-button', color='success', className='me-2', style={"display": "none"}),
                            dbc.Button("Cancel", id='cancel-edit-button', color='danger', style={"display": "none"})
                        ], style={"float": "right"}),

                        html.Div(id='profile-output', className='mt-3')
                    ])
                ])
            ], width=12, md=6, className="mx-auto")
        ])
    ], fluid=True)



# def create_profile_layout():
#     return dbc.Container([
#         dbc.Row([
#             dbc.Col([
#                 dbc.Card([
#                     dbc.CardBody([
#                         html.H1("👩🏻‍💻 User Profile", className="text-center"),

#                         # Username field
#                         dbc.Label("Username"),
#                         dcc.Input(id='profile-username', type='text', disabled=True, className='form-control mb-3'),

#                         # Email field (permanently disabled)
#                         dbc.Label("Email"),
#                         dcc.Input(id='profile-email', type='email', disabled=True, className='form-control mb-3'),

#                         # Subscription status
#                         dbc.Label("Subscription Status"),
#                         html.Div(id='profile-subscription', className='form-control mb-3'),

#                         # Password section hidden initially
#                         dbc.Button("Change Password", id='toggle-password-fields', color='link', className='mb-3', style={"display": "none"}),  # Hidden by default
                        
#                         html.Div([
#                             dbc.Label("Current Password"),
#                             dcc.Input(id='profile-current-password', type='password', placeholder="Enter current password", className='form-control mb-3'),

#                             dbc.Label("New Password"),
#                             dcc.Input(id='profile-password', type='password', placeholder="Enter new password", className='form-control mb-3'),

#                             # Password requirement list
#                             html.Ul([
#                                 html.Li("At least 8 characters", id='profile-req-length', className='text-muted'),
#                                 html.Li("At least one uppercase letter", id='profile-req-uppercase', className='text-muted'),
#                                 html.Li("At least one lowercase letter", id='profile-req-lowercase', className='text-muted'),
#                                 html.Li("At least one digit", id='profile-req-digit', className='text-muted'),
#                                 # html.Li("At least one special character (!@#$%^&*(),.?\":{}|<>)_", id='profile-req-special', className='text-muted')
#                             ], className='mb-3'),

#                             dbc.Label("Confirm New Password"),
#                             dcc.Input(id='profile-confirm-password', type='password', placeholder="Confirm new password", className='form-control mb-3'),
                            
#                         ], id='password-fields-container', style={"display": "none"}),  # Password fields hidden by default
#                         dbc.Col(dbc.Button("Cancel Subscription", id="cancel-subscription-btn", color="danger", className="ml-auto")),
#                         dbc.Modal(
#                             [
#                                 dbc.ModalHeader("Confirm Cancelation"),
#                                 dbc.ModalBody([
#                                     html.P("Are you sure you want to cancel your subscription? You will lose access to the following features:"),
#                                     html.Ul([
#                                         html.Li("🔒 Personalized Watchlists"),
#                                         html.Li("📈 Analyst recommendations"),
#                                         html.Li("🚀 Stock suggestions based on KPIs"),
#                                     ]),
#                                 ]),
#                                 dbc.ModalFooter([
#                                     dbc.Button("No, Keep Subscription", id="close-cancel-modal-btn", className="ml-auto"),
#                                     dbc.Button("Yes, Cancel Subscription", id="confirm-cancel-btn", color="bg-secondary")
#                                 ])
#                             ],
#                             id="cancel-subscription-modal",
#                             centered=True,
#                         ),
#                         html.Div(id="subscription-status", className="mt-4"),


#                         # Buttons aligned to the right
#                         html.Div([
#                             dbc.Button("Edit", id='edit-profile-button', color='primary', className='me-2'),
#                             dbc.Button("Save", id='save-profile-button', color='success', className='me-2', style={"display": "none"}),
#                             dbc.Button("Cancel", id='cancel-edit-button', color='danger', style={"display": "none"})
#                         ], style={"float": "right"}),
                        

#                         # Output area for messages
#                         html.Div(id='profile-output', className='mt-3')
#                     ])
#                 ])
#             ], width=12, md=6, className="mx-auto")
#         ])
#     ], fluid=True)

   
       
def create_subscription_selection_layout(is_free_user=False):
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Choose the Perfect Plan for You", className="text-center mt-5 mb-4"),
                html.P("Unlock the best stock monitoring experience tailored to your needs.", className="text-center lead mb-5"),
            ], width=12,className="text-dark")
        ]),

        # Display both free and premium plan options
        html.Div([
            # Free Plan - greyed out for existing free users
            dbc.Card([
                dbc.CardHeader(html.H3("Free Plan", className="text-center text-success")),
                dbc.CardBody([
                    # html.Div([html.H4("Free access, no credit card", className="text-center text-success mb-4")]),
                    
                    html.Div([
                        html.H4([
                            "Free access, ",
                            html.Span("no credit card", className="bg-success text-white rounded px-2")
                            ],className="text-center text-success")
                        ]),
                    html.Div([html.H6("", className="text-center text-secondary")]),

                    html.H4("What You Get", className="text-center mt-3"),

                    html.Div(["📊 Create and save your own stock watchlists"], className="mb-3"),
                    html.Div(["🔍 Monitor your favorite stocks"], className="mb-3"),
                    html.Div(["📈 Analyst recommendations"], className="mb-3"),
                    html.Div([html.Span("🚀 Stock suggestions based on KPIs", className="text-muted", style={'text-decoration': 'line-through'})], className="mb-3"),
                    html.Div([html.Span("📊 Advanced stock forecasts", className="text-muted", style={'text-decoration': 'line-through'})], className="mb-3"),
                    html.Div([
                        dbc.Button("You are on Free Plan", color='secondary', className='w-100 mt-auto', disabled=is_free_user)
                        if is_free_user else
                        dbc.Button("Sign Up for Free", id='free-signup-button', color='success', className='w-100 mt-auto')
                    ], className="d-grid gap-2 mb-3"),
                ], className="p-4 d-flex flex-column h-100"),
            ], className="h-100 border-light", style={"max-width": "400px"}),

            # Premium Plan
            dbc.Card([
                dbc.CardHeader(html.H3("Premium Plan", className="text-center text-light"),className="bg-primary"),
                dbc.CardBody([
                    html.Div([html.H4("$2.50 USD per week", className="text-center text-primary")]),
                    html.Div([html.H6("billed as $9.99 every 4 weeks", className="text-center text-secondary")]),
                    html.H4("What You Get", className="text-center mt-3"),
                    html.Div(["📊 Create and save your own stock watchlists"], className="mb-3"),
                    html.Div(["🔍 Monitor your favorite stocks"], className="mb-3"),
                    html.Div(["📈 Analyst recommendations"], className="mb-3"),
                    html.Div(["🚀 Stock suggestions based on KPIs"], className="mb-3"),
                    html.Div(["📊 Advanced stock forecasts"], className="mb-3"),
                    html.Div([dbc.Button("Subscribe Now", id='paid-signup-button', color='primary', className='w-100 mt-auto')], className="d-grid gap-2 mb-3"),
                ], className="p-4 d-flex flex-column h-100"),
            ], className="shadow-lg h-100 border-3 border-primary", style={"max-width": "400px"}),
        ], style={
            "display": "flex", 
            "justify-content": "center", 
            "gap": "30px",  
            "flex-wrap": "wrap", 
            "margin": "0 auto",
        }),

        dbc.Row([
            dbc.Col([html.P("No credit card required for the Free Plan.", className="text-center text-dark mt-4")], width=12)
        ]),
        
        html.P([
            "Wanna know more about the Features? ",
            html.A("Check it out here", href="/about", className="text-center",
                   style={"color": "blue", "text-decoration": "underline"})
        ],className="text-center text-dark mt-4")
        
    ], fluid=True, className="custom-light-bg")
            

def create_register_layout(plan):
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H1(f"📝 Register ({plan.capitalize()} Plan)", className="text-center mt-4", style={"display":"none"}),
                        html.H3("Register with Google", className="text-center mt-4"),

                        html.A([
                            dbc.Button([
                                html.Img(src='/assets/google_logo.png', height="30px", className='mr-2', alt="Google Logo"),  # Google logo
                                "Sign Up with Google"
                            ], id='google-signup-button', color='danger', className='mt-2 w-100')
                        ], href="/login/google") ,
                        
                        html.Br(),  # Line separator
                        html.Br(),  # Line separator
                        html.Hr(),  # Line separator
                        html.Br(),  # Line separator
                        html.H3("Or register with E-mail", className="text-center mt-4"),

                        # Registration form fields
                        dcc.Input(id='username', type='text', placeholder='Username', className='form-control mb-3'),
                        dcc.Input(id='email', type='email', placeholder='Email', className='form-control mb-3'),
                        dcc.Input(id='password', type='password', placeholder='Password', className='form-control mb-3'),
                        
                        # Password requirements
                        html.Ul([
                            html.Li("At least 8 characters", id='req-length', className='text-muted'),
                            html.Li("At least one uppercase letter", id='req-uppercase', className='text-muted'),
                            html.Li("At least one lowercase letter", id='req-lowercase', className='text-muted'),
                            html.Li("At least one digit", id='req-digit', className='text-muted'),
                            # html.Li("At least one special character (!@#$%^&*(),.?\":{}|<>)_", id='req-special', className='text-muted')
                        ], className='mb-3'),
                        
                        dcc.Store(id='selected-plan', data=plan),

                        # Confirm password
                        dcc.Input(id='confirm_password', type='password', placeholder='Confirm Password', className='form-control mb-3'),

                        # Register button
                        dbc.Button("Register", id='register-button', color='primary', className='mt-2 w-100'),
                        dcc.Loading(html.Div(id='register-output', className='mt-3')),
                        
                                               
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
                        html.H1("🔐 Login", className="text-center"),
                        html.H3("Login with Google", className="text-center mt-4"),
                        html.A([
                            dbc.Button([
                                html.Img(src='/assets/google_logo.png', height="30px", className='mr-2', alt="Google Logo"),
                                "Login with Google"
                            ], id='google-login-button', color='danger', className='mt-2 w-100')
                        ], href="/login/google"),
                       
                        html.Br(),  # Line separator
                        html.Br(),  # Line separator
                        html.Hr(),  # Line separator
                        html.Br(),  # Line separator

                    
                        html.H3("Or Login with Username and Password", className="text-center mt-4"),

                        # Username and Password Login
                        dcc.Input(id='login-username', type='text', placeholder='Username', className='form-control mb-3'),
                        dcc.Input(id='login-password', type='password', placeholder='Password', className='form-control mb-3'),
                        dbc.Button("Login", id='login-button', color='primary', className='mt-2 w-100'),

                        # Error message placeholder
                        html.Div(id='login-output', className='mt-3'),
                        
                        # Forgot password link
                        html.Div([
                            html.P("Forgot your password?", className="text-center"),
                            html.A("Reset Password", href="/forgot-password", className="text-center", style={"display": "block"}),
                        ], className='mt-3'),
                        
                        # Google Login Button
                       
                        # Register link
                        html.Div([
                            html.P("Don't have an account?", className="text-center"),
                            html.A("Register here", href="/register", className="text-center", style={"display": "block"})
                        ], className='mt-3')
                    ])
                ])
            ], width=12, md=6, className="mx-auto")
        ]),
        
        # Additional informational section
        dbc.Row([
            dbc.Col([
                html.H3("Welcome to WatchMyStocks Dashboard", className="text-center mt-5 mb-4"),
                html.P([
                    "Learn more about the application on the ",
                    html.A("About page.", href="/about", className="text-primary")
                ], className="text-center")
            ], width=12, md=6, className="mx-auto")
        ])
    ], fluid=True)


def create_forgot_password_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H1("🔒 Reset Password", className="text-center"),
                        html.P("Enter your email to reset your password.", className="text-center"),
                        dcc.Input(id='reset-email', type='email', placeholder='Email', className='form-control mb-3'),
                        dbc.Button("Send Reset Link", id='reset-button', color='primary', className='mt-2 w-100'),
                        html.Div(id='reset-output', className='mt-3')
                    ])
                ])
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
                "caption": "Financial indicators, custom time windows, and more.",
                "loading": "lazy"
            },
            {
                "key": "2",
                "src": "/assets/gif4.gif",
                "alt": "Demo 2",
                "header": "Save your Watchlist(s)",
                "caption": "Create your Account, save your Watchlist(s) and your custom Theme.",
                "loading": "lazy"
            },
            {
                "key": "3",
                "src": "/assets/gif2.gif",
                "alt": "Demo 3",
                "header": "Get latest Stock News",
                "caption": "Get tailored News Updates.",
                "loading": "lazy"
            },
            {
                "key": "4",
                "src": "/assets/gif3.gif",
                "alt": "Demo 4",
                "header": "Stock Forecasts and Recommendations",
                "caption": "Visualize forecasts and access analyst recommendations.",
                "loading": "lazy"
            },
            {
                "key": "5",
                "src": "/assets/gif5.gif",
                "alt": "Demo 5",
                "header": "Gen AI powered Chatbot",
                "caption": "Chat with your financial advisor bot powered by Chat GPT-3.5 Turbo.",
                "loading": "lazy"
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
                    html.H2("Why Choose WatchMyStocks?", className="text-center mt-5 mb-3", style={"color": "black"}),
                    html.P("Comprehensive Data: Access to a wide range of financial data and tools for better decision-making. "
                           "User-Friendly Interface: Simple and intuitive design, making it easy for users at all levels to navigate. "
                           "Advanced Analytics: Leverage sophisticated forecasting and simulation tools to gain a competitive edge. "
                           "Real-Time Updates: Stay informed with up-to-date news and market data.", className="text-dark lead text-center"),
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
                    ], className="text-dark checked-list"),
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
                    "margin": "20px 0" ,
                    "position":"fixed"# Add some margin around the paragraph
                })
            ], className="mx-auto", style={"max-width": "800px"}))
        ])
    ], fluid=True)

watchlist_management_layout = create_watchlist_management_layout()
dashboard_layout = create_dashboard_layout(watchlist_management_layout)
login_layout = create_login_layout()
carousel_layout = create_carousel()
about_layout = create_about_layout(carousel_layout)
profile_layout = create_profile_layout()
forgot_layout = create_forgot_password_layout()

subscription_page = create_subscription_selection_layout()
login_overlay = create_overlay()
