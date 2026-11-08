# AlphaScanner

AlphaScanner is a stock and sentiment analysis engine built in Python featuring a multi-source, battle-tested data acquisition architecture.

## Architecture Overview

1. **Primary Global Engine (`fba-finance`)**:
   - Rotates automatically between providers (`yfinance`, `Twelve Data`, `Alpha Vantage`) to eliminate rate-limiting bans.
   - Built-in multi-tier caching prevents duplicate queries.
2. **Dedicated Indian Equities Fallback (`vendor/Hive-Mind`)**:
   - Direct NSE & BSE tick streaming, historical data fetching, and symbol metadata.
3. **Technical Analysis Engine (`vendor/indiaquant-mcp`)**:
   - Native computation of 14-period RSI, MACD (line, signal, histogram), Bollinger Bands, and AI BUY/SELL/HOLD trade signals.
4. **AI News Sentiment Engine (`Gemini AI`)**:
   - Google News RSS headlines synthesized by Google Gemini AI with fallback to `TextBlob`.

## Project Structure

```text
stonks/
├── app/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── data_aggregator.py
│       ├── market_provider.py
│       ├── news_scraper.py
│       ├── stock_scraper.py
│       └── technical_analysis.py
├── vendor/
│   ├── Hive-Mind/
│   ├── indiaquant-mcp/
│   └── Indian-Stock-Market-API/
├── test_hybrid_engine.py
├── test_scrapers.py
├── requirements.txt
└── README.md
```

## Running the Verification Suite

```bash
python test_hybrid_engine.py
```
