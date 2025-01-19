# import yfinance as yf
# import pandas as pd
# from datetime import datetime, timedelta
# import requests
# from bs4 import BeautifulSoup
#
#
#
# # Function to retrieve the next earnings date for a given ticker
# # def get_next_earnings_date(ticker):
# #     stock = yf.Ticker(ticker)
# #     try:
# #         earnings_dates = stock.earnings_dates
# #         earnings_dates.index = earnings_dates.index.tz_localize(None)  # Remove timezone
# #
# #         # Filter for dates after today and select the earliest upcoming date
# #         upcoming_dates = earnings_dates[earnings_dates.index > datetime.now()]
# #
# #         if not upcoming_dates.empty:
# #             next_earnings_date = upcoming_dates.index.min()
# #         else:
# #             next_earnings_date = earnings_dates.index.max()  # Use the most recent earnings date
# #         return next_earnings_date.date()
# #     except (IndexError, KeyError, ValueError, AttributeError):
# #         return None
#
# # Function to retrieve earnings date from the Yahoo website
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
#     return "N/A"
#
# # Function to retrieve and process options data for any ticker
# def get_options_data(ticker):
#     stock = yf.Ticker(ticker)
#
#     # Fetch the current stock price
#     current_price = stock.history(period='1d')['Close'].iloc[-1]
#
#     # Define +/- 20% bounds for the strike price
#     lower_bound = current_price * 0.80
#     upper_bound = current_price * 1.20
#
#     # Define the three-week boundary from today
#     today = datetime.today()
#     three_weeks_from_now = today + timedelta(weeks=3)
#
#     # Filter expiration dates to within the next three weeks
#     expirations = [date for date in stock.options if datetime.strptime(date, '%Y-%m-%d') <= three_weeks_from_now]
#
#     # Fetch the next earnings date for the ticker
#     next_earnings_date = get_earnings_date(ticker)
#
#     options_data_list = []
#
#     for expiration in expirations:
#         # Fetch both calls and puts options for the expiration date
#         option_chain = stock.option_chain(expiration)
#         options_data = pd.concat([option_chain.calls, option_chain.puts], ignore_index=True)
#
#         # Add columns for 'type', 'expiration', 'ticker', 'Next_Earnings_Date', and 'Current_Price'
#         options_data['type'] = ['call'] * len(option_chain.calls) + ['put'] * len(option_chain.puts)
#         options_data['expiration'] = expiration
#         options_data['ticker'] = ticker
#         options_data['Next_Earnings_Date'] = next_earnings_date
#         options_data['Current_Price'] = current_price
#
#         # Remove timezone information if present in 'lastTradeDate'
#         if 'lastTradeDate' in options_data.columns:
#             options_data['lastTradeDate'] = options_data['lastTradeDate'].dt.tz_localize(None)
#
#         # Apply additional filters
#         seven_days_ago = today - timedelta(days=7)
#         options_data = options_data[
#             (options_data['volume'] > 10) &
#             (options_data['strike'] >= lower_bound) & (options_data['strike'] <= upper_bound) &
#             (options_data['impliedVolatility'] >= 0.0001) &  # Filter by implied volatility
#             (options_data['lastTradeDate'] >= seven_days_ago)  # Filter by last trade date
#         ]
#
#         # Calculate percent difference from strike price
#         options_data['Percent_Diff_from_Strike'] = (options_data['strike'] - current_price) / current_price
#
#         # Ensure both 'Next_Earnings_Date' and 'expiration' are in date format
#         options_data['Next_Earnings_Date'] = pd.to_datetime(options_data['Next_Earnings_Date'], errors='coerce').dt.date
#         options_data['expiration'] = pd.to_datetime(options_data['expiration'], errors='coerce').dt.date
#
#         # Create the flag 'Earnings_Before_Expiration' with an additional check for NaT
#         options_data['Earnings_Before_Expiration'] = options_data.apply(
#             lambda row: "Y" if pd.notna(row['Next_Earnings_Date']) and row['Next_Earnings_Date'] < row[
#                 'expiration'] else "N",
#             axis=1
#         )
#
#         # Append the processed options data to the list
#         options_data_list.append(options_data)
#
#     # Combine all options data into a single DataFrame
#     if not options_data_list:
#         print(f"No options data for {ticker}")
#     else:
#         final_options_data = pd.concat(options_data_list, ignore_index=True)
#         return final_options_data
#
#
# # Function to compute yield and annualized return for options data
# def compute_yield_and_annualized_return(options_data):
#     today = datetime.today()
#
#     # Convert expiration column to datetime if not already
#     options_data['expiration'] = pd.to_datetime(options_data['expiration'], errors='coerce')
#
#     # Ensure lastPrice and strike are properly converted to numeric values
#     options_data['lastPrice'] = pd.to_numeric(options_data['lastPrice'], errors='coerce')
#     options_data['strike'] = pd.to_numeric(options_data['strike'], errors='coerce')
#
#     # Compute yield as lastPrice / strike, avoid division by zero
#     options_data['yield'] = options_data.apply(
#         lambda row: row['lastPrice'] / row['strike'] if row['strike'] > 0 else 0, axis=1
#     )
#
#     # Calculate the number of days until expiration
#     options_data['days_to_expiration'] = (((options_data['expiration'] - today).dt.days) + 1)
#
#     # Filter out any options that have expired or have no days left
#     options_data = options_data[options_data['days_to_expiration'] > 0]
#
#     # After filtering out expired options, create a copy to avoid the SettingWithCopyWarning
#     options_data = options_data[options_data['days_to_expiration'] > 0].copy()
#
#     # Compute annualized return: (1 + yield) ^ (365 / days_to_expiration) - 1
#     options_data.loc[:, 'annualized_return'] = options_data.apply(
#         lambda row: ((1 + row['yield']) ** (365 / row['days_to_expiration']) - 1) if row['days_to_expiration'] > 0 else 0,axis=1)
#
#     # Filter out options with an annualized return of less than 10%
#     options_data = options_data[options_data['annualized_return'] >= 0.10]
#
#     return options_data
#
# # Function to retrieve TTM EPS using yfinance
# def get_ttm_eps(ticker):
#     stock = yf.Ticker(ticker)
#     try:
#         ttm_eps = stock.info['trailingEps']
#         return ttm_eps
#     except KeyError:
#         print(f"TTM EPS not available for {ticker}. Setting EPS to None.")
#         return None
#
# # Function to compute the price changes and other metrics
# def calculate_price_change_metrics(data, current_date):
#     # Define time periods (in days)
#     periods = {
#         '1_week': 7,
#         '1_month': 30,
#         '2_months': 60,
#         '3_months': 90,
#         '6_months': 180,
#         '1_year': 365
#     }
#
#     # Get the latest closing price
#     latest_price = data['Close'].iloc[-1]
#
#     # Calculate 1-year (52-week), 6-month, and 3-month highs
#     data_last_1_year = data[data['Date'] >= current_date - timedelta(days=365)]
#     data_last_6_months = data[data['Date'] >= current_date - timedelta(days=180)]
#     data_last_3_months = data[data['Date'] >= current_date - timedelta(days=90)]
#     data_last_1_months = data[data['Date'] >= current_date - timedelta(days=30)]
#     data_last_1_weeks = data[data['Date'] >= current_date - timedelta(days=7)]
#
#     week_52_high = data_last_1_year['Close'].max()
#     month_6_high = data_last_6_months['Close'].max()
#     month_3_high = data_last_3_months['Close'].max()
#     month_1_high = data_last_1_months['Close'].max()
#     week_1_high = data_last_1_weeks['Close'].max()
#
#     # Calculate percentage of the 1-year, 6-month, and 3-month highs
#     percentage_of_52_week_high = (latest_price / week_52_high) * 100 if week_52_high > 0 else 0
#     percentage_of_6_month_high = (latest_price / month_6_high) * 100 if month_6_high > 0 else 0
#     percentage_of_3_month_high = (latest_price / month_3_high) * 100 if month_3_high > 0 else 0
#     percentage_of_1_month_high = (latest_price / month_1_high) * 100 if month_1_high > 0 else 0
#     percentage_of_1_week_high = (latest_price / week_1_high) * 100 if week_1_high > 0 else 0
#
#     # Prepare a dictionary to hold the price changes and additional metrics
#     metrics = {
#         'Date': current_date,
#         'Current_Price': latest_price,
#         '52_Week_High': week_52_high,
#         '6_Month_High': month_6_high,
#         '3_Month_High': month_3_high,
#         'Percentage_of_52_Week_High': percentage_of_52_week_high,
#         'Percentage_of_6_Month_High': percentage_of_6_month_high,
#         'Percentage_of_3_Month_High': percentage_of_3_month_high,
#         'Percentage_of_1_Month_High': percentage_of_1_month_high,
#         'Percentage_of_1_Week_High': percentage_of_1_week_high
#     }
#
#     # Add the current RSI and MACD indicators to the metrics
#     metrics['Current_RSI'] = data['RSI'].iloc[-1]
#     metrics['Current_MACD'] = data['MACD'].iloc[-1]
#     metrics['Current_Signal_Line'] = data['Signal'].iloc[-1]
#
#     # Calculate price changes for the last week and last month
#     for label, days in periods.items():
#         period_start = current_date - timedelta(days=days)
#
#         # Get the price at the start of the period (find the nearest available date)
#         closest_date = data[data['Date'] <= period_start].iloc[-1]
#         period_start_price = closest_date['Close']
#
#         # Calculate price change (without multiplying by 100, keeping it as a decimal)
#         price_change = (latest_price - period_start_price) / period_start_price
#         metrics[f'Price_Change_{label}'] = price_change
#
#     return metrics
#
# # Calculate money flow metrics
# def calculate_money_flow_indicators(data):
#     # Calculate Money Flow Index (MFI)
#     data['Typical_Price'] = (data['High'] + data['Low'] + data['Close']) / 3
#     data['Money_Flow'] = data['Typical_Price'] * data['Volume']
#
#     # Calculate Positive and Negative Money Flow based on Typical Price shifts
#     data['Positive_Flow'] = data['Money_Flow'].where(data['Typical_Price'] > data['Typical_Price'].shift(1), 0)
#     data['Negative_Flow'] = data['Money_Flow'].where(data['Typical_Price'] < data['Typical_Price'].shift(1), 0)
#
#     # Calculate Money Flow Ratio and MFI
#     data['Money_Flow_Ratio'] = data['Positive_Flow'].rolling(14).sum() / data['Negative_Flow'].rolling(14).sum()
#     data['MFI'] = 100 - (100 / (1 + data['Money_Flow_Ratio']))
#
#     # Calculate On-Balance Volume (OBV)
#     obv_change = data['Volume'] * (
#                 (data['Close'] > data['Close'].shift(1)).astype(int) - (data['Close'] < data['Close'].shift(1)).astype(
#             int))
#     data['OBV'] = obv_change.cumsum()
#
#     # Calculate Accumulation/Distribution (A/D) Line
#     data['AD_Multiplier'] = ((data['Close'] - data['Low']) - (data['High'] - data['Close'])) / (
#                 data['High'] - data['Low'])
#     data['AD_Volume'] = data['AD_Multiplier'] * data['Volume']
#     data['AD_Line'] = data['AD_Volume'].cumsum()
#
#     return data
#
#
# # Function to add P/E Ratio, MFI, and A/D Line to the metrics file
# def compute_and_save_metrics(tickers, price_history_filename, metrics_filename, mfstats_filename):
#     price_data = pd.read_excel(price_history_filename)
#
#     all_metrics = []
#     current_date = price_data['Date'].max()
#
#     for ticker in tickers:
#         print(f"Compute and save metrics for {ticker}")
#         ticker_data = price_data[price_data['ticker'] == ticker]
#
#         # Last recorded values for current P/E Ratio, MFI, and A/D Line
#         if 'PE_Ratio' not in ticker_data.columns:
#             current_pe_ratio = ""
#         else:
#             current_pe_ratio = ticker_data['PE_Ratio'].iloc[-1]
#         current_mfi = ticker_data['MFI'].iloc[-1]
#         current_ad_line = ticker_data['AD_Line'].iloc[-1]
#
#         metrics = calculate_price_change_metrics(ticker_data, current_date)
#         metrics['ticker'] = ticker
#         metrics['Current_PE_Ratio'] = current_pe_ratio
#         metrics['Current_MFI'] = current_mfi
#         metrics['Current_AD_Line'] = current_ad_line
#
#         all_metrics.append(metrics)
#
#     metrics_df = pd.DataFrame(all_metrics)
#
#     mfstats_df = pd.read_csv(mfstats_filename)
#     mfstats_df = mfstats_df[['ticker', 'MF Scoreboard', 'Rec Appearances', 'Avg Rec Rating']]
#
#     combined_df = pd.merge(metrics_df, mfstats_df, on='ticker', how='left')
#
#     # Write the combined data to an Excel file
#     combined_df.to_excel(metrics_filename, sheet_name='Price_Change_Metrics', index=False)
#     combined_df.to_excel(f"C:/Users/ryanm/Desktop/Stock_Data/{metrics_filename}", sheet_name='Price_Change_Metrics', index=False)
#
#     print(f"Metrics with MFStats have been written to '{metrics_filename}'")
#
#
# # Function to compute the RSI for a given data
# def calculate_rsi(data, period=14):
#     delta = data['Close'].diff()
#     gain = delta.where(delta > 0, 0)  # Keep only positive gains
#     loss = -delta.where(delta < 0, 0)  # Keep only negative losses, but make them positive
#     avg_gain = gain.rolling(window=period, min_periods=1).mean()
#     avg_loss = loss.rolling(window=period, min_periods=1).mean()
#     rs = avg_gain / avg_loss
#     rsi = 100 - (100 / (1 + rs))
#     data['RSI'] = rsi
#     return data
#
#
# # Function to calculate MACD
# def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
#     data['EMA_12'] = data['Close'].ewm(span=fast_period, adjust=False).mean()
#     data['EMA_26'] = data['Close'].ewm(span=slow_period, adjust=False).mean()
#     data['MACD'] = data['EMA_12'] - data['EMA_26']
#     data['Signal'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
#     return data
#
#
# # Function to retrieve daily price history for the last two years for two tickers and save to an Excel file with daily P/E ratio
# def get_price_history_for_two_years(tickers, filename):
#     end_date = datetime.today()
#     start_date = end_date - timedelta(days=2*365)  # Approximate 2 years
#     price_history = {}
#
#     for ticker in tickers:
#         print(f"Getting price history for two years for {ticker}")
#         # Download the daily price data
#         stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
#         stock_data = stock_data.reset_index()
#         stock_data['ticker'] = ticker
#
#         # Calculate MACD, RSI, and Money Flow Indicators
#         stock_data = calculate_macd(stock_data)
#         stock_data = calculate_rsi(stock_data)
#         stock_data = calculate_money_flow_indicators(stock_data)
#
#         # Get the TTM EPS and calculate daily P/E ratio
#         ttm_eps = get_ttm_eps(ticker)
#         if ttm_eps:
#             stock_data['PE_Ratio'] = stock_data['Close'] / ttm_eps
#         else:
#             stock_data['PE_Ratio'] = None  # Set as None if EPS is not available
#
#         # Add to the dictionary
#         price_history[ticker] = stock_data
#
#     # Combine the price history for all tickers
#     combined_data = pd.concat([df for df in price_history.values() if not df.empty and not df.isna().all().all()], ignore_index=True)
#
#     # Write to Excel with P/E ratio included
#     combined_data.to_excel(filename, sheet_name='PriceHistoryWithIndicators', index=False)
#     combined_data.to_excel(f"C:/Users/ryanm/Desktop/Stock_Data/{filename}", sheet_name='PriceHistoryWithIndicators',
#                          index=False)
#
#     print(f"Daily price history with MACD, RSI, and P/E ratio has been written to '{filename}'")
#
#
# # Main script execution
# if __name__ == '__main__':
#     # Generate the price history for the last two years for AAPL and GOOGL
#     tickers = ['AAPL', 'ABNB', 'AMZN', 'ANET', 'ASML', 'AXON', 'AZO', 'BAC', 'BRK-B', 'BWXT', 'CDNS', 'CELH', 'CFLT',
#                'CHWY', 'CLBT', 'CMG', 'COST', 'CRWD', 'DAR', 'DASH', 'DDOG', 'DHI', 'EBAY', 'EGP', 'ELF', 'EME', 'EPR',
#                'EQT', 'ESRT', 'FTNT', 'GLD', 'GM', 'GOOG', 'GOOGL', 'GRMN', 'INTU', 'IRM', 'ISRG', 'JNJ', 'JPM',
#                'KNSL', 'KO', 'LOW', 'LULU', 'MA', 'MELI', 'MNDY', 'MNST', 'MSFT', 'NVDA', 'NVO', 'O', 'ODFL', 'ONON',
#                'PGR', 'PINS', 'PLD', 'PSX', 'PYPL', 'QQQ', 'RBLX', 'RDFN', 'RHP', 'RPM', 'SHOP', 'SNOW', 'SPG', 'SPY',
#                'TEAM', 'TLT', 'TMDX', 'TOST', 'TPL', 'TQQQ', 'TSLA', 'TTD', 'U', 'UNH', 'V', 'VEEV', 'VICI', 'VRTX',
#                'WMT', 'WSO', 'ZM']
#     # tickers = ['EGP', 'AAPL']
#
#     # Define file paths
#     price_history_filename = 'outputFiles/price_history_with_indicators.xlsx'
#     metrics_filename = 'outputFiles/price_change_metrics.xlsx'
#     mfstats_filename = 'inputFiles/mf_recs.csv'
#     combined_options_filename = 'outputFiles/options_with_yield.xlsx'
#     output_path = f'C:/Users/ryanm/Desktop/Stock_Data/{combined_options_filename}'
#
#     # Get price history with MACD and RSI indicators
#     get_price_history_for_two_years(tickers, price_history_filename)
#
#     # Compute metrics based on the price history
#     compute_and_save_metrics(tickers, price_history_filename, metrics_filename, mfstats_filename)
#
#     print(f"Price change metrics have been written to '{metrics_filename}'")
#
#     # Initialize an empty list to store options data for all tickers
#     all_options_data = []
#
#     # Iterate over each ticker to retrieve and compute options data
#     for ticker in tickers:
#         print(ticker)
#         options_data = get_options_data(ticker)
#         if options_data is not None and not options_data.empty:
#             options_data = compute_yield_and_annualized_return(options_data)
#             all_options_data.append(options_data)
#
#     # Combine options data for all tickers into a single DataFrame
#     combined_options = pd.concat(all_options_data, ignore_index=True)
#
#     # Write the combined options data to an Excel file
#     combined_options.to_excel(combined_options_filename, sheet_name='OptionsData', index=False)
#     combined_options.to_excel(output_path, sheet_name='OptionsData', index=False)
#
#     print(
#         f"Combined options data for all tickers, with yield and annualized return, has been written to '{combined_options_filename}' at '{output_path}'")