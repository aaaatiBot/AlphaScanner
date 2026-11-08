"""AlphaScanner Services Package."""

from .data_aggregator import DataAggregator
from .market_provider import (
    HybridDataProvider,
    LSEProvider,
    MarketDataProvider,
    YFinanceProvider,
)
from .news_scraper import get_news_sentiment
from .scanner import scan_market
from .score_engine import calculate_buy_score
from .stock_scraper import get_stock_data
from .technical_analysis import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
    generate_trade_signal,
)
from .ticker_universe import TICKER_UNIVERSE

__all__ = [
    "DataAggregator",
    "HybridDataProvider",
    "MarketDataProvider",
    "YFinanceProvider",
    "LSEProvider",
    "get_stock_data",
    "get_news_sentiment",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "generate_trade_signal",
    "calculate_buy_score",
    "scan_market",
    "TICKER_UNIVERSE",
]
