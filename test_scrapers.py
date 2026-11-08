"""Test script for AlphaScanner Multi-Source Data Provider & Aggregator."""

import pandas as pd
from app.services.data_aggregator import DataAggregator
from app.services.market_provider import YFinanceProvider, LSEProvider

# Configure pandas display for clean terminal tables
pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)


def test_aggregator_with_yfinance() -> None:
    print("=" * 80)
    print("ALPHASCANNER DATA SCRAPING ENGINE - MULTI-SOURCE ARCHITECTURE TEST")
    print("=" * 80)

    # Instantiate DataAggregator with YFinanceProvider as specified in STEP 4
    provider = YFinanceProvider()
    aggregator = DataAggregator(provider=provider)

    test_tickers = ["AAPL", "RELIANCE.NS"]

    for ticker in test_tickers:
        print("\n" + "#" * 80)
        print(f"Running Analysis for Ticker: {ticker}")
        print("#" * 80)

        analysis = aggregator.get_stock_analysis(ticker)

        if "error" in analysis and analysis.get("live_price", {}).get("current_price") is None:
            print(f"Error analyzing {ticker}: {analysis['error']}")
            continue

        live = analysis["live_price"]
        currency = live.get("currency") or ""
        price = live.get("current_price")
        prev_close = live.get("previous_close")
        change_pct = live.get("change_pct")
        prov_name = live.get("provider")

        # 1. Print Live Price Information
        print("\n[1] LIVE / REAL-TIME PRICE")
        print(f"  Ticker         : {live.get('ticker')}")
        print(f"  Provider       : {prov_name}")
        print(f"  Current Price  : {currency} {price}")
        print(f"  Previous Close : {currency} {prev_close}")
        print(f"  Change (%)     : {change_pct:+}%")

        # 2. Print Historical Data for the last 5 days
        print("\n[2] HISTORICAL DATA (Last 5 Days)")
        df = analysis["history_df"]
        if not df.empty:
            display_cols = [c for c in ["Open", "High", "Low", "Close", "Volume", "SMA_20", "SMA_50", "RSI_14"] if c in df.columns]
            print(df[display_cols].tail(5))
        else:
            print("  No historical data returned.")

        # 3. Print RSI Calculation & Technical Indicators
        print("\n[3] TECHNICAL INDICATORS (RSI & SMA)")
        indicators = analysis["indicators"]
        rsi_val = indicators.get("rsi")
        sma20_val = indicators.get("sma_20")
        sma50_val = indicators.get("sma_50")

        print(f"  14-Day RSI     : {rsi_val}")
        if rsi_val is not None:
            if rsi_val >= 70:
                rsi_signal = "Overbought (>= 70)"
            elif rsi_val <= 30:
                rsi_signal = "Oversold (<= 30)"
            else:
                rsi_signal = "Neutral (30 - 70)"
            print(f"  RSI Condition  : {rsi_signal}")

        print(f"  20-Day SMA     : {currency} {sma20_val}")
        print(f"  50-Day SMA     : {currency} {sma50_val}")


def test_lse_provider_stub() -> None:
    print("\n" + "=" * 80)
    print("TESTING LSE PROVIDER FALLBACK STRUCTURE (Without API Key)")
    print("=" * 80)
    lse_provider = LSEProvider()
    lse_result = lse_provider.get_live_price("VOD")
    print("LSE Live Price Call Result:")
    print(f"  Ticker   : {lse_result.get('ticker')}")
    print(f"  Provider : {lse_result.get('provider')}")
    print(f"  Notice   : {lse_result.get('error')}")


def main() -> None:
    test_aggregator_with_yfinance()
    test_lse_provider_stub()


if __name__ == "__main__":
    main()
