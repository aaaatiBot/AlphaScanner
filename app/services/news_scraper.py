"""News sentiment fetching service powered by Google News RSS, Gemini AI, and TextBlob fallback."""

import json
import os
import urllib.parse
from typing import Any, Dict, List
from dotenv import load_dotenv
import feedparser
import requests
from textblob import TextBlob

load_dotenv()


def get_news_sentiment(ticker: str) -> Dict[str, Any]:
    """Fetch top news headlines for a ticker and compute sentiment using Gemini AI (with TextBlob fallback).

    Args:
        ticker: The stock ticker symbol (e.g. 'AAPL', 'RELIANCE.NS').

    Returns:
        dict: A dictionary containing:
            - ticker (str): The requested ticker symbol.
            - headlines (List[str]): Top 5 headlines from the RSS feed.
            - average_sentiment (float): Sentiment polarity score (-1.0 to 1.0).
            - sentiment_label (str): "Positive", "Negative", or "Neutral".
            - ai_summary (str, optional): Synthesis from Gemini AI.
            - engine (str): "Gemini AI" or "TextBlob fallback".
            - error (str, optional): Error message if fetching fails.
    """
    if not ticker or not isinstance(ticker, str):
        return {
            "ticker": ticker,
            "headlines": [],
            "average_sentiment": 0.0,
            "sentiment_label": "Neutral",
            "ai_summary": None,
            "engine": "none",
            "error": "A valid non-empty string ticker must be provided.",
        }

    ticker = ticker.strip()

    try:
        # Construct Google News RSS query URL
        query = urllib.parse.quote_plus(f"{ticker} stock news")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        headlines: List[str] = [entry.title for entry in feed.entries[:5]]

        if not headlines:
            return {
                "ticker": ticker,
                "headlines": [],
                "average_sentiment": 0.0,
                "sentiment_label": "Neutral",
                "ai_summary": "No recent news headlines found.",
                "engine": "none",
            }

        gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Attempt Gemini AI sentiment analysis if API key is present
        if gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={gemini_api_key}"
                prompt = (
                    f"Analyze financial sentiment for ticker '{ticker}' based strictly on these top news headlines:\n"
                    f"{json.dumps(headlines, indent=2)}\n\n"
                    "Respond with a valid JSON object matching this schema:\n"
                    "{\n"
                    '  "average_sentiment": <float between -1.0 (most negative) and 1.0 (most positive)>,\n'
                    '  "sentiment_label": <"Positive", "Negative", or "Neutral">,\n'
                    '  "summary": <concise 1-2 sentence market catalyst synthesis>\n'
                    "}"
                )

                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                }

                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    candidate = data["candidates"][0]["content"]["parts"][0]["text"]
                    ai_result = json.loads(candidate)

                    avg_sent = round(float(ai_result.get("average_sentiment", 0.0)), 2)
                    label = ai_result.get("sentiment_label", "Neutral")
                    summary = ai_result.get("summary", "")

                    return {
                        "ticker": ticker,
                        "headlines": headlines,
                        "average_sentiment": avg_sent,
                        "sentiment_label": label,
                        "ai_summary": summary,
                        "engine": "Gemini AI",
                    }
            except Exception:
                # Silently fallback to TextBlob if Gemini call fails
                pass

        # TextBlob Fallback
        polarities = [TextBlob(h).sentiment.polarity for h in headlines]
        average_sentiment = round(sum(polarities) / len(polarities), 4)

        if average_sentiment > 0.05:
            sentiment_label = "Positive"
        elif average_sentiment < -0.05:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"

        return {
            "ticker": ticker,
            "headlines": headlines,
            "average_sentiment": average_sentiment,
            "sentiment_label": sentiment_label,
            "ai_summary": "Heuristic polarity generated via TextBlob.",
            "engine": "TextBlob fallback",
        }

    except Exception as exc:
        return {
            "ticker": ticker,
            "headlines": [],
            "average_sentiment": 0.0,
            "sentiment_label": "Neutral",
            "ai_summary": None,
            "engine": "none",
            "error": f"Error fetching news sentiment for '{ticker}': {str(exc)}",
        }
