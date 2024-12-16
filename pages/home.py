import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import dash

dash.register_page(
    __name__,
    title="Stocks Dashboard - WatchMyStocks - Save your watchlist today",
    path='/',
    description="Welcome to WatchMyStocks - Your Stocks Dashboard to monitor your favorite stocks and save your watchlist"
)


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
                            html.Button(
                                button_text,
                                id=f"btn-{button_text.replace(' ', '-').lower()}",
                                n_clicks=0,
                                className="btn btn-success mt-3"
                            )
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
                                "width": "100%",
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
            html.H1("Welcome to WatchMyStocks", style={"fontSize": "4rem", "fontWeight": "bold"}),
            html.H2("Your Stocks Dashboard"),
            html.H3("Simplicity is key"),
            html.P(
                "Your go-to platform for tracking, forecasting, and monitoring stock trends.",
                style={"fontSize": "1.5rem", "margin": "20px 0", "color": "var(--bs-primary)"}
            ),
            html.Div([
                html.Button("Explore Stock Prices", id="btn-prices", n_clicks=0, className="btn btn-primary btn-lg m-2"),
                html.Button("Forecast Stocks", id="btn-forecast", n_clicks=0, className="btn btn-info btn-lg m-2"),
                html.Button("Read News", id="btn-news", n_clicks=0, className="btn btn-secondary btn-lg m-2"),
                html.Button("Compare Stocks", id="btn-compare", n_clicks=0, className="btn btn-warning btn-lg m-2"),
                html.Button("Get Hottest Stocks", id="btn-hotstocks", n_clicks=0, className="btn btn-danger btn-lg m-2"),
            ])
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

# Client-Side Callbacks for All Buttons
app = dash.get_app()

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.location.href = "/prices";
        }
    }
    """,
    Output('btn-prices', 'n_clicks'),
    Input('btn-prices', 'n_clicks')
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.location.href = "/forecast";
        }
    }
    """,
    Output('btn-forecast', 'n_clicks'),
    Input('btn-forecast', 'n_clicks')
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.location.href = "/news";
        }
    }
    """,
    Output('btn-news', 'n_clicks'),
    Input('btn-news', 'n_clicks')
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.location.href = "/compare";
        }
    }
    """,
    Output('btn-compare', 'n_clicks'),
    Input('btn-compare', 'n_clicks')
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.location.href = "/hotstocks";
        }
    }
    """,
    Output('btn-hotstocks', 'n_clicks'),
    Input('btn-hotstocks', 'n_clicks')
)
