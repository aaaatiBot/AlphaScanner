"""Market data providers for AlphaScanner, including the primary HybridDataProvider."""

import asyncio
import concurrent.futures
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import pandas as pd
import yfinance as yf

# Load environment variables
load_dotenv()

# Ensure standard streams support UTF-8 on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add vendor directories to sys.path
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_HIVE_MIND_PATH = os.path.join(_BASE_DIR, "vendor", "Hive-Mind")
if _HIVE_MIND_PATH not in sys.path:
    sys.path.insert(0, _HIVE_MIND_PATH)

# Primary fba-finance multi-source client
try:
    from fba_finance import FinanceClient
except ImportError:
    FinanceClient = None

# Optional LSE provider
try:
    import lse
except ImportError:
    lse = None


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        """Fetch current live or delayed market price information."""
        pass

    @abstractmethod
    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical OHLCV data for the given period."""
        pass


class HybridDataProvider(MarketDataProvider):
    """Hybrid market data provider combining fba-finance and Hive-Mind.

    - Primary Engine: `fba_finance.FinanceClient` with built-in provider rotation (yfinance,
      Twelve Data, Alpha Vantage) and caching to prevent rate-limiting and bans.
    - Fallback Engine: `Hive-Mind` (`MarketDataFetcher`) specialized for Indian equities (NSE/BSE).
    """

    def __init__(self):
        self.finance_client = FinanceClient() if FinanceClient is not None else None

    def _fetch_from_hive_mind(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fallback to Hive-Mind for Indian equities (NSE / BSE)."""
        clean = ticker.strip().upper()
        symbol = clean.replace(".NS", "").replace(".BO", "")
        exchange = "BSE" if clean.endswith(".BO") else "NSE"

        try:
            from market_data_fetcher import MarketDataFetcher
            fetcher = MarketDataFetcher()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                info = executor.submit(lambda: asyncio.run(fetcher.get_symbol_info(symbol, exchange=exchange))).result(timeout=10)

            if info and info.get("current_price"):
                current_price = round(float(info["current_price"]), 2)
                prev_close = round(float(info.get("previous_close", current_price)), 2) if info.get("previous_close") else None
                change_pct = round(float(info.get("change_percent", 0.0)), 2)
                return {
                    "ticker": ticker,
                    "current_price": current_price,
                    "previous_close": prev_close,
                    "change_pct": change_pct,
                    "currency": "INR",
                    "source": "Hive-Mind (NSE/BSE Fallback)",
                    "provider": "HybridDataProvider",
                }
        except Exception:
            pass
        return None

    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Fetch real-time quote for a stock.

        Tries `fba-finance.FinanceClient` first.
        If ticker ends with .NS or .BO (India) and fba-finance fails, falls back to Hive-Mind.
        """
        if not ticker or not isinstance(ticker, str):
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": None,
                "source": "none",
                "provider": "HybridDataProvider",
                "error": "A valid non-empty string ticker must be provided.",
            }

        clean_ticker = ticker.strip().upper()
        is_indian = clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO")

        # 1. Try fba-finance FinanceClient first
        if self.finance_client is not None:
            try:
                quote = self.finance_client.get_quote(clean_ticker)
                if quote is not None and quote.price is not None:
                    price = round(float(quote.price), 2)
                    prev_close = round(float(quote.previous_close), 2) if quote.previous_close else None
                    change_pct = round(float(quote.change_percent), 2) if quote.change_percent is not None else 0.0
                    currency = quote.currency or ("INR" if is_indian else "USD")
                    source = f"fba-finance ({quote.source or 'primary'})"

                    return {
                        "ticker": clean_ticker,
                        "current_price": price,
                        "previous_close": prev_close,
                        "change_pct": change_pct,
                        "currency": currency,
                        "source": source,
                        "provider": "HybridDataProvider",
                    }
            except Exception:
                pass

        # 2. If Indian ticker and primary failed, try Hive-Mind fallback
        if is_indian:
            hive_res = self._fetch_from_hive_mind(clean_ticker)
            if hive_res is not None:
                return hive_res

        # 3. Final yfinance fallback if needed
        try:
            s = yf.Ticker(clean_ticker)
            fast_info = s.fast_info
            price = round(float(fast_info.last_price), 2) if fast_info.last_price else None
            prev_close = round(float(fast_info.previous_close), 2) if fast_info.previous_close else None
            change_pct = round(((price - prev_close) / prev_close) * 100, 2) if price and prev_close else 0.0
            currency = fast_info.currency or ("INR" if is_indian else "USD")

            return {
                "ticker": clean_ticker,
                "current_price": price,
                "previous_close": prev_close,
                "change_pct": change_pct,
                "currency": currency,
                "source": "yfinance (direct fallback)",
                "provider": "HybridDataProvider",
            }
        except Exception as exc:
            return {
                "ticker": clean_ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": "INR" if is_indian else "USD",
                "source": "none",
                "provider": "HybridDataProvider",
                "error": f"Failed to fetch quote for '{ticker}': {str(exc)}",
            }

    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        """Alias for get_quote to satisfy MarketDataProvider interface."""
        return self.get_quote(ticker)

    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical daily OHLCV data using fba-finance's built-in caching."""
        if not ticker or not isinstance(ticker, str):
            return pd.DataFrame()

        clean_ticker = ticker.strip().upper()
        is_indian = clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO")

        # 1. Try fba-finance with built-in caching
        if self.finance_client is not None:
            try:
                hist = self.finance_client.get_historical(clean_ticker, period=period)
                if hist and hasattr(hist, "data") and isinstance(hist.data, pd.DataFrame) and not hist.data.empty:
                    df = hist.data.copy()
                    rename_map = {
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "volume": "Volume",
                        "date": "Date",
                    }
                    df = df.rename(columns=rename_map)
                    if "Date" in df.columns:
                        df["Date"] = pd.to_datetime(df["Date"])
                        df = df.set_index("Date")
                    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
                    return df[cols]
            except Exception:
                pass

        # 2. Try Hive-Mind fallback for Indian stocks
        if is_indian:
            symbol = clean_ticker.replace(".NS", "").replace(".BO", "")
            exchange = "BSE" if clean_ticker.endswith(".BO") else "NSE"
            try:
                from market_data_fetcher import MarketDataFetcher
                fetcher = MarketDataFetcher()
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    records = executor.submit(lambda: asyncio.run(fetcher.get_historical_data(symbol, exchange=exchange, interval="1D"))).result(timeout=10)
                if records:
                    df = pd.DataFrame(records)
                    if "timestamp" in df.columns:
                        df["Date"] = pd.to_datetime(df["timestamp"])
                        df = df.set_index("Date")
                    rename_map = {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
                    df = df.rename(columns=rename_map)
                    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
                    return df[cols]
            except Exception:
                pass

        # 3. Direct yfinance fallback
        try:
            stock = yf.Ticker(clean_ticker)
            return stock.history(period=period)
        except Exception:
            return pd.DataFrame()


class YFinanceProvider(MarketDataProvider):
    """Direct yfinance provider with Indian exchange suffix resolution."""

    def resolve_ticker(self, ticker: str) -> str:
        clean_ticker = ticker.strip().upper()
        if "." in clean_ticker:
            return clean_ticker
        try:
            s = yf.Ticker(clean_ticker)
            if not s.history(period="5d").empty:
                return clean_ticker
        except Exception:
            pass
        try:
            ns_ticker = f"{clean_ticker}.NS"
            ns_s = yf.Ticker(ns_ticker)
            if not ns_s.history(period="5d").empty:
                return ns_ticker
        except Exception:
            pass
        return clean_ticker

    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        resolved = self.resolve_ticker(ticker)
        try:
            stock = yf.Ticker(resolved)
            fast_info = stock.fast_info
            current_price = getattr(fast_info, "last_price", None) or fast_info.get("lastPrice")
            prev_close = getattr(fast_info, "previous_close", None) or fast_info.get("previousClose")
            currency = getattr(fast_info, "currency", None) or fast_info.get("currency")

            change_pct = 0.0
            if current_price and prev_close:
                change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)
                current_price = round(float(current_price), 2)
                prev_close = round(float(prev_close), 2)

            return {
                "ticker": resolved,
                "current_price": current_price,
                "previous_close": prev_close,
                "change_pct": change_pct,
                "currency": currency,
                "provider": "YFinanceProvider",
            }
        except Exception as exc:
            return {
                "ticker": resolved,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": None,
                "provider": "YFinanceProvider",
                "error": str(exc),
            }

    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        resolved = self.resolve_ticker(ticker)
        try:
            return yf.Ticker(resolved).history(period=period)
        except Exception:
            return pd.DataFrame()


