"""Market data provider abstraction and concrete implementations for multi-source data ingestion."""

from abc import ABC, abstractmethod
import os
from typing import Any, Dict, Optional
import pandas as pd
import yfinance as yf

try:
    import lse
except ImportError:
    lse = None


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        """Fetch current live or delayed market price information.

        Args:
            ticker: The asset ticker symbol.

        Returns:
            Dict containing ticker, current_price, previous_close, change_pct, currency, etc.
        """
        pass

    @abstractmethod
    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical OHLCV data for the given period.

        Args:
            ticker: The asset ticker symbol.
            period: Time span to fetch (default '1y').

        Returns:
            pd.DataFrame: OHLCV DataFrame indexed by date/datetime.
        """
        pass


class YFinanceProvider(MarketDataProvider):
    """Market data provider using yfinance.

    Supports global equities, including US tickers (e.g. 'AAPL') and Indian tickers
    (e.g. 'RELIANCE.NS', with automatic '.NS' appending for Indian stocks if needed).
    """

    def resolve_ticker(self, ticker: str) -> str:
        """Normalize ticker and handle Indian exchange suffixes (.NS).

        If ticker doesn't contain a dot and yields no direct data, attempts appending '.NS'.
        """
        clean_ticker = ticker.strip().upper()
        if "." in clean_ticker:
            return clean_ticker

        # Test if symbol exists directly (e.g. US stock like AAPL)
        try:
            s = yf.Ticker(clean_ticker)
            if not s.history(period="5d").empty:
                return clean_ticker
        except Exception:
            pass

        # Try appending .NS for National Stock Exchange of India
        try:
            ns_ticker = f"{clean_ticker}.NS"
            ns_s = yf.Ticker(ns_ticker)
            if not ns_s.history(period="5d").empty:
                return ns_ticker
        except Exception:
            pass

        return clean_ticker

    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        """Fetch real-time / 15-min delayed quote data from yfinance."""
        if not ticker or not isinstance(ticker, str):
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": None,
                "provider": "YFinanceProvider",
                "error": "A valid non-empty string ticker must be provided.",
            }

        resolved_ticker = self.resolve_ticker(ticker)

        try:
            stock = yf.Ticker(resolved_ticker)
            current_price = None
            prev_close = None
            currency = None

            try:
                fast_info = stock.fast_info
                current_price = getattr(fast_info, "last_price", None)
                if current_price is None:
                    current_price = fast_info.get("lastPrice")
                prev_close = getattr(fast_info, "previous_close", None)
                if prev_close is None:
                    prev_close = fast_info.get("previousClose")
                currency = getattr(fast_info, "currency", None)
                if currency is None:
                    currency = fast_info.get("currency")
            except Exception:
                pass

            # Fallback to history close if fast_info missing
            if current_price is None or prev_close is None:
                hist = stock.history(period="5d")
                if not hist.empty and "Close" in hist.columns:
                    if current_price is None:
                        current_price = float(hist["Close"].iloc[-1])
                    if prev_close is None and len(hist) >= 2:
                        prev_close = float(hist["Close"].iloc[-2])

            change_pct = None
            if current_price is not None and prev_close not in (None, 0):
                change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)
                current_price = round(float(current_price), 2)
            elif current_price is not None:
                current_price = round(float(current_price), 2)
                change_pct = 0.0

            if prev_close is not None:
                prev_close = round(float(prev_close), 2)

            return {
                "ticker": resolved_ticker,
                "current_price": current_price,
                "previous_close": prev_close,
                "change_pct": change_pct,
                "currency": currency,
                "provider": "YFinanceProvider",
            }

        except Exception as exc:
            return {
                "ticker": resolved_ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": None,
                "provider": "YFinanceProvider",
                "error": f"Failed to fetch live price for '{ticker}': {str(exc)}",
            }

    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical daily OHLCV data."""
        if not ticker or not isinstance(ticker, str):
            return pd.DataFrame()

        resolved_ticker = self.resolve_ticker(ticker)

        try:
            stock = yf.Ticker(resolved_ticker)
            df = stock.history(period=period)
            return df
        except Exception:
            return pd.DataFrame()


class LSEProvider(MarketDataProvider):
    """London Strategic Edge (LSE) Data Provider using the `lse-data` library.

    NOTE: This provider requires an active LSE API key to connect to the 
    London Strategic Edge market data feed. Obtain a key from London Strategic Edge
    and pass it to the constructor or set the LSE_API_KEY environment variable.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LSE_API_KEY")
        self.client = None
        if self.api_key and lse is not None:
            try:
                # Initialize LSE client when API key is provided
                self.client = lse.LSE(api_key=self.api_key)
            except Exception:
                self.client = None

    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        """Fetch live price using lse-data API.

        Requires an active LSE API key to run.
        """
        if not self.api_key:
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": "GBP",
                "provider": "LSEProvider",
                "error": "LSE API key required. Set LSE_API_KEY environment variable to use LSEProvider.",
            }

        try:
            # Example API call structure with lse-data:
            # client = self.client or lse.LSE(api_key=self.api_key)
            # tick = client.tape(market="LSE", symbol=ticker)
            # return {
            #     "ticker": ticker,
            #     "current_price": tick.price,
            #     "previous_close": getattr(tick, "prev_close", None),
            #     "change_pct": None,
            #     "currency": "GBP",
            #     "provider": "LSEProvider",
            # }
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": "GBP",
                "provider": "LSEProvider",
                "error": "Live connection not established.",
            }
        except Exception as exc:
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": "GBP",
                "provider": "LSEProvider",
                "error": f"LSE API error: {str(exc)}",
            }

    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical bar data using lse-data API.

        Requires an active LSE API key to run.
        """
        if not self.api_key:
            # Returns empty DataFrame when API key is not configured
            return pd.DataFrame()

        try:
            # Example API call structure with lse-data:
            # client = self.client or lse.LSE(api_key=self.api_key)
            # bars = client.load(symbol=ticker, timeframe="1d", period=period)
            # return pd.DataFrame(bars)
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
