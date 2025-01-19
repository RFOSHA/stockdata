import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Function to compute the price changes and other metrics
def calculate_price_change_metrics(data, current_date):
    # Define time periods (in days)
    periods = {
        '1_week': 7,
        '1_month': 30,
        '2_months': 60,
        '3_months': 90,
        '6_months': 180,
        '1_year': 365
    }

    # Get the latest closing price
    latest_price = data['Close'].iloc[-1]

    # Calculate 1-year (52-week), 6-month, and 3-month highs
    data_last_1_year = data[data['Date'] >= current_date - timedelta(days=365)]
    data_last_6_months = data[data['Date'] >= current_date - timedelta(days=180)]
    data_last_3_months = data[data['Date'] >= current_date - timedelta(days=90)]
    data_last_1_months = data[data['Date'] >= current_date - timedelta(days=30)]
    data_last_1_weeks = data[data['Date'] >= current_date - timedelta(days=7)]

    week_52_high = data_last_1_year['Close'].max()
    month_6_high = data_last_6_months['Close'].max()
    month_3_high = data_last_3_months['Close'].max()
    month_1_high = data_last_1_months['Close'].max()
    week_1_high = data_last_1_weeks['Close'].max()

    # Calculate percentage of the 1-year, 6-month, and 3-month highs
    percentage_of_52_week_high = (latest_price / week_52_high) * 100 if week_52_high > 0 else 0
    percentage_of_6_month_high = (latest_price / month_6_high) * 100 if month_6_high > 0 else 0
    percentage_of_3_month_high = (latest_price / month_3_high) * 100 if month_3_high > 0 else 0
    percentage_of_1_month_high = (latest_price / month_1_high) * 100 if month_1_high > 0 else 0
    percentage_of_1_week_high = (latest_price / week_1_high) * 100 if week_1_high > 0 else 0

    # Prepare a dictionary to hold the price changes and additional metrics
    metrics = {
        'Date': current_date,
        'Current_Price': latest_price,
        '52_Week_High': week_52_high,
        '6_Month_High': month_6_high,
        '3_Month_High': month_3_high,
        'Percentage_of_52_Week_High': percentage_of_52_week_high,
        'Percentage_of_6_Month_High': percentage_of_6_month_high,
        'Percentage_of_3_Month_High': percentage_of_3_month_high,
        'Percentage_of_1_Month_High': percentage_of_1_month_high,
        'Percentage_of_1_Week_High': percentage_of_1_week_high
    }

    # Add the current RSI and MACD indicators to the metrics
    metrics['Current_RSI'] = data['RSI'].iloc[-1]
    metrics['Current_MACD'] = data['MACD'].iloc[-1]
    metrics['Current_Signal_Line'] = data['Signal'].iloc[-1]

    # Calculate price changes for the last week and last month
    for label, days in periods.items():
        period_start = current_date - timedelta(days=days)

        # Get the price at the start of the period (find the nearest available date)
        closest_date = data[data['Date'] <= period_start].iloc[-1]
        period_start_price = closest_date['Close']

        # Calculate price change (without multiplying by 100, keeping it as a decimal)
        price_change = (latest_price - period_start_price) / period_start_price
        metrics[f'Price_Change_{label}'] = price_change

    return metrics

# Function to add P/E Ratio, MFI, and A/D Line to the metrics file
def compute_and_save_metrics(tickers, price_history_filename, metrics_filename, mfstats_filename):
    price_data = pd.read_excel(f"outputFiles/{price_history_filename}")

    all_metrics = []
    current_date = price_data['Date'].max()

    for ticker in tickers:
        print(f"Compute and save metrics for {ticker}")
        ticker_data = price_data[price_data['ticker'] == ticker]

        # Last recorded values for current P/E Ratio, MFI, and A/D Line
        if 'PE_Ratio' not in ticker_data.columns or ticker_data['PE_Ratio'].empty:
            current_pe_ratio = ""
        else:
            current_pe_ratio = ticker_data['PE_Ratio'].iloc[-1]

        current_mfi = ticker_data['MFI'].iloc[-1]
        current_ad_line = ticker_data['AD_Line'].iloc[-1]

        metrics = calculate_price_change_metrics(ticker_data, current_date)
        metrics['ticker'] = ticker
        metrics['Current_PE_Ratio'] = current_pe_ratio
        metrics['Current_MFI'] = current_mfi
        metrics['Current_AD_Line'] = current_ad_line

        all_metrics.append(metrics)

    metrics_df = pd.DataFrame(all_metrics)

    mfstats_df = pd.read_csv(mfstats_filename)
    mfstats_df = mfstats_df[['ticker', 'MF Scoreboard', 'Rec Appearances']]

    combined_df = pd.merge(metrics_df, mfstats_df, on='ticker', how='left')

    # Write the combined data to an Excel file
    combined_df.to_excel(f"outputFiles/{metrics_filename}", sheet_name='Price_Change_Metrics', index=False)
    combined_df.to_excel(f"C:/Users/ryanm/Desktop/Stock_Data/{metrics_filename}", sheet_name='Price_Change_Metrics', index=False)

    print(f"Metrics with MFStats have been written to '{metrics_filename}'")