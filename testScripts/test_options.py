import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

stock = yf.Ticker('TSLA')

# Fetch the current stock price
# print(stock.history)
current_price = stock.history(period='1d')['Close'].iloc[-1]
print(current_price)

# Define +/- 20% bounds for the strike price
lower_bound = current_price * 0.80
upper_bound = current_price * 1.20

# Define the three-week boundary from today
today = datetime.today()
three_weeks_from_now = today + timedelta(weeks=3)