"""Master Market Scanner for AlphaScanner: batch-processes tickers through Hybrid Engine & Score Engine."""

import time
from typing import Any, Dict, List, Optional
from .data_aggregator import DataAggregator
from .market_provider import HybridDataProvider
from .score_engine import calculate_buy_score


def scan_market(
    tickers: List[str],
    delay_seconds: float = 2.0,
    aggregator: Optional[DataAggregator] = None,
) -> List[Dict[str, Any]]:
    """Scan a list of tickers, compute technical indicators, Gemini AI sentiment,

    and final Buy Scores, sorted in descending order of Buy Score.

    Args:
        tickers: List of stock ticker symbols.
        delay_seconds: Pause between API requests to respect rate limits (default 2.0s).
        aggregator: Optional DataAggregator instance (defaults to HybridDataProvider).

    Returns:
        List of dicts for each ticker containing price, RSI, sentiment, scores, and verdict,
        sorted from highest final_score to lowest.
    """
    if aggregator is None:
        aggregator = DataAggregator(provider=HybridDataProvider())

    results: List[Dict[str, Any]] = []
    total = len(tickers)

    for idx, ticker in enumerate(tickers):
        clean_ticker = ticker.strip().upper()
        print(f"[{idx + 1}/{total}] Scanning {clean_ticker}...")

        try:
            # 1. Fetch analysis: quote + history + IndiaQuant technicals + Gemini news
            analysis = aggregator.get_stock_analysis(clean_ticker, include_news=True)

            live = analysis.get("live_price", {})
            technicals = analysis.get("technicals", {})
            sentiment = analysis.get("sentiment", {})

            # 2. Compute final Buy Score via score_engine
            score_res = calculate_buy_score(tech_data=technicals, news_data=sentiment)

            price = live.get("current_price")
            currency = live.get("currency") or ("INR" if clean_ticker.endswith(".NS") else "USD")

            record = {
                "ticker": clean_ticker,
                "price": f"{currency} {price}" if price is not None else "N/A",
                "raw_price": price,
                "currency": currency,
                "change_pct": live.get("change_pct", 0.0),
                "rsi": technicals.get("rsi"),
                "macd": technicals.get("macd", {}).get("macd"),
                "macd_signal": technicals.get("macd", {}).get("signal"),
                "gemini_sentiment": sentiment.get("average_sentiment", 0.0),
                "sentiment_label": sentiment.get("sentiment_label", "Neutral"),
                "ai_summary": sentiment.get("ai_summary", ""),
                "tech_score": score_res["tech_score"],
                "news_score": score_res["news_score"],
                "final_score": score_res["final_score"],
                "verdict": score_res["verdict"],
                "source": live.get("source", "HybridDataProvider"),
            }
            results.append(record)

        except Exception as exc:
            print(f"  [Warning] Error scanning {clean_ticker}: {exc}")
            results.append({
                "ticker": clean_ticker,
                "price": "N/A",
                "raw_price": None,
                "currency": "USD",
                "change_pct": 0.0,
                "rsi": None,
                "macd": None,
                "macd_signal": None,
                "gemini_sentiment": 0.0,
                "sentiment_label": "Neutral",
                "ai_summary": f"Scan error: {str(exc)}",
                "tech_score": 0.0,
                "news_score": 25.0,
                "final_score": 25.0,
                "verdict": "AVOID",
                "source": "error",
            })

        # Pause to prevent rate-limiting on Gemini & market endpoints
        if idx < total - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)

    # Sort results by final_score descending (best stocks to buy first)
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results
