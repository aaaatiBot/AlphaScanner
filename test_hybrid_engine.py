"""Verification test script for AlphaScanner's Hybrid Data Architecture."""

import asyncio
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Configure stdout encoding on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add vendor path for Hive-Mind
VENDOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "vendor"))
HIVE_MIND_DIR = os.path.join(VENDOR_DIR, "Hive-Mind")
if HIVE_MIND_DIR not in sys.path:
    sys.path.insert(0, HIVE_MIND_DIR)

# Configure pandas formatting
pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)


def test_fba_finance_aapl() -> None:
    print("=" * 80)
    print("STEP 1: Testing Primary Multi-Source Engine (fba-finance FinanceClient)")
    print("=" * 80)

    from fba_finance import FinanceClient

    client = FinanceClient()
    print("\nFetching real-time quote for AAPL using FinanceClient...")
    quote = client.get_quote("AAPL")

    if quote is not None:
        prev_str = f"{quote.previous_close:.2f}" if quote.previous_close else "N/A"
        print(f"  [SUCCESS] Received quote via {quote.source}:")
        print(f"    Symbol         : {quote.symbol}")
        print(f"    Price          : {quote.currency} {quote.price:.2f}")
        print(f"    Previous Close : {quote.currency} {prev_str}")
        print(f"    Change (%)     : {quote.change_percent:+.2f}%")
        print(f"    Exchange       : {quote.exchange}")
    else:
        print("  [ERROR] Failed to fetch quote for AAPL.")


def test_hive_mind_reliance() -> None:
    print("\n" + "=" * 80)
    print("STEP 2: Testing Dedicated Indian Market Engine (Hive-Mind MarketDataFetcher)")
    print("=" * 80)

    from market_data_fetcher import MarketDataFetcher

    fetcher = MarketDataFetcher()
    print("\nFetching symbol info for RELIANCE.NS using Hive-Mind...")

    async def fetch():
        return await fetcher.get_symbol_info("RELIANCE", exchange="NSE")

    info = asyncio.run(fetch())

    if info and info.get("current_price"):
        print(f"  [SUCCESS] Received data via Hive-Mind (NSE):")
        print(f"    Company Name   : {info.get('company_name')}")
        print(f"    Exchange       : {info.get('exchange')}")
        print(f"    Current Price  : INR {info.get('current_price')}")
        print(f"    52-Week High   : INR {info.get('52_week_high')}")
        print(f"    52-Week Low    : INR {info.get('52_week_low')}")
        print(f"    Sector         : {info.get('sector')}")
    else:
        print(f"  [ERROR] Failed to fetch info via Hive-Mind: {info}")


def test_hybrid_provider_and_aggregator() -> None:
    print("\n" + "=" * 80)
    print("STEP 3: Testing HybridDataProvider & DataAggregator (Full Pipeline)")
    print("=" * 80)

    from app.services.data_aggregator import DataAggregator
    from app.services.market_provider import HybridDataProvider

    provider = HybridDataProvider()
    aggregator = DataAggregator(provider=provider)

    test_tickers = ["AAPL", "RELIANCE.NS"]

    for ticker in test_tickers:
        print("\n" + "-" * 80)
        print(f"Running Full Pipeline Analysis for: {ticker}")
        print("-" * 80)

        analysis = aggregator.get_stock_analysis(ticker, include_news=True)
        live = analysis["live_price"]
        tech = analysis["technicals"]
        sent = analysis["sentiment"]

        # 1. Live Price & Source
        print(f"\n[Price Data] (Source: {live.get('source', 'Unknown')})")
        print(f"  Ticker        : {live.get('ticker')}")
        print(f"  Price         : {live.get('currency')} {live.get('current_price')}")
        print(f"  Change        : {live.get('change_pct'):+}%")

        # 2. IndiaQuant Technicals
        print(f"\n[IndiaQuant Technical Indicators]")
        print(f"  RSI (14-period) : {tech.get('rsi')}")
        macd = tech.get("macd", {})
        print(f"  MACD            : Line={macd.get('macd')}, Signal={macd.get('signal')}, Hist={macd.get('histogram')}")
        bb = tech.get("bollinger_bands", {})
        print(f"  Bollinger Bands : Upper={bb.get('upper')}, Middle={bb.get('middle')}, Lower={bb.get('lower')}")
        sig = tech.get("trade_signal", {})
        print(f"  Trade Signal    : {sig.get('signal')} (Confidence: {sig.get('confidence')})")

        # 3. Gemini News Sentiment
        print(f"\n[Gemini AI News Sentiment] (Engine: {sent.get('engine')})")
        print(f"  Sentiment Score : {sent.get('average_sentiment')} ({sent.get('sentiment_label')})")
        print(f"  AI Summary      : {sent.get('ai_summary')}")
        print("  Top Headlines:")
        for idx, h in enumerate(sent.get("headlines", [])[:3], 1):
            print(f"    {idx}. {h}")


def main() -> None:
    test_fba_finance_aapl()
    test_hive_mind_reliance()
    test_hybrid_provider_and_aggregator()


if __name__ == "__main__":
    main()
