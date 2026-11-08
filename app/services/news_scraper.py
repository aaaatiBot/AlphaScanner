"""News sentiment fetching service using Google News RSS and TextBlob."""

import urllib.parse
from typing import Any, Dict, List
import feedparser
from textblob import TextBlob


def get_news_sentiment(ticker: str) -> Dict[str, Any]:
    """Fetch top news headlines for a ticker and compute average sentiment polarity.

    Args:
        ticker: The stock ticker symbol (e.g. 'AAPL', 'RELIANCE.NS').

    Returns:
        dict: A dictionary containing:
            - ticker (str): The requested ticker symbol.
            - headlines (List[str]): Top 5 headlines from the RSS feed.
            - average_sentiment (float): Average sentiment polarity score (-1.0 to 1.0).
            - sentiment_label (str): "Positive", "Negative", or "Neutral".
            - error (str, optional): Error message if fetching or parsing fails.
    """
    if not ticker or not isinstance(ticker, str):
        return {
            "ticker": ticker,
            "headlines": [],
            "average_sentiment": 0.0,
            "sentiment_label": "Neutral",
            "error": "A valid non-empty string ticker must be provided.",
        }

    ticker = ticker.strip()

    try:
        # Construct Google News RSS query URL
        query = urllib.parse.quote_plus(f"{ticker} stock news")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

        # Parse RSS feed
        feed = feedparser.parse(rss_url)

        # Extract up to 5 headlines
        headlines: List[str] = [entry.title for entry in feed.entries[:5]]

        # Calculate sentiment polarity using TextBlob
        if headlines:
            polarities = [TextBlob(h).sentiment.polarity for h in headlines]
            average_sentiment = round(sum(polarities) / len(polarities), 4)
        else:
            average_sentiment = 0.0

        # Determine sentiment label
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
        }

    except Exception as exc:
        return {
            "ticker": ticker,
            "headlines": [],
            "average_sentiment": 0.0,
            "sentiment_label": "Neutral",
            "error": f"Error fetching news sentiment for '{ticker}': {str(exc)}",
        }
