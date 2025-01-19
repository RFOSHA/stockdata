import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

ticker = 'TPL'

stock = yf.Ticker(ticker)
print(stock)

# Fetch the current stock price
print(stock.history())
print(stock.history(period='1d'))
if stock.history(period='1d')['Close'].empty:
    #current_price = get_price_from_file(ticker)
    print(f"Close price not available for {ticker}. The history DataFrame is empty.")
else:
    current_price = stock.history(period='1d')['Close'].iloc[-1]