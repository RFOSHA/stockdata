import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Used to get the latest price from the price history file if the latest close is not returned from Yahoo
def get_price_from_file(ticker):
    try:
        # Load the local Excel file
        filepath = "../outputFiles/price_history_with_indicators.xlsx"
        df = pd.read_excel(filepath)

        # Ensure the required columns exist
        if not {'Ticker', 'Date', 'Close'}.issubset(df.columns):
            raise ValueError(f"The file {filepath} must contain 'Ticker', 'Date', and 'Close' columns.")

        # Filter the DataFrame for the given ticker
        ticker_data = df[df['Ticker'] == ticker]
        if ticker_data.empty:
            print(f"No data found in local file for {ticker}.")
            return None  # Default value if no data is available

        # Find the most recent Close price
        most_recent_row = ticker_data.sort_values(by='Date', ascending=False).iloc[0]
        return most_recent_row['Close']
    except FileNotFoundError:
        print(f"File {filepath} not found. Cannot fetch data for {ticker}.")
        return None
    except Exception as e:
        print(f"Error processing local file for {ticker}: {e}")
        return None

# def get_earnings_date(ticker):
#     """
#     Fetches the first upcoming earnings date for a given ticker from Yahoo Finance.
#     """
#     url = f"https://finance.yahoo.com/quote/{ticker}/"
#     response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
#
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, "html.parser")
#         container = soup.find("div", {"data-testid": "quote-statistics"})
#
#         if container:
#             items = container.find_all("li")
#             for item in items:
#                 label = item.find("span", class_="label")
#                 value = item.find("span", class_="value")
#                 if label and label.get_text(strip=True) == "Earnings Date":
#                     # Extract the first date before the hyphen
#                     earnings_date_value = value.get_text(strip=True)
#                     first_earnings_date = earnings_date_value.split('-')[0].strip()
#                     return first_earnings_date
#     return None

# Function to retrieve and process options data for any ticker
def get_options_data(ticker, next_earnings_date):
    stock = yf.Ticker(ticker)

    # Fetch the current stock price
    if stock.history().empty:
        current_price = get_price_from_file(ticker)
        print(f"Close price not available for {ticker}. The history DataFrame is empty.")
    else:
        current_price = stock.history(period='5d')['Close'].iloc[-1]

    # Define +/- 20% bounds for the strike price
    lower_bound = current_price * 0.80
    upper_bound = current_price * 1.20

    # Define the three-week boundary from today
    today = datetime.today()
    three_weeks_from_now = today + timedelta(weeks=3)

    # Filter expiration dates to within the next three weeks
    expirations = [date for date in stock.options if datetime.strptime(date, '%Y-%m-%d') <= three_weeks_from_now]

    options_data_list = []

    for expiration in expirations:
        # Fetch both calls and puts options for the expiration date
        option_chain = stock.option_chain(expiration)
        options_data = pd.concat([option_chain.calls, option_chain.puts], ignore_index=True)

        # Add columns for 'type', 'expiration', 'ticker', 'Next_Earnings_Date', and 'Current_Price'
        options_data['type'] = ['call'] * len(option_chain.calls) + ['put'] * len(option_chain.puts)
        options_data['expiration'] = expiration
        options_data['ticker'] = ticker
        options_data['Next_Earnings_Date'] = next_earnings_date
        options_data['Current_Price'] = current_price

        # Remove timezone information if present in 'lastTradeDate'
        if 'lastTradeDate' in options_data.columns:
            options_data['lastTradeDate'] = options_data['lastTradeDate'].dt.tz_localize(None)

        # Apply additional filters
        seven_days_ago = today - timedelta(days=7)
        options_data = options_data[
            (options_data['volume'] > 10) &
            (options_data['strike'] >= lower_bound) & (options_data['strike'] <= upper_bound) &
            (options_data['impliedVolatility'] >= 0.0001) &  # Filter by implied volatility
            (options_data['lastTradeDate'] >= seven_days_ago)  # Filter by last trade date
        ]

        # Calculate percent difference from strike price
        options_data['Percent_Diff_from_Strike'] = (options_data['strike'] - current_price) / current_price

        # Ensure both 'Next_Earnings_Date' and 'expiration' are in date format
        options_data['Next_Earnings_Date_Format'] = pd.to_datetime(options_data['Next_Earnings_Date'], errors='coerce').dt.date
        options_data['expiration'] = pd.to_datetime(options_data['expiration'], errors='coerce').dt.date


        # Create the flag 'Earnings_Before_Expiration' with an additional check for NaT
        options_data['Earnings_Before_Expiration'] = options_data.apply(
            lambda row: "Y" if pd.notna(row['Next_Earnings_Date_Format']) and row['Next_Earnings_Date_Format'] < row[
                'expiration'] else "N",
            axis=1
        )

        # Append the processed options data to the list
        options_data_list.append(options_data)

    # Combine all options data into a single DataFrame
    if not options_data_list:
        print(f"No options data for {ticker}")
    else:
        final_options_data = pd.concat(options_data_list, ignore_index=True)
        return final_options_data


# Function to compute yield and annualized return for options data
def compute_yield_and_annualized_return(options_data):
    today = datetime.today()

    # Convert expiration column to datetime if not already
    options_data['expiration'] = pd.to_datetime(options_data['expiration'], errors='coerce')

    # Ensure lastPrice and strike are properly converted to numeric values
    options_data['lastPrice'] = pd.to_numeric(options_data['lastPrice'], errors='coerce')
    options_data['strike'] = pd.to_numeric(options_data['strike'], errors='coerce')

    # Compute yield as lastPrice / strike, avoid division by zero
    options_data['yield'] = options_data.apply(
        lambda row: row['lastPrice'] / row['strike'] if row['strike'] > 0 else 0, axis=1
    )

    # Calculate the number of days until expiration
    options_data['days_to_expiration'] = (((options_data['expiration'] - today).dt.days) + 1)

    # Filter out any options that have expired or have no days left
    options_data = options_data[options_data['days_to_expiration'] > 0]

    # After filtering out expired options, create a copy to avoid the SettingWithCopyWarning
    options_data = options_data[options_data['days_to_expiration'] > 0].copy()

    # Compute annualized return: (1 + yield) ^ (365 / days_to_expiration) - 1
    options_data.loc[:, 'annualized_return'] = options_data.apply(
        lambda row: ((1 + row['yield']) ** (365 / row['days_to_expiration']) - 1) if row['days_to_expiration'] > 0 else 0,axis=1)

    # Filter out options with an annualized return of less than 10%
    options_data = options_data[options_data['annualized_return'] >= 0.10]

    return options_data