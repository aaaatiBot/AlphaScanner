"""Data Aggregator service coordinating HybridDataProvider, IndiaQuant technicals, and Gemini AI news sentiment."""

from typing import Any, Dict, Optional
import pandas as pd

from .market_provider import HybridDataProvider, MarketDataProvider
from .news_scraper import get_news_sentiment
from .technical_analysis import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
    generate_trade_signal,
)


class DataAggregator:
    """Aggregates market data from HybridDataProvider, computes technical indicators via IndiaQuant,

    and analyzes news sentiment using Gemini AI.
    """

    def __init__(self, provider: Optional[MarketDataProvider] = None):
        """Initialize aggregator. Defaults to HybridDataProvider for anti-rate-limiting rotation and fallbacks."""
        self.provider: MarketDataProvider = provider if provider is not None else HybridDataProvider()

    def get_stock_analysis(self, ticker: str, include_news: bool = True) -> Dict[str, Any]:
        """Fetch quote and historical data, calculate technical indicators and AI signals.

        Pipeline:
        1. HybridDataProvider fetches live price (fba-finance rotation / Hive-Mind fallback).
        2. HybridDataProvider fetches cached 1-year historical data.
        3. IndiaQuant computes RSI, MACD, Bollinger Bands, and AI Trade Signals.
        4. Gemini AI analyzes top news headlines.

        Args:
            ticker: The asset ticker symbol (e.g. 'AAPL', 'RELIANCE.NS').
            include_news: Whether to fetch and synthesize news sentiment (default True).

        Returns:
            Dict containing live_price, history_df, technicals, and sentiment.
        """
        # 1. Fetch live quote
        live_price_data = self.provider.get_live_price(ticker)

        # 2. Fetch cached historical OHLCV data
        history_df = self.provider.get_historical_data(ticker, period="1y")

        technicals: Dict[str, Any] = {
            "rsi": None,
            "macd": {"macd": 0.0, "signal": 0.0, "histogram": 0.0},
            "bollinger_bands": {"upper": 0.0, "middle": 0.0, "lower": 0.0},
            "trade_signal": {"signal": "NEUTRAL", "confidence": 0.5, "reasons": []},
            "sma_20": None,
            "sma_50": None,
        }

        # 3. Compute indicators using IndiaQuant
        if not history_df.empty and "Close" in history_df.columns:
            closes = history_df["Close"].dropna()
            if len(closes) >= 14:
                technicals["rsi"] = calculate_rsi(closes)
                technicals["macd"] = calculate_macd(closes)
                technicals["bollinger_bands"] = calculate_bollinger_bands(closes)
                technicals["trade_signal"] = generate_trade_signal(ticker, closes=closes)

                # Add moving averages
                history_df["SMA_20"] = history_df["Close"].rolling(window=20).mean()
                history_df["SMA_50"] = history_df["Close"].rolling(window=50).mean()
                valid_sma20 = history_df["SMA_20"].dropna()
                valid_sma50 = history_df["SMA_50"].dropna()
                technicals["sma_20"] = round(float(valid_sma20.iloc[-1]), 2) if not valid_sma20.empty else None
                technicals["sma_50"] = round(float(valid_sma50.iloc[-1]), 2) if not valid_sma50.empty else None

        # 4. Fetch News Sentiment via Gemini AI
        sentiment: Dict[str, Any] = {}
        if include_news:
            sentiment = get_news_sentiment(ticker)

        return {
            "ticker": live_price_data.get("ticker", ticker),
            "live_price": live_price_data,
            "history_df": history_df,
            "technicals": technicals,
            "sentiment": sentiment,
        }