class LSEProvider(MarketDataProvider):
    """London Strategic Edge (LSE) Data Provider using the `lse-data` library."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LSE_API_KEY")
        self.client = None
        if self.api_key and lse is not None:
            try:
                self.client = lse.LSE(api_key=self.api_key, timeout=10)
            except Exception:
                self.client = None

    def _detect_market(self, ticker: str) -> str:
        clean = ticker.strip().upper()
        if clean.endswith(".L") or clean in ["VOD", "BP", "HSBA", "AZN", "SHEL", "GSK"]:
            return "uk_stocks"
        return "us_stocks"

    def get_live_price(self, ticker: str) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": "USD",
                "provider": "LSEProvider",
                "error": "LSE API key required.",
            }

        symbol = ticker.strip().upper().replace(".L", "")
        market = self._detect_market(ticker)
        currency = "GBP" if market == "uk_stocks" else "USD"

        try:
            client = self.client or lse.LSE(api_key=self.api_key, timeout=10)
            candles = client.candles(symbol=symbol, market=market, timeframe="1d", limit=2)
            if not candles:
                return {
                    "ticker": ticker,
                    "current_price": None,
                    "previous_close": None,
                    "change_pct": None,
                    "currency": currency,
                    "provider": "LSEProvider",
                    "error": f"No candle data returned for symbol '{symbol}'.",
                }

            latest = candles[-1]
            current_price = round(float(latest.get("close", 0.0)), 2)
            prev_close = round(float(candles[-2].get("close", 0.0)), 2) if len(candles) >= 2 else None

            change_pct = 0.0
            if current_price and prev_close:
                change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

            return {
                "ticker": ticker,
                "current_price": current_price,
                "previous_close": prev_close,
                "change_pct": change_pct,
                "currency": currency,
                "provider": "LSEProvider",
            }
        except Exception as exc:
            return {
                "ticker": ticker,
                "current_price": None,
                "previous_close": None,
                "change_pct": None,
                "currency": currency,
                "provider": "LSEProvider",
                "error": str(exc),
            }

    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        if not self.api_key:
            return pd.DataFrame()

        symbol = ticker.strip().upper().replace(".L", "")
        market = self._detect_market(ticker)
        limit = 252 if period == "1y" else 500

        try:
            client = self.client or lse.LSE(api_key=self.api_key, timeout=10)
            candles = client.candles(symbol=symbol, market=market, timeframe="1d", limit=limit)
            if not candles:
                return pd.DataFrame()

            df = pd.DataFrame(candles)
            if "timestamp" in df.columns:
                df["Date"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("Date")
            elif "date" in df.columns:
                df["Date"] = pd.to_datetime(df["date"])
                df = df.set_index("Date")

            rename_map = {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
            df = df.rename(columns=rename_map)
            cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
            return df[cols]
        except Exception:
            return pd.DataFrame()
