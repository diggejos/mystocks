
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import dash

dash.register_page(
    __name__,
    title="Stocks Dashboard - WatchMyStocks - Save your watchlist today",
    path='/',
    description="WatchMyStocks: Track stock prices, analyze trends, and monitor the stock market today. Save custom watchlists and forecast stock movements easily."
)


# Layout template for feature sections with text and video
def create_feature_section(title, description, video_src, link_href, button_text, button_id, reverse=False):
    # Determine text color class based on the background color
    text_color_class = "text-light" if not reverse else "text-dark"

    return html.Div(
        className="py-5",
        style={
            "backgroundColor": "var(--bs-light)" if reverse else "var(--bs-primary)"},
        children=[
            dbc.Container(
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            html.H2(
                                title, className=f"mb-3 {text_color_class}"),
                            html.P(description,
                                   className=f"lead {text_color_class}"),
                            html.Button(
                                button_text,
                                id=button_id,
                                n_clicks=0,
                                className="btn btn-success mt-3"
                            )
                        ]),
                        md=6,
                        className="order-md-2" if reverse else "order-md-1",
                        style={"display": "flex", "flexDirection": "column",
                               "justifyContent": "center"}
                    ),
                    dbc.Col(
                        html.Video(
                            src=video_src,
                            controls=False,
                            loop=True,
                            muted=True,
                            autoPlay=True,
                            title=f"{title} demo video",
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
            html.Div(
                className="typewriter",
                style={
                    "textAlign": "center",
                    "padding": "20px 10px",
                    "maxWidth": "100%",
                    "overflow": "hidden"
                },
                children=[
                    html.H1(
                        "Welcome to WatchMyStocks",
                        style={
                            "fontSize": "4rem",
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
            html.Div([
                html.Button("Explore Stock Prices", id="btn-prices",
                            n_clicks=0, className="btn btn-primary btn-lg m-2"),
                html.Button("Forecast Stocks", id="btn-forecast",
                            n_clicks=0, className="btn btn-info btn-lg m-2"),
                html.Button("Read News", id="btn-news", n_clicks=0,
                            className="btn btn-secondary btn-lg m-2"),
                html.Button("Compare Stocks", id="btn-compare",
                            n_clicks=0, className="btn btn-warning btn-lg m-2"),
                html.Button("Get Hottest Stocks", id="btn-hotstocks",
                            n_clicks=0, className="btn btn-danger btn-lg m-2"),
            ])
        ]
    ),

    create_feature_section(
        "Real-Time Stock Prices",
        "Stay updated with real-time stock prices and trends for informed decisions. "
        "Access detailed price charts, including line and candlestick options, to analyze short-term and long-term performance. "
        "Our platform provides up to 10 years of historical data, making it easier for you to track price movements and make smarter trading decisions. "
        "Customize your stock view with moving averages and volume indicators to get a clearer picture of the market.",
        "/assets/stock_prices_demo.mp4",
        "/prices",
        "View Prices",
        "btn-prices-section"
    ),

    create_feature_section(
        "Stock Forecasting",
        "Analyze future trends using advanced forecasting tools for better decision-making. "
        "Leverage cutting-edge algorithms to generate up to three forecasts simultaneously. "
        "Whether you're planning short-term trades or long-term investments, our forecasting tools allow you to look ahead for up to two years. "
        "Make informed predictions about market movements and minimize risks in your portfolio.",
        "/assets/stock_forecast_demo.mp4",
        "/forecast",
        "Go to Forecast",
        "btn-forecast-section",
        reverse=True
    ),

    create_feature_section(
        "Stock Comparison",
        "Compare stocks against market indices and peers to find the best opportunities. "
        "Use our powerful comparison tools to evaluate stocks from your watchlist against benchmarks like the S&P 500. "
        "Identify outperforming stocks, assess trends, and optimize your portfolio based on accurate and comprehensive data. "
        "Whether you’re a beginner or an experienced trader, our comparison tools will help you make confident decisions.",
        "/assets/stock_comparison_demo.mp4",
        "/compare",
        "Compare Stocks",
        "btn-compare-section"
    ),

    create_feature_section(
        "Get the Hottest Stocks",
        "Discover the hottest stocks to consider investing in today. "
        "Our platform analyzes a vast number of stocks across industries and ranks them based on their key performance indicators. "
        "Personalize your results with a risk profile that matches your investment strategy. "
        "Find the best opportunities in the market with our regularly updated lists of top-performing stocks.",
        "/assets/hot_stocks_demo.mp4",
        "/hotstocks",
        "Get hottest Stocks",
        "btn-hotstocks-section",
        reverse=True
    ),

    create_feature_section(
        "AI Chatbot",
        "Get instant answers and smart assistance with our AI-powered chatbot. "
        "Whether you have questions about stock trends, need help navigating the platform, or want quick insights into market performance, "
        "our chatbot is here to help. Save time and get the information you need to make informed trading decisions faster.",
        "/assets/ai_chatbot_demo.mp4",
        "/prices",
        "Chat Now",
        "btn-chatbot-section"
    ),

    create_feature_section(
        "Save Your Watchlist",
        "Create an account and save multiple watchlists to monitor your favorite stocks. "
        "Our watchlist feature allows you to track stocks that matter to you and access them anytime, anywhere. "
        "Stay organized, set alerts, and make better investment decisions by keeping your top picks in one place. "
        "Sign up today to start building your personalized watchlist.",
        "/assets/watchlist_demo.mp4",
        "/prices",
        "Create Your Watchlist",
        "btn-watchlist-section",
        reverse=True
    ),

    create_feature_section(
        "Stock News",
        "Stay informed with the latest stock news and updates tailored to your watchlist or stocks of interest. "
        "Get curated news from trusted sources and stay ahead of market trends. "
        "From breaking news to in-depth analysis, our news section ensures you're always up to date with what's happening in the stock market.",
        "/assets/stock_news_demo.mp4",
        "/news",
        "Read News",
        "btn-news-section"
    ),
    # Adding the JavaScript to the layout
    html.Script(js_script)
])


# Client-Side Callbacks
app = dash.get_app()

# Button-to-href mapping
pages = {
    "btn-prices": "/prices",
    "btn-prices-section": "/prices",
    "btn-forecast": "/forecast",
    "btn-forecast-section": "/forecast",
    "btn-news": "/news",
    "btn-news-section": "/news",
    "btn-compare": "/compare",
    "btn-compare-section": "/compare",
    "btn-hotstocks": "/hotstocks",
    "btn-hotstocks-section": "/hotstocks",
    "btn-chatbot": "/chatbot",
    "btn-chatbot-section": "/chatbot",
    "btn-watchlist": "/save-watchlist",
    "btn-watchlist-section": "/save-watchlist",
}

# Register client-side callbacks for navigation
for button_id, href in pages.items():
    app.clientside_callback(
        f"""
        function(n_clicks) {{
            if ((n_clicks || 0) > 0) {{
                window.location.href = "{href}";
            }}
            return 0;
        }}
        """,
        Output(button_id, "n_clicks"),
        Input(button_id, "n_clicks")
    )
