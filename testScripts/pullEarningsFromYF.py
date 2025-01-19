# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
#
# # URL of the Yahoo Finance page
# url = "https://finance.yahoo.com/quote/MSFT/"
#
# # Send an HTTP GET request to the URL
# response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
#
# # Check if the request was successful
# if response.status_code == 200:
#     # Parse the HTML content of the page
#     soup = BeautifulSoup(response.text, "html.parser")
#
#     # Locate the container with the data-testid="quote-statistics"
#     container = soup.find("div", {"data-testid": "quote-statistics"})
#
#     if container:
#         # Extract all <li> items within the container
#         items = container.find_all("li")
#
#         # Prepare data for the DataFrame
#         data = []
#         for item in items:
#             label = item.find("span", class_="label")
#             value = item.find("span", class_="value")
#
#             if label and value:
#                 data.append((label.get_text(strip=True), value.get_text(strip=True)))
#
#         # Create a DataFrame from the extracted data
#         df = pd.DataFrame(data, columns=["Metric", "Value"])
#         print(df)
#     else:
#         print("Could not find the quote-statistics container.")
# else:
#     print(f"Failed to retrieve the page. HTTP Status Code: {response.status_code}")
#
# # Extract the "Earnings Date" value from the DataFrame
# earnings_date_value = df.loc[df['Metric'] == 'Earnings Date', 'Value'].values[0]
#
# # Split the value by the hyphen and take the first part, stripping any extra whitespace
# first_earnings_date = earnings_date_value.split('-')[0].strip()
#
# print("First Earnings Date:", first_earnings_date)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv


def get_earnings_date(ticker):
    """
    Fetches the first upcoming earnings date for a given ticker from Yahoo Finance.
    """
    url = f"https://finance.yahoo.com/quote/{ticker}/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div", {"data-testid": "quote-statistics"})

        if container:
            items = container.find_all("li")
            for item in items:
                label = item.find("span", class_="label")
                value = item.find("span", class_="value")
                if label and label.get_text(strip=True) == "Earnings Date":
                    # Extract the first date before the hyphen
                    earnings_date_value = value.get_text(strip=True)
                    print(earnings_date_value)
                    first_earnings_date = earnings_date_value.split('-')[0].strip()
                    print(first_earnings_date)
                    return first_earnings_date
    return "N/A"


# List of tickers to fetch data for
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]

# Prepare the data for the CSV
results = []
for ticker in tickers:
    earnings_date = get_earnings_date(ticker)
    print(earnings_date)
    results.append({"Ticker": ticker, "Earnings Date": earnings_date})
    print(f"Fetched earnings date for {ticker}: {earnings_date}")

# Create a DataFrame from the results
results_df = pd.DataFrame(results)
# print(results_df)
#
# # Save the DataFrame to a CSV file
# results_df.to_csv("earnings_dates.csv", index=False, quoting=csv.QUOTE_MINIMAL)
# print("Earnings dates saved to earnings_dates.csv")
