from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from app import db, StockKPI, app  # Import necessary pieces from app
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv  # Include dotenv to load environment variables
import os

# Load environment variables from .env
load_dotenv()

# Set the database URI from the environment variable
db_uri = os.getenv('DATABASE_URL')

# Ensure that the database URI is set in your app's configuration
app.server.config['SQLALCHEMY_DATABASE_URI'] = db_uri

# Function to fetch KPI data
def fetch_kpi_for_stock(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    kpis = {
        'P/E Ratio': info.get('trailingPE'),
        'P/B Ratio': info.get('priceToBook'),
        'Beta': info.get('beta'),
        'Dividend Yield': info.get('dividendYield'),
        'Market Cap': info.get('marketCap'),
        'ROE': info.get('returnOnEquity'),
        'Debt-to-Equity': info.get('debtToEquity'),
        'Price Momentum': info.get('fiftyTwoWeekHigh') - info.get('fiftyTwoWeekLow') if info.get('fiftyTwoWeekHigh') and info.get('fiftyTwoWeekLow') else None
    }
    print(f"Fetched KPIs for {symbol}: {kpis}")
    return kpis

# Fetch the list of stocks
def get_stock_list():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    sp500_table = tables[0]
    sp500_tickers = sp500_table['Symbol'].tolist()
    return sp500_tickers

# Store top 20 stocks in the database
def store_top_20_stocks(stock_symbols):
    with app.server.app_context():  # Use app.server.app_context() to get Flask app context
        kpi_data = []
        
        for symbol in stock_symbols:
            kpis = fetch_kpi_for_stock(symbol)
            kpis['Symbol'] = symbol
            kpi_data.append(kpis)

        df = pd.DataFrame(kpi_data)

        # Filter and store the top 20 for each risk tolerance
        def filter_and_store(df, risk_tolerance, beta_range):
            if risk_tolerance == "low":
                filtered = df[df['Beta'] < 1]  # Low risk
            elif risk_tolerance == "medium":
                filtered = df[(df['Beta'] >= 1) & (df['Beta'] <= 2)]  # Medium risk
            else:
                filtered = df[df['Beta'] > 2]  # High risk

            # Apply the Buy criteria
            filtered.loc[:, 'Buy'] = (
                (filtered['P/E Ratio'] < 30) | filtered['P/E Ratio'].isnull()
                & (filtered['ROE'] > 0.10)
                & (filtered['Debt-to-Equity'] < 2)
                & (filtered['Price Momentum'] > 0)
            )

            # Get the top 20 stocks by momentum
            top_20 = filtered[filtered['Buy'] == True].nlargest(20, 'Price Momentum')

            # Clear old records for this risk tolerance
            StockKPI.query.filter_by(risk_tolerance=risk_tolerance).delete()

            for _, row in top_20.iterrows():
                stock_kpi = StockKPI(
                    symbol=row['Symbol'],
                    pe_ratio=row['P/E Ratio'],
                    pb_ratio=row['P/B Ratio'],
                    beta=row['Beta'],
                    dividend_yield=row['Dividend Yield'],
                    market_cap=row['Market Cap'],
                    roe=row['ROE'],
                    debt_to_equity=row['Debt-to-Equity'],
                    price_momentum=row['Price Momentum'],
                    risk_tolerance=risk_tolerance,
                    last_updated=datetime.utcnow()
                )
                db.session.add(stock_kpi)
            
            db.session.commit()

        # Run the filtering for each risk tolerance
        filter_and_store(df, "low", (None, 1))
        filter_and_store(df, "medium", (1, 2))
        filter_and_store(df, "high", (2, None))

# Scheduled job to update stock data weekly
def update_stock_data():
    stock_symbols = get_stock_list()
    store_top_20_stocks(stock_symbols)
    print(f"Stock data updated at {datetime.utcnow()}.")

# Initialize and start the scheduler
if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    # First-time update
    print("Updating stock data for the first time...")
    update_stock_data()

    # Set up the scheduler for weekly updates
    scheduler.add_job(func=update_stock_data, trigger="interval", weeks=1)
    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down the scheduler...")
        scheduler.shutdown()
