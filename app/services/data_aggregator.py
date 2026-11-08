"""Data Aggregator service coordinating market providers and technical analysis."""

from typing import Any, Dict, Optional
import pandas as pd

from .market_provider import MarketDataProvider, YFinanceProvider


class DataAggregator:
    """Aggregates market data from configurable providers and calculates technical indicators."""

    def __init__(self, provider: Optional[MarketDataProvider] = None):
        """Initialize aggregator with a market data provider.

        Args:
            provider: Concrete MarketDataProvider instance. Defaults to YFinanceProvider.
        """
        self.provider: MarketDataProvider = provider if provider is not None else YFinanceProvider()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate the Relative Strength Index (RSI) using standard Wilder's smoothing.

        Args:
            series: Price series (typically Close price).
            period: Smoothing period (default 14).

        Returns:
            pd.Series: RSI series bounded between 0 and 100.
        """
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_stock_analysis(self, ticker: str) -> Dict[str, Any]:
        """Fetch live quote and 1-year historical data, and compute technical indicators (RSI, SMA).

        Args:
            ticker: The asset ticker symbol (e.g. 'AAPL', 'RELIANCE.NS').

        Returns:
            dict containing:
                - ticker (str): The requested ticker.
                - live_price (dict): Output from the provider's get_live_price.
                - history_df (pd.DataFrame): 1-year history with SMA_20, SMA_50, and RSI_14.
                - indicators (dict): Latest calculated RSI and SMA values.
                - error (str, optional): Error message if fetching fails.
        """
        live_price_data = self.provider.get_live_price(ticker)
        history_df = self.provider.get_historical_data(ticker, period="1y")

        if history_df.empty or "Close" not in history_df.columns:
            return {
                "ticker": live_price_data.get("ticker", ticker),
                "live_price": live_price_data,
                "history_df": history_df,
                "indicators": {
                    "rsi": None,
                    "sma_20": None,
                    "sma_50": None,
                },
                "error": f"No historical price data available for '{ticker}'.",
            }

        df = history_df.copy()

        # Calculate Simple Moving Averages
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()

        # Calculate 14-day RSI
        df["RSI_14"] = self.calculate_rsi(df["Close"], period=14)

        # Extract latest indicator metrics
        valid_rsi = df["RSI_14"].dropna()
        latest_rsi = round(float(valid_rsi.iloc[-1]), 2) if not valid_rsi.empty else None

        valid_sma_20 = df["SMA_20"].dropna()
        latest_sma_20 = round(float(valid_sma_20.iloc[-1]), 2) if not valid_sma_20.empty else None

        valid_sma_50 = df["SMA_50"].dropna()
        latest_sma_50 = round(float(valid_sma_50.iloc[-1]), 2) if not valid_sma_50.empty else None

        return {
            "ticker": live_price_data.get("ticker", ticker),
            "live_price": live_price_data,
            "history_df": df,
            "indicators": {
                "rsi": latest_rsi,
                "sma_20": latest_sma_20,
                "sma_50": latest_sma_50,
            },
        }
