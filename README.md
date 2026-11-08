# AlphaScanner

AlphaScanner is a stock and sentiment analysis engine built in Python. This phase implements the core data scraping engine for financial metrics and news sentiment.

## Features

- **Stock Data Scraping (`app/services/stock_scraper.py`)**:
  - Real-time and fast market data fetching using `yfinance`.
  - Current price, previous close, percentage change, and currency detection.
  - 1-year historical daily OHLCV dataset loaded into Pandas DataFrames.
  - Graceful handling of invalid and delisted tickers.
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

## Testing Scrapers

Run the scraper test script at the root:

```bash
python test_scrapers.py
```
