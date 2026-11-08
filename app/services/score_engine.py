"""Scoring Engine for AlphaScanner: Computes Technical and News Sentiment Buy Scores."""

from typing import Any, Dict, Union


def calculate_buy_score(
    tech_data: Union[Dict[str, Any], None],
    news_data: Union[Dict[str, Any], float, int, None],
) -> Dict[str, Any]:
    """Calculate the comprehensive Buy Score combining technical analysis and news sentiment.

    1. Technical Score (50 points max):
       - Baseline: 25 points
       - RSI < 40 (Oversold / Cheap): +15 points
       - RSI > 70 (Overbought / Expensive): -15 points
       - MACD Line > MACD Signal (Bullish momentum): +10 points
       - MACD Line < MACD Signal (Bearish momentum): -10 points
       - Clamped between 0 and 50 points.

    2. News Sentiment Score (50 points max):
       - Gemini sentiment score (-1.0 to 1.0) mapped to 0-50 scale.
       - Formula: (sentiment + 1.0) * 25.0
       - Clamped between 0 and 50 points.

    3. Final Score: Technical Score + News Sentiment Score (0 to 100 points).

    4. Verdict:
       - Score >= 75: "STRONG BUY"
       - Score 50 - 74: "HOLD"
       - Score < 50: "AVOID"

    Args:
        tech_data: Technical indicators dictionary containing 'rsi' and 'macd'.
        news_data: News sentiment dict containing 'average_sentiment' or raw float score.

    Returns:
        dict: {
            "final_score": float,
            "verdict": str,
            "tech_score": float,
            "news_score": float
        }
    """
    # ── 1. TECHNICAL SCORE (50 points max) ──
    tech_score = 25.0

    if isinstance(tech_data, dict):
        # RSI component
        rsi = tech_data.get("rsi")
        if rsi is not None:
            try:
                rsi_val = float(rsi)
                if rsi_val < 40.0:
                    tech_score += 15.0
                elif rsi_val > 70.0:
                    tech_score -= 15.0
            except (ValueError, TypeError):
                pass

        # MACD component
        macd_obj = tech_data.get("macd")
        macd_line = None
        macd_signal = None

        if isinstance(macd_obj, dict):
            macd_line = macd_obj.get("macd")
            macd_signal = macd_obj.get("signal")
        else:
            macd_line = tech_data.get("macd_line")
            macd_signal = tech_data.get("macd_signal")

        if macd_line is not None and macd_signal is not None:
            try:
                m_line = float(macd_line)
                m_sig = float(macd_signal)
                if m_line > m_sig:
                    tech_score += 10.0
                elif m_line < m_sig:
                    tech_score -= 10.0
            except (ValueError, TypeError):
                pass

    # Clamp Technical Score between 0 and 50
    tech_score = max(0.0, min(50.0, tech_score))

    # ── 2. NEWS SENTIMENT SCORE (50 points max) ──
    sentiment_val = 0.0
    if isinstance(news_data, dict):
        raw_sentiment = news_data.get("average_sentiment", 0.0)
        try:
            sentiment_val = float(raw_sentiment) if raw_sentiment is not None else 0.0
        except (ValueError, TypeError):
            sentiment_val = 0.0
    elif isinstance(news_data, (int, float)):
        sentiment_val = float(news_data)

    # Clamp sentiment to [-1.0, 1.0] before mapping
    sentiment_val = max(-1.0, min(1.0, sentiment_val))

    # Map -1.0 -> 0 pts, 0.0 -> 25 pts, 1.0 -> 50 pts
    news_score = (sentiment_val + 1.0) * 25.0
    news_score = max(0.0, min(50.0, news_score))

    # ── 3. FINAL SCORE & VERDICT ──
    final_score = round(tech_score + news_score, 2)
    final_score = max(0.0, min(100.0, final_score))

    if final_score >= 75.0:
        verdict = "STRONG BUY"
    elif final_score >= 50.0:
        verdict = "HOLD"
    else:
        verdict = "AVOID"

    return {
        "final_score": final_score,
        "verdict": verdict,
        "tech_score": round(tech_score, 2),
        "news_score": round(news_score, 2),
    }
