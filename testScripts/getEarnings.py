import requests
import os
import csv

from configs import tickers

# Alpha Vantage API details
api_key = 'GIDH7JPQUOM12KK1'
# tickers = ['AAPL']  # List of ticker symbols
horizon = '3month'  # Set horizon to 3, 6, or 12 months
output_dir = 'earnings_data'  # Directory to save individual and final CSV files
final_csv_file = 'combined_earnings_data.csv'  # Name of the final combined file

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Create a combined earnings data list
combined_data = [['symbol', 'name', 'reportDate', 'fiscalDateEnding', 'estimate', 'currency']]  # CSV header

# Iterate over each ticker
for ticker in tickers:
    print(f"Processing ticker: {ticker}")
    url = f'https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&symbol={ticker}&horizon={horizon}&apikey={api_key}'

    # Fetch CSV data from Alpha Vantage
    response = requests.get(url)
    if response.status_code == 200:
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')

        # Convert CSV to a list of rows
        earnings_data = list(cr)
        print(earnings_data)

        if len(earnings_data) > 1:
            # Save individual ticker CSV file
            ticker_csv_path = os.path.join(output_dir, f"{ticker}_earnings.csv")
            with open(ticker_csv_path, 'w', newline='') as ticker_csv_file:
                writer = csv.writer(ticker_csv_file)
                writer.writerows(earnings_data)

            print(f"Saved earnings data for {ticker} to {ticker_csv_path}")

            # Add data to the combined data list
            for row in earnings_data[1:]:  # Skip the header row
                combined_data.append([ticker] + row)
        else:
            print(f"No earnings data found for {ticker}.")
    else:
        print(f"Failed to fetch data for {ticker}. Status code: {response.status_code}")

# Save the combined data to a final CSV file
final_csv_path = os.path.join(output_dir, final_csv_file)
with open(final_csv_path, 'w', newline='') as final_csv:
    writer = csv.writer(final_csv)
    writer.writerows(combined_data)

print(f"Final combined CSV file saved to {final_csv_path}")
