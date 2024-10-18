import dash_bootstrap_components as dbc
import yfinance as yf
from dash import html
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from dash import dash_table
import re
import requests
from prophet import Prophet
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import url_for
from flask import render_template
from models import User
from flask import session
from dash import dcc
import os
import logging

logging.getLogger('cmdstanpy').setLevel(logging.WARNING)



def generate_unique_username(base_username):
    # Remove any non-alphanumeric characters and make it lowercase
    clean_username = re.sub(r'\W+', '', base_username).lower()
    # Check if the username already exists
    user = User.query.filter_by(username=clean_username).first()
    if not user:
        return clean_username
    # Append a number to the username to make it unique
    counter = 1
    while True:
        new_username = f"{clean_username}{counter}"
        user = User.query.filter_by(username=new_username).first()
        if not user:
            return new_username
        counter += 1


def get_user_role():
    # Check if user is logged in
    logged_in = session.get('logged_in', False)
    username = session.get('username', None)

    if not logged_in:
        return 'logged_out'

    user = User.query.filter_by(username=username).first()

    # Define user roles based on subscription status
    if user and user.subscription_status == 'premium':
        return 'premium'
    elif user:
        return 'free'
    else:
        return 'logged_out'


def send_welcome_email(user_email, username, mail):
    msg = Message("Welcome to WatchMyStocks!",
                  sender="mystocks.monitoring@gmail.com",
                  recipients=[user_email])
    msg.html = render_template('welcome_email.html', username=username)
    mail.send(msg)


def send_watchlist_email(user_email, username,mail,app):
    with app.app_context():
        msg = Message("How to Create Your First Watchlist!", 
                      recipients=[user_email], 
                      sender="mystocks.monitoring@gmail.com")

        # Attach the GIF
        with app.open_resource(os.path.join('assets', 'watchlist-tutorial.gif')) as gif:
            msg.attach("watchlist-tutorial.gif", "image/gif", gif.read())

        # Use cid to reference the attached GIF in the email body
        msg.html = render_template('watchlist_email.html', username=username, gif_cid='watchlist-tutorial.gif')
        mail.send(msg)

        print(f"Email sent to {user_email}")

    
def send_confirmation_email(email, token, mail):
     msg = Message('Confirm Your Email', sender='mystocks.monitoring@gmail.com', recipients=[email])
     link = url_for('confirm_email', token=token, _external=True)
     msg.body = f'Please confirm your email by clicking the link: {link}'
     mail.send(msg)
 
def send_reset_email(user_email, reset_url, mail):
    msg = Message("Password Reset Request", 
                  sender="mystocks.monitoring@gmail.com", 
                  recipients=[user_email])
    msg.html = render_template('reset_password_email.html', reset_url=reset_url)
    mail.send(msg)
    
    
def send_cancellation_email(user_email, username,mail):
    msg = Message(
        subject="Your WatchMyStocks Subscription Has Been Cancelled",
        recipients=[user_email],
        sender='mystocks.portfolio@gmail.com'
    )
    msg.html = render_template('cancellation_email.html', username=username)
    mail.send(msg)   



def fetch_news(symbols, max_articles=4):
    news_content = []

    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        news = ticker.news  # Fetch news using yfinance

        if news:
            news_content.append(html.H4(f"News for {symbol}", className="mt-4"))

            articles = []
            for idx, article in enumerate(news[:max_articles]):  # Display only the first `max_articles` news articles
                related_tickers = ", ".join(article.get('relatedTickers', []))
                publisher = article.get('publisher', 'Unknown Publisher')

                # Consistent card height
                news_card = dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(
                                html.A(article['title'], href=article['link'], target="_blank"),
                                # style={"white-space": "nowrap", "overflow": "hidden", "text-overflow": "ellipsis"}

                            ),
                            html.Img(
                                src=article['thumbnail']['resolutions'][0]['url'],
                                style={"max-width": "150px", "height": "auto", "margin-bottom": "10px", "loading": "lazy"},alt="stock news"
                            ) if 'thumbnail' in article else html.Div(),
                            html.P(f"Related Tickers: {related_tickers}" if related_tickers else "No related tickers available."),
                            html.Footer(
                                f"Published by: {publisher} | Published at: {datetime.utcfromtimestamp(article['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')}",
                                style={"font-size": "12px", "margin-top": "auto"}
                            )
                        ], style={"min-height": "250px", "max-height": "350px", "display": "flex", "flex-direction": "column"})
                    ),
                    xs=12, md=6,  # Full width on mobile, half width on desktop
                    className="mb-2"
                )
                articles.append(news_card)

            news_content.append(dbc.Row(articles, className="news-row"))

            if len(news) > max_articles:
                news_content.append(
                    dbc.Button("Load More", id={'type': 'load-more-button', 'index': symbol}, color='primary', size='sm', className='mb-2')
                )
                news_content.append(html.Div(id={'type': 'additional-news', 'index': symbol}))
        else:
            news_content.append(dbc.Col(html.P(f"No news found for {symbol}."), width=12))

    return    dcc.Loading(id="loading-more-news", type="default", children=[html.Div(news_content)])

                                 

