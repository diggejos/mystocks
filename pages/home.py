import dash_bootstrap_components as dbc
from dash import html, dcc
import dash

dash.register_page(__name__, title="Home - WatchMyStocks", path='/',
                   description="Welcome to WatchMyStocks - Your Stocks Dashboard")

# Layout template for feature sections with text and video
def create_feature_section(title, description, video_src, link_href, button_text, reverse=False):
    # Determine text color class based on the background color
    text_color_class = "text-light" if not reverse else "text-dark"

    return html.Div(
        className="py-5",
        style={"backgroundColor": "var(--bs-light)" if reverse else "var(--bs-primary)"},
        children=[
            dbc.Container(
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            html.H2(title, className=f"mb-3 {text_color_class}"),
                            html.P(description, className=f"lead {text_color_class}"),
                            dbc.Button(button_text, href=link_href, color="success", className="mt-3")
                        ]),
                        md=6,
                        className="order-md-2" if reverse else "order-md-1",
                        style={"display": "flex", "flexDirection": "column", "justifyContent": "center"}
                    ),
                    dbc.Col(
                        html.Video(
                            src=video_src,
                            controls=False,
                            loop=True,
                            muted=True,
                            autoPlay=True,
                            title=f"{title} demo video",  # Descriptive title for SEO and accessibility
                            className="video-demo",
                            style={
                                "width": "80%",
                                "maxWidth": "800px",
                                "borderRadius": "8px",
                                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)"
                            }
                        ),
                        md=6,
                        className="order-md-1" if reverse else "order-md-2"
                    )
                ]),
                fluid=True
            )
        ]
    )



# JavaScript for playing videos only when visible
js_script = """
document.addEventListener('DOMContentLoaded', function () {
    const videos = document.querySelectorAll('.video-demo');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.play();
            } else {
                entry.target.pause();
            }
        });
    }, {
        threshold: 0.5  // Start playing when 50% of the video is visible
    });

    videos.forEach(video => {
        observer.observe(video);
    });
});
"""

# Main layout
layout = html.Div([
    # Hero section
    html.Div(

        style={
            "backgroundImage": "url('/assets/background_picture.svg')",
            "backgroundSize": "cover",
            "backgroundPosition": "center",
            "padding": "100px 0",
            "color": "white",
            "textAlign": "center",
        },
        children=[
            html.Link(
                href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400&display=swap",
                rel="stylesheet"
            ),
            html.Div(
                className="typewriter",
                style={
                    "textAlign": "center",
                    "padding": "20px 10px",  # Add padding to prevent edges on mobile
                    "maxWidth": "100%",      # Ensure the text block is not too wide
                    "overflow": "hidden"     # Prevent overflow on smaller screens
                },
                children=[
                    html.H1(
                        "Welcome to WatchMyStocks",
                        style={
                            "fontSize": "4rem",  # This adjusts based on the media query
                            "fontWeight": "bold",
                            "fontFamily": "'Roboto Mono', monospace",
                            "margin": "0 auto",
                            "display": "inline-block"
                        }
                    )
                ]
            ),


            html.H2("Your Stocks Dashboard"),
            html.H3("Simplicity is key"),


            html.P(
                "Your go-to platform for tracking, forecasting, and monitoring stock trends.", 
                style={"fontSize": "1.5rem", "margin": "20px 0", "color": "var(--bs-primary)"}
            ),
            dbc.Button("Explore Stock Prices", href="/prices", color="primary", size="lg", className="m-2"),
            dbc.Button("Forecast Stocks", href="/forecast", color="info", size="lg", className="m-2"),
            dbc.Button("Read News", href="/news", color="secondary", size="lg", className="m-2")
        ]
    ),

    # Feature sections with buttons
    create_feature_section(
        "Real-Time Stock Prices",
        "Stay updated with real-time stock prices and trends for informed decisions. Choose between line-chart or candlestick-chart and get up to 10 years historical prices.",
        "/assets/stock_prices_demo.mp4",
        "/prices",
        "View Prices"
    ),
    create_feature_section(
        "Stock Forecasting",
        "Analyze future trends using advanced forecasting tools for better decision-making. Generate up to 3 forecasts simultaneously with a time-window of up to 2 years.",
        "/assets/stock_forecast_demo.mp4",
        "/forecast",
        "Go to Forecast",
        reverse=True
    ),
    
    create_feature_section(
        "Stock Comparison",
        "Compare stocks against market indices and peers to find the best opportunities. See how the stocks in your watchlist perform against the market e.g. SP500 indices.",
        "/assets/stock_comparison_demo.mp4",
        "/compare",
        "Compare Stocks",
    ),
    create_feature_section(
        "Get the hottest Stocks",
        "Get a list of currently hot stocks to consider investing in based on your desired risk profile. The list considers a large number of stocks and compares respective KPIs against each other.",
        "/assets/hot_stocks_demo.mp4",
        "/hotstocks",
        "Get hottest Stocks",
        reverse=True

    ),
    create_feature_section(
        "AI Chatbot",
        "Interact with our AI-powered chatbot for quick, smart answers and assistance.",
        "/assets/ai_chatbot_demo.mp4",
        "/prices",
        "Chat Now"
    ),
    create_feature_section(
        "Save your Watchlist",
        "Create an Account and save multiple watchlists.",
        "/assets/watchlist_demo.mp4",
        "/prices",
        "Create your watchlist",
        reverse=True
    ),
    create_feature_section(
        "Stock News",
        "Stay informed with the latest stock news and updates tailored to your watchlist or stocks of interest.",
        "/assets/stock_news_demo.mp4",
        "/news",
        "Read News"
    ),

    # Adding the JavaScript to the layout
    html.Script(js_script)
])
