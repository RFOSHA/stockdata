import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Function to compute the RSI for a given data
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)  # Keep only positive gains
    loss = -delta.where(delta < 0, 0)  # Keep only negative losses, but make them positive
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi
    return data


# Function to calculate MACD
def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    data['EMA_12'] = data['Close'].ewm(span=fast_period, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=slow_period, adjust=False).mean()
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['Signal'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
    return data

# Calculate money flow metrics
def calculate_money_flow_indicators(data):
    # Calculate Money Flow Index (MFI)
    data['Typical_Price'] = (data['High'] + data['Low'] + data['Close']) / 3
    data['Money_Flow'] = data['Typical_Price'] * data['Volume']

    # Calculate Positive and Negative Money Flow based on Typical Price shifts
    data['Positive_Flow'] = data['Money_Flow'].where(data['Typical_Price'] > data['Typical_Price'].shift(1), 0)
    data['Negative_Flow'] = data['Money_Flow'].where(data['Typical_Price'] < data['Typical_Price'].shift(1), 0)

    # Calculate Money Flow Ratio and MFI
    data['Money_Flow_Ratio'] = data['Positive_Flow'].rolling(14).sum() / data['Negative_Flow'].rolling(14).sum()
    data['MFI'] = 100 - (100 / (1 + data['Money_Flow_Ratio']))

    # Calculate On-Balance Volume (OBV)
    obv_change = data['Volume'] * (
                (data['Close'] > data['Close'].shift(1)).astype(int) - (data['Close'] < data['Close'].shift(1)).astype(
            int))
    data['OBV'] = obv_change.cumsum()

    # Calculate Accumulation/Distribution (A/D) Line
    data['AD_Multiplier'] = ((data['Close'] - data['Low']) - (data['High'] - data['Close'])) / (
                data['High'] - data['Low'])
    data['AD_Volume'] = data['AD_Multiplier'] * data['Volume']
    data['AD_Line'] = data['AD_Volume'].cumsum()

    return data

# Function to retrieve TTM EPS using yfinance
def get_ttm_eps(ticker):
    stock = yf.Ticker(ticker)
    try:
        ttm_eps = stock.info['trailingEps']
        return ttm_eps
    except KeyError:
        print(f"TTM EPS not available for {ticker}. Setting EPS to None.")
        return None

def get_price_history_for_two_years(tickers, filename):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=2*365)  # Approximate 2 years
    price_history = {}

    for ticker in tickers:
        print(f"Getting price history for two years for {ticker}")
        # Download the daily price data
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        stock_data = stock_data.reset_index()
        stock_data['ticker'] = ticker

        # Calculate MACD, RSI, and Money Flow Indicators
        stock_data = calculate_macd(stock_data)
        stock_data = calculate_rsi(stock_data)
        stock_data = calculate_money_flow_indicators(stock_data)

        # Get the TTM EPS and calculate daily P/E ratio
        ttm_eps = get_ttm_eps(ticker)
        if ttm_eps:
            stock_data['PE_Ratio'] = stock_data['Close'] / ttm_eps
        else:
            stock_data['PE_Ratio'] = None  # Set as None if EPS is not available

        # Add to the dictionary
        price_history[ticker] = stock_data

    # Combine the price history for all tickers
    combined_data = pd.concat([df for df in price_history.values() if not df.empty and not df.isna().all().all()], ignore_index=True)

    # Write to Excel with P/E ratio included
    combined_data.to_excel(f"outputFiles/{filename}", sheet_name='PriceHistoryWithIndicators', index=False)
    combined_data.to_excel(f"C:/Users/ryanm/Desktop/Stock_Data/{filename}", sheet_name='PriceHistoryWithIndicators',
                         index=False)

    print(f"Daily price history with MACD, RSI, and P/E ratio has been written to '{filename}'")