def fetch_analyst_recommendations(symbol):
    ticker = yf.Ticker(symbol)
    rec = ticker.recommendations
    if rec is not None and not rec.empty:
        return rec.tail(10)  # Fetch the latest 10 recommendations
    return pd.DataFrame()  # Return an empty DataFrame if no data



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
        dragmode=False,
    
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
        style_cell={
            'textAlign': 'left', 
            'whiteSpace': 'normal', 
            'height': 'auto',
            'backgroundColor': 'rgba(0, 0, 0, 0)'  # Transparent background for table cells
        },
        style_header={
            'fontWeight': 'bold', 
            'backgroundColor': 'rgba(0, 0, 0, 0)'  # Transparent background for headers
        }

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
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password):
    #     return "Password must contain at least one special character."
    
    # If all conditions are met
    return None


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
                                   style={"text-decoration": "none", "color": "bg-primary"}), 
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
            html.Thead(html.Tr([html.Th("Symbol"), html.Th("Latest"), html.Th("daily %"), html.Th("")])),
            html.Tbody(rows)
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        size="sm",
        className="custom-table"  # Apply the custom class for the table
    )


def get_ticker(company_name):
    yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    params = {"q": company_name, "quotes_count": 3}

    res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
    data = res.json()

    # Extract multiple ticker symbols, if available
    company_codes = [quote['symbol'] for quote in data['quotes'][:3]]
    
    return company_codes


def generate_forecast_data(selected_stocks, horizon):
    """
    Generate forecast data using Prophet for selected stocks and return the forecast results,
    including KPIs for expected price at the end of the forecast horizon.
    """
    forecast_data = {}
    for symbol in selected_stocks:
        try:
            df = yf.download(symbol, period='5y')  # Fetch 5 years of data
            if df.empty:
                raise ValueError(f"No data found for {symbol}")

            df.reset_index(inplace=True)
            # Correct renaming of columns
            df_prophet = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
            model = Prophet(daily_seasonality=True)
            
            model.fit(df_prophet)

            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)

            # KPIs: Extract the expected price at the end of the horizon
            expected_price = forecast['yhat'].iloc[-1]
            expected_upper = forecast['yhat_upper'].iloc[-1]
            expected_lower = forecast['yhat_lower'].iloc[-1]

            forecast_data[symbol] = {
                'historical': df,
                'forecast': forecast,
                'kpi': {
                    'expected_price': expected_price,
                    'upper_bound': expected_upper,
                    'lower_bound': expected_lower
                }
            }

        except Exception as e:
            forecast_data[symbol] = {
                'error': str(e)
            }
    return forecast_data


def generate_confirmation_token(email, server):
    serializer = URLSafeTimedSerializer(server.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirmation-salt')

def confirm_token(token, server, expiration=3600):
    serializer = URLSafeTimedSerializer(server.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirmation-salt', max_age=expiration)
    except Exception as e:
        print(f"Token confirmation error: {e}")  # Add this line to log the error
        return False
    return email


def page_not_found_layout():
    return html.Div([
        html.H1("404: Page Not Found"),
        html.P("Sorry, the page you're looking for doesn't exist."),
        dcc.Link('Go back to Home', href='/')
    ])


def create_blog_post(title, date, author, image_src, content_file, cta_text, cta_href, article_id):
    return html.Div(
        [
            # Blog Article Title
            html.H2(title, id=article_id, className="text-center my-4"),
            html.P(f"By {author} | {date}", className="text-center text-muted mb-4"),

            # Blog Image
            html.Div(
                html.Img(
                    src=image_src, 
                    alt=title, 
                    # loading="lazy" ,
                    className="img-fluid rounded", 
                    style={"width": "auto", "max-width": "350px", "height": "auto"}  # Maintain original width but max 600px
                ),
                className="text-center mb-4"
            ),

            # Blog Content
            html.Div(
                dcc.Markdown(open(f"assets/{content_file}").read()),  # Load content from a Markdown file
                className="p-4",
                style={"line-height": "1.8", "font-size": "18px", "color": "#343a40", "background-color": "#f9f9f9", "border-radius": "10px"}
            ),

            # Call to Action Button
            html.Div(
                dbc.Button(cta_text, href=cta_href, color="primary", className="d-block mx-auto my-4", style={"width": "100%", "max-width": "400px", "font-size": "20px"}),
                className="text-center"
            ),
        ],
        className="blog-post",
    )


