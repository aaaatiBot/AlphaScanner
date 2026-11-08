"""Test script for AlphaScanner data scraping services."""

from app.services.stock_scraper import get_stock_data
from app.services.news_scraper import get_news_sentiment


def test_ticker(ticker: str) -> None:
    print("=" * 70)
    print(f"Testing Scrapers for Ticker: {ticker}")
    print("=" * 70)

    # 1. Test Stock Data Scraper
    print("\n--- [1] Stock Data ---")
    stock_res = get_stock_data(ticker)

    if "error" in stock_res and stock_res["current_price"] is None:
        print(f"Error fetching stock data: {stock_res['error']}")
    else:
        currency = stock_res.get("currency") or ""
        print(f"Ticker: {stock_res['ticker']}")
        print(f"Current Price: {currency} {stock_res['current_price']}")
        print(f"Change: {stock_res['change_pct']:+}%")

        history_df = stock_res["history_df"]
        print("\nHistorical Data (First 3 rows):")
        if not history_df.empty:
            print(history_df.head(3))
        else:
            print("No historical data available.")

    # 2. Test News Sentiment Scraper
    print("\n--- [2] News Sentiment ---")
    news_res = get_news_sentiment(ticker)

    if "error" in news_res and not news_res["headlines"]:
        print(f"Error fetching news sentiment: {news_res['error']}")
    else:
        print(f"Ticker: {news_res['ticker']}")
        print(f"Average Sentiment Score: {news_res['average_sentiment']}")
        print(f"Sentiment Label: {news_res['sentiment_label']}")
        print("\nTop 3 News Headlines:")
        top_headlines = news_res["headlines"][:3]
        if top_headlines:
            for idx, headline in enumerate(top_headlines, 1):
                print(f"  {idx}. {headline}")
        else:
            print("  No headlines found.")

    print("\n")


def main() -> None:
    tickers = ["AAPL", "RELIANCE.NS"]
    for ticker in tickers:
        test_ticker(ticker)


if __name__ == "__main__":
    main()
