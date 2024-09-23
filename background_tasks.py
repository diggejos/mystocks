from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os
from yfinance.exceptions import YFException

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
    except YFException as e:
        print(f"Failed to fetch data for {symbol}: {e}")
        return None

# Function to get stock list (S&P 500, etc.)
def get_stock_list():
    # S&P 500
    url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp500_tables = pd.read_html(url_sp500)
    sp500_table = sp500_tables[0]
    sp500_tickers = sp500_table['Symbol'].tolist()

    # FTSE 100
    #url_ftse100 = 'https://en.wikipedia.org/wiki/FTSE_100_Index'
    #ftse100_tables = pd.read_html(url_ftse100)
    #ftse100_table = ftse100_tables[4]  # Table 4 typically contains the tickers
    #ftse100_tickers = ftse100_table['Ticker'].tolist()

    # DAX (Germany)
    #url_dax = 'https://en.wikipedia.org/wiki/DAX'
    #dax_tables = pd.read_html(url_dax)
    #dax_table = dax_tables[4]  # Table 2 typically contains the tickers
    #dax_tickers = dax_table['Ticker'].tolist()
    
    #url_asx = 'https://en.wikipedia.org/wiki/S%26P/ASX_200'
    #asx_tables = pd.read_html(url_asx)
    #asx_table = asx_tables[2]  # First table typically contains the tickers
    #asx_tickers = asx_table['Code'].tolist()
    
    # Sensex (India)
    #url_sensex = 'https://en.wikipedia.org/wiki/BSE_SENSEX'
    #sensex_tables = pd.read_html(url_sensex)
    #sensex_table = sensex_tables[1]  # Table 2 typically contains the tickers
    #sensex_tickers = sensex_table['Symbol'].tolist()


    # SMI (Swiss Market Index)
    #url_smi = 'https://en.wikipedia.org/wiki/Swiss_Market_Index'
    #smi_tables = pd.read_html(url_smi)
    #smi_table = smi_tables[2]  # Table 4 typically contains the tickers
    #smi_tickers = smi_table['Ticker'].tolist()

    # Combine all tickers
    combined_tickers = sp500_tickers 

    # Remove duplicates using a set
    unique_tickers = list(set(combined_tickers))

    print(f"Number of unique tickers: {len(unique_tickers)}")  # To verify uniqueness
    return unique_tickers

# Store top 20 stocks in the database
def store_top_20_stocks(stock_symbols):
    with app.app_context():  # Use Flask app context
        kpi_data = []
        batch_id = int(datetime.utcnow().timestamp())  # Create a unique batch ID

        for symbol in stock_symbols:
            kpis = fetch_kpi_for_stock(symbol)
            if kpis and kpis['P/E Ratio'] is not None:
                kpis['Symbol'] = symbol
                kpi_data.append(kpis)
            else:
                print(f"Skipping {symbol} due to incomplete KPI data.")

        df = pd.DataFrame(kpi_data)

        # Filter and store the top 20 for each risk tolerance
        def filter_and_store(df, risk_tolerance, beta_range):
            if risk_tolerance == "low":
                filtered = df[df['Beta'] < 1]
            elif risk_tolerance == "medium":
                filtered = df[(df['Beta'] >= 1) & (df['Beta'] <= 2)]
            else:
                filtered = df[df['Beta'] > 2]

            filtered.loc[:, 'Buy'] = (
                (filtered['P/E Ratio'] < 30) | filtered['P/E Ratio'].isnull()
                & (filtered['ROE'] > 0.10)
                & (filtered['Debt-to-Equity'] < 2)
                & (filtered['Price Momentum'] > 0)
            )

            top_20 = filtered[filtered['Buy'] == True].nlargest(20, 'Price Momentum')

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
    scheduler = BackgroundScheduler()

    # First-time update
    print("Updating stock data for the first time...")
    update_stock_data()

    # Set up the scheduler for weekly updates
    scheduler.add_job(func=update_stock_data, trigger="interval", weeks=1)

    # Start the scheduler and allow it to finish the task before exiting
    scheduler.start()
    scheduler.shutdown(wait=True)

