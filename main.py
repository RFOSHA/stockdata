import yfinance as yf
import pandas as pd


# Function to extract options data for a given ticker
def get_options_data(ticker):
    stock = yf.Ticker(ticker)

    # Get the list of available expiration dates
    expirations = stock.options
    options_list = []

    for expiration in expirations:
        # Fetching call and put options for the current expiration date
        calls = stock.option_chain(expiration).calls
        puts = stock.option_chain(expiration).puts

        # Remove timezone information from datetime columns if present
        if 'lastTradeDate' in calls.columns:
            calls['lastTradeDate'] = calls['lastTradeDate'].dt.tz_localize(None)
        if 'lastTradeDate' in puts.columns:
            puts['lastTradeDate'] = puts['lastTradeDate'].dt.tz_localize(None)

        # Filter out contracts with both bid and ask being 0
        calls = calls[(calls['bid'] != 0) | (calls['ask'] != 0)]
        puts = puts[(puts['bid'] != 0) | (puts['ask'] != 0)]

        # Add columns for 'type' (call/put), 'expiration', and 'ticker'
        calls['type'] = 'call'
        puts['type'] = 'put'
        calls['expiration'] = expiration
        puts['expiration'] = expiration
        calls['ticker'] = ticker
        puts['ticker'] = ticker

        # Append both calls and puts to the options_list
        options_list.append(calls)
        options_list.append(puts)

    # Combine all options into one DataFrame
    options_data = pd.concat(options_list, ignore_index=True)

    return options_data


# Fetch options data for AAPL and GOOGL
aapl_options = get_options_data("AAPL")
googl_options = get_options_data("GOOGL")

# Combine AAPL and GOOGL options data
combined_options_data = pd.concat([aapl_options, googl_options], ignore_index=True)

# Write the combined data to an Excel file in one tab
combined_options_data.to_excel('options_data_combined.xlsx', sheet_name='OptionsData', index=False)

print("Options data for AAPL and GOOGL has been written to 'options_data_combined.xlsx'")
