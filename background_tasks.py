from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os
from yfinance.exceptions import YFException
from sqlalchemy.exc import SQLAlchemyError
import time

# Load environment variables
load_dotenv()

# Database URI from environment variable
db_uri = os.getenv('DATABASE_URL')

# Fix the URL format if needed (Render uses a `postgres://` URI)
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

# Initialize a minimal Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the StockKPI model
class StockKPI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    pe_ratio = db.Column(db.Float)
    pb_ratio = db.Column(db.Float)
    beta = db.Column(db.Float)
    dividend_yield = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    roe = db.Column(db.Float)
    debt_to_equity = db.Column(db.Float)
    price_momentum = db.Column(db.Float)
    risk_tolerance = db.Column(db.String(10), nullable=False)  # "low", "medium", or "high"
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    batch_id = db.Column(db.Integer)

# Function to fetch KPI data
def fetch_kpi_for_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            print(f"No data found for {symbol}")
            return None

        # Define KPIs and ensure numeric conversion, defaulting to None if conversion fails
        kpis = {
            'P/E Ratio': pd.to_numeric(info.get('trailingPE'), errors='coerce'),
            'P/B Ratio': pd.to_numeric(info.get('priceToBook'), errors='coerce'),
            'Beta': pd.to_numeric(info.get('beta'), errors='coerce'),
            'Dividend Yield': pd.to_numeric(info.get('dividendYield'), errors='coerce'),
            'Market Cap': pd.to_numeric(info.get('marketCap'), errors='coerce'),
            'ROE': pd.to_numeric(info.get('returnOnEquity'), errors='coerce'),
            'Debt-to-Equity': pd.to_numeric(info.get('debtToEquity'), errors='coerce'),
            'Price Momentum': (
                pd.to_numeric(info.get('fiftyTwoWeekHigh'), errors='coerce') - 
                pd.to_numeric(info.get('fiftyTwoWeekLow'), errors='coerce')
            ) if info.get('fiftyTwoWeekHigh') and info.get('fiftyTwoWeekLow') else None
        }

        print(f"Fetched KPIs for {symbol}: {kpis}")
        return kpis
    except YFException as e:
        print(f"Failed to fetch data for {symbol}: {e}")
        return None

def get_stock_list():
    # S&P 500
    url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp500_tables = pd.read_html(url_sp500)
    sp500_table = sp500_tables[0]
    sp500_tickers = sp500_table['Symbol'].tolist()
    return list(set(sp500_tickers))  # Remove duplicates

def store_top_20_stocks(stock_symbols):
    with app.app_context():  # Use app.app_context() instead of app.server.app_context()
        kpi_data = []
        batch_id = int(datetime.utcnow().timestamp())

        for symbol in stock_symbols:
            kpis = fetch_kpi_for_stock(symbol)
            if kpis and kpis['P/E Ratio'] is not None:
                kpis['Symbol'] = symbol
                kpi_data.append(kpis)
            else:
                print(f"Skipping {symbol} due to incomplete KPI data.")
        
        df = pd.DataFrame(kpi_data)

        # Ensure all columns are numeric for filtering
        numeric_columns = ['P/E Ratio', 'P/B Ratio', 'Beta', 'Dividend Yield', 'ROE', 'Debt-to-Equity', 'Price Momentum']
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

        # Filter and store the top 20 for each risk tolerance
        def filter_and_store(df, risk_tolerance):
            if risk_tolerance == "low":
                filtered = df[df['Beta'] < 1]
                filtered['Buy'] = (
                    ((filtered['P/E Ratio'] < 25) | filtered['P/E Ratio'].isnull()) &
                    (filtered['ROE'] > 0.08) &
                    (filtered['Debt-to-Equity'] < 1.5) &
                    (filtered['Price Momentum'] > 0)
                )
            elif risk_tolerance == "medium":
                filtered = df[(df['Beta'] >= 1) & (df['Beta'] <= 2)]
                filtered['Buy'] = (
                    ((filtered['P/E Ratio'] < 40) | filtered['P/E Ratio'].isnull()) &
                    (filtered['ROE'] > 0.05) &
                    (filtered['Debt-to-Equity'] < 3) &
                    (filtered['Price Momentum'] > 0)
                )
            else:
                filtered = df[df['Beta'] > 2]
                filtered['Buy'] = (
                    ((filtered['P/E Ratio'] < 60) | filtered['P/E Ratio'].isnull()) &
                    (filtered['ROE'] > 0) &
                    (filtered['Debt-to-Equity'] < 5) &
                    (filtered['Price Momentum'] > 0)
                )

            # Use alternative scoring approach
            filtered['Score'] = (
                (filtered['P/E Ratio'].apply(lambda x: 1 if x < 30 else 0.5 if x < 40 else 0) * 0.3) +
                (filtered['ROE'].apply(lambda x: 1 if x > 0.10 else 0.5 if x > 0.05 else 0) * 0.4) +
                (filtered['Debt-to-Equity'].apply(lambda x: 1 if x < 2 else 0.5 if x < 3 else 0) * 0.2) +
                (filtered['Price Momentum'].apply(lambda x: 1 if x > 0 else 0) * 0.1)
            )

            # Select top 20 by highest score if not enough with "Buy" criteria
            top_20 = filtered[filtered['Buy'] == True].nlargest(20, 'Price Momentum')
            if len(top_20) < 20:
                top_20 = filtered.nlargest(20, 'Score')

            # Clear old records if more than 5 batches exist
            existing_batches = db.session.query(StockKPI.batch_id).distinct().count()
            if existing_batches >= 5:
                oldest_batch_id = db.session.query(StockKPI.batch_id).order_by(StockKPI.batch_id).first()[0]
                StockKPI.query.filter_by(batch_id=oldest_batch_id).delete()

            # Insert the top 20 stocks into the database with the new batch ID
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
                    last_updated=datetime.utcnow(),
                    batch_id=batch_id
                )
                db.session.add(stock_kpi)

            db.session.commit()

        # Run the filtering for each risk tolerance
        filter_and_store(df, "low")
        filter_and_store(df, "medium")
        filter_and_store(df, "high")

# Scheduled job to update stock data weekly
def update_stock_data():
    stock_symbols = get_stock_list()
    store_top_20_stocks(stock_symbols)
    print(f"Stock data updated at {datetime.utcnow()}.")

# Initialize and start the scheduler
if __name__ == "__main__":
    scheduler = BackgroundScheduler()

    # First-time update
    print("Updating stock data for the first time...")
    update_stock_data()

    # Set up the scheduler for weekly updates
    scheduler.add_job(func=update_stock_data, trigger="interval", weeks=1)

    # Start the scheduler
    scheduler.start()

    try:
        # Keep the script running
        while True:
            time.sleep(60)  # Sleep for 60 seconds between checks
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
