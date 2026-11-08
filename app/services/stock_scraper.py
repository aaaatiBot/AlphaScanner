"""Stock data fetching service using yfinance."""

from typing import Any, Dict
import pandas as pd
import yfinance as yf


def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Fetch current price, percentage change, currency, and 1-year historical OHLCV data.

    Args:
        ticker: The stock ticker symbol (e.g. 'AAPL', 'RELIANCE.NS').

    Returns:
        dict: A dictionary containing:
            - ticker (str): The requested ticker symbol.
            - current_price (float or None): Latest market price.
            - change_pct (float or None): Percentage change compared to previous close.
            - history_df (pd.DataFrame): 1-year historical daily OHLCV DataFrame.
            - currency (str or None): Currency code (e.g., 'USD', 'INR').
            - error (str, optional): Error message if fetching fails or ticker is invalid.
    """
    if not ticker or not isinstance(ticker, str):
        return {
            "ticker": ticker,
            "current_price": None,
            "change_pct": None,
            "history_df": pd.DataFrame(),
            "currency": None,
            "error": "A valid non-empty string ticker must be provided.",
        }

    ticker = ticker.strip()

    try:
        stock = yf.Ticker(ticker)

        # 1-year daily historical OHLCV data
        history_df = stock.history(period="1y")

        if history_df.empty:
            return {
                "ticker": ticker,
                "current_price": None,
                "change_pct": None,
                "history_df": pd.DataFrame(),
                "currency": None,
                "error": f"No historical data found for ticker '{ticker}'. The ticker may be invalid or delisted.",
            }

        # Retrieve current price, previous close, and currency from fast_info
        current_price = None
        prev_close = None
        currency = None

        try:
            fast_info = stock.fast_info
            current_price = getattr(fast_info, "last_price", None)
            if current_price is None:
                current_price = fast_info.get("lastPrice")
        except Exception:
            current_price = None

        try:
            prev_close = getattr(fast_info, "previous_close", None)
            if prev_close is None:
                prev_close = fast_info.get("previousClose")
        except Exception:
            prev_close = None

        try:
            currency = getattr(fast_info, "currency", None)
            if currency is None:
                currency = fast_info.get("currency")
        except Exception:
            currency = None

        # Fallbacks from historical DataFrame if fast_info fields are missing
        if current_price is None and not history_df.empty and "Close" in history_df.columns:
            current_price = float(history_df["Close"].iloc[-1])

        if prev_close is None and len(history_df) >= 2 and "Close" in history_df.columns:
            prev_close = float(history_df["Close"].iloc[-2])

        # Calculate percentage change
        change_pct = None
        if current_price is not None and prev_close not in (None, 0):
            change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)
            current_price = round(float(current_price), 2)
        elif current_price is not None:
            current_price = round(float(current_price), 2)
            change_pct = 0.0

        return {
            "ticker": ticker,
            "current_price": current_price,
            "change_pct": change_pct,
            "history_df": history_df,
            "currency": currency,
        }

    except Exception as exc:
        return {
            "ticker": ticker,
            "current_price": None,
            "change_pct": None,
            "history_df": pd.DataFrame(),
            "currency": None,
            "error": f"Error fetching data for ticker '{ticker}': {str(exc)}",
        }
