# Generate the price history and indicators for a list of tickers
from configs import tickers, price_history_filename, metrics_filename, mfstats_filename
from functions.get_price_history_for_two_years import get_price_history_for_two_years
from functions.compute_and_save_metrics import compute_and_save_metrics

# Get price history with MACD and RSI indicators
get_price_history_for_two_years(tickers, price_history_filename)

# Compute metrics based on the price history
compute_and_save_metrics(tickers, price_history_filename, metrics_filename, mfstats_filename)