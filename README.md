# AlphaScanner

AlphaScanner is a stock and sentiment analysis engine built in Python featuring a multi-source data provider architecture.

## Features

- **Multi-Source Market Data Provider (`app/services/market_provider.py`)**:
  - `MarketDataProvider`: Abstract base class establishing interfaces for live quotes and historical OHLCV data.
  - `YFinanceProvider`: Default provider for global equities, supporting US tickers (e.g. `AAPL`) and Indian tickers (e.g. `RELIANCE.NS` / automatic `.NS` exchange resolution).
  - `LSEProvider`: Integration structure for London Strategic Edge (`lse-data`), prepared for real-time fallback feeds (requires API key).
- **Data Aggregator & Technical Analysis (`app/services/data_aggregator.py`)**:
  - Coordinates provider data ingestion.
  - Automatically computes technical indicators:
    - 14-period Relative Strength Index (RSI) using Wilder's smoothing.
    - 20-day Simple Moving Average (SMA_20).
    - 50-day Simple Moving Average (SMA_50).
- **News Sentiment Analysis (`app/services/news_scraper.py`)**:
  - Automated RSS feed retrieval from Google News.
  - Extraction of top news headlines for any ticker.
  - Headline sentiment polarity scoring and classification (Positive / Neutral / Negative) using `TextBlob`.

## Project Structure

```text
stonks/
├── app/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── data_aggregator.py
│       ├── market_provider.py
│       ├── stock_scraper.py
│       └── news_scraper.py
├── .gitignore
├── requirements.txt
├── test_scrapers.py
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Testing Scrapers & Aggregator

Run the test suite:

```bash
python test_scrapers.py
```
