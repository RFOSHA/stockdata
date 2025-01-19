import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime


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
                    first_earnings_date = earnings_date_value.split('-')[0].strip()
                    return first_earnings_date
    return None


def update_earnings_dates(csv_path):
    """
    Reads a CSV file with ticker and earnings columns, updates the earnings column
    if it's empty or the date is in the past.
    """
    # Load the CSV into a DataFrame
    df = pd.read_csv(csv_path)

    # Ensure the columns are present
    if 'ticker' not in df.columns or 'earnings' not in df.columns:
        raise ValueError("CSV must contain 'ticker' and 'earnings' columns")

    for index, row in df.iterrows():
        ticker = row['ticker']
        print(ticker)
        earnings_date = row['earnings']

        if pd.isna(earnings_date) or earnings_date.strip() == "":
            # Fetch earnings date if missing
            new_earnings_date = get_earnings_date(ticker)
            if new_earnings_date:
                df.at[index, 'earnings'] = new_earnings_date
        else:
            try:
                # Convert earnings date to datetime for comparison
                earnings_datetime = datetime.strptime(earnings_date, '%b %d, %Y')
                if earnings_datetime < datetime.now():
                    # Update past earnings date
                    new_earnings_date = get_earnings_date(ticker)
                    if new_earnings_date:
                        df.at[index, 'earnings'] = new_earnings_date
            except ValueError:
                # Handle incorrect date format
                print(f"Invalid date format for ticker {ticker}: {earnings_date}")

    # Save the updated DataFrame back to CSV
    df.to_csv(csv_path, index=False)
    print("Earnings dates updated successfully.")

csv_path = "inputFiles/earnings.csv"
update_earnings_dates(csv_path)