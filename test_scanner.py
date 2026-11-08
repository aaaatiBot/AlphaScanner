"""Test script for Phase 3: The Master Scanner & Scoring Engine."""

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

from app.services.scanner import scan_market
from app.services.ticker_universe import TICKER_UNIVERSE

# Configure clean Pandas display settings
pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 1000)
pd.set_option("display.unicode.east_asian_width", True)


def main() -> None:
    print("=" * 95)
    print("ALPHASCANNER PHASE 3: MASTER SCANNER & SCORING ENGINE TEST")
    print(f"Total Ticker Universe: {len(TICKER_UNIVERSE)} stocks (US + India)")
    print("=" * 95)

    # 1. Take the first 10 tickers from the TICKER_UNIVERSE
    test_tickers = TICKER_UNIVERSE[:10]
    print(f"\nScanning Top 10 Batch: {test_tickers}\n")

    # 2. Run market scanner
    scan_results = scan_market(test_tickers, delay_seconds=2.0)

    # 3. Build summary DataFrame
    table_rows = []
    for r in scan_results:
        sent_str = f"{r['gemini_sentiment']:+.2f} ({r['sentiment_label']})"
        table_rows.append({
            "Ticker": r["ticker"],
            "Price": r["price"],
            "RSI": round(r["rsi"], 2) if r["rsi"] is not None else "N/A",
            "Gemini Sentiment": sent_str,
            "Tech Pts": f"{r['tech_score']:.1f}/50",
            "News Pts": f"{r['news_score']:.1f}/50",
            "Final Score": f"{r['final_score']:.1f}",
            "Verdict": r["verdict"],
        })

    df = pd.DataFrame(table_rows)

    print("\n" + "=" * 95)
    print("MASTER SCANNER RANKINGS (Sorted by Final Buy Score - Highest to Lowest)")
    print("=" * 95)
    print(df.to_string(index=False))
    print("=" * 95)

    # Print top 3 recommendations with AI summaries
    print("\nTOP RECOMMENDATIONS BREAKDOWN:")
    for idx, r in enumerate(scan_results[:3], 1):
        print(f"\n#{idx} {r['ticker']} - Final Score: {r['final_score']:.1f}/100 [{r['verdict']}]")
        print(f"   Price: {r['price']} | RSI: {r['rsi']} | Sentiment: {r['gemini_sentiment']}")
        print(f"   AI Catalyst Summary: {r['ai_summary']}")


if __name__ == "__main__":
    main()
