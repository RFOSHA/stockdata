import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Initialize the ticker
ticker = 'AAPL'
stock = yf.Ticker(ticker)

# Fetch earnings dates and remove timezone information from the index
earnings_dates = stock.earnings_dates
print(earnings_dates)

if earnings_dates is not None:

    earnings_dates.index = earnings_dates.index.tz_localize(None)  # Remove timezone

    print(earnings_dates)
    print("####################################")

    # Filter for dates after today and select the earliest upcoming date
    upcoming_dates = earnings_dates[earnings_dates.index > datetime.now()]

    if not upcoming_dates.empty:
        next_earnings_date = upcoming_dates.index.min()
    else:
        next_earnings_date = earnings_dates.index.max()  # Use the most recent earnings date

    print(upcoming_dates)
    print("####################################")
    print(next_earnings_date)
    print("####################################")


# # Retrieve quarterly income statements and balance sheets
# quarterly_income = stock.income_stmt
# # print(quarterly_income)
#
# quarterly_balance_sheet = stock.balance_sheet
# # print(quarterly_balance_sheet)
#
# # Extract relevant columns (Net Income and Shares Outstanding)
#
# # Ensure we only keep 'Net Income' from income statements
# earnings_df = quarterly_income.loc['Net Income'].to_frame(name='Net Income')
# print(earnings_df)
#
# # Get shares outstanding (using balance sheet common stock data)
# shares_outstanding_df = quarterly_balance_sheet.loc['Common Stock'].to_frame(name='Shares Outstanding')
#
#
# # Align the indices and rename them to avoid overlap
# earnings_df.index.name = 'Date'
# shares_outstanding_df.index.name = 'Date'
# print(earnings_df)
# print(shares_outstanding_df)
#
# # Combine net income and shares outstanding data by joining on date index
# combined_df = earnings_df.join(shares_outstanding_df, how='inner', rsuffix='_shares')
# print(combined_df)
#
# # Calculate EPS as Net Income / Shares Outstanding
# combined_df['EPS'] = combined_df['Net Income'] / combined_df['Shares Outstanding']
#
# # Calculate TTM EPS (trailing 12-month EPS) by rolling sum of the last 4 quarters' EPS
# combined_df['TTM_EPS'] = combined_df['EPS'].rolling(window=4).sum()
#
# print(combined_df[['Net Income', 'Shares Outstanding', 'EPS', 'TTM_EPS']])
