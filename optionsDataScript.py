# Generate the price history and indicators for a list of tickers
from configs import tickers, options_output_path, combined_options_filename
from functions.get_options_data import get_options_data, compute_yield_and_annualized_return
import pandas as pd

# Initialize an empty list to store options data for all tickers
all_options_data = []

df_earnings = pd.read_csv("inputFiles/earnings.csv")

# Iterate over each ticker to retrieve and compute options data
for ticker in tickers:
    print(ticker)

    # Filter the DataFrame for the given ticker
    ticker_row = df_earnings[df_earnings['ticker'] == ticker]

    # Check if the ticker exists in the DataFrame
    if not ticker_row.empty:
        earnings_date = ticker_row.iloc[0]['earnings']  # Get the 'earnings' value
    else:
        earnings_date = None  # Return None if the ticker is not found

    options_data = get_options_data(ticker, earnings_date)
    if options_data is not None and not options_data.empty:
        options_data = compute_yield_and_annualized_return(options_data)
        all_options_data.append(options_data)

# Combine options data for all tickers into a single DataFrame
combined_options = pd.concat(all_options_data, ignore_index=True)

# Write the combined options data to an Excel file
combined_options.to_excel(combined_options_filename, sheet_name='OptionsData', index=False)
combined_options.to_excel(options_output_path, sheet_name='OptionsData', index=False)

print(f"Combined options data for all tickers, with yield and annualized return, has been written to '{combined_options_filename}' at '{options_output_path}'")