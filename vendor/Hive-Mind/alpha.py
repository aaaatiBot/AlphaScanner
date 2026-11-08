import requests
import os
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def json_to_csv(data, filename_prefix='alpha_vantage'):
    """Convert Alpha Vantage JSON response to CSV files"""
    
    if 'feed' not in data:
        print("No 'feed' data found in JSON response")
        return
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Extract articles data
    articles = []
    ticker_sentiments = []
    topics = []
    
    for article in data['feed']:
        # Main article data
        article_row = {
            'title': article.get('title', ''),
            'url': article.get('url', ''),
            'time_published': article.get('time_published', ''),
            'authors': ', '.join(article.get('authors', [])),
            'summary': article.get('summary', ''),
            'banner_image': article.get('banner_image', ''),
            'source': article.get('source', ''),
            'source_domain': article.get('source_domain', ''),
            'overall_sentiment_score': article.get('overall_sentiment_score', ''),
            'overall_sentiment_label': article.get('overall_sentiment_label', '')
        }
        articles.append(article_row)
        
        # Ticker sentiment data
        for ticker_info in article.get('ticker_sentiment', []):
            ticker_row = {
                'article_title': article.get('title', ''),
                'time_published': article.get('time_published', ''),
                'ticker': ticker_info.get('ticker', ''),
                'relevance_score': ticker_info.get('relevance_score', ''),
                'ticker_sentiment_score': ticker_info.get('ticker_sentiment_score', ''),
                'ticker_sentiment_label': ticker_info.get('ticker_sentiment_label', '')
            }
            ticker_sentiments.append(ticker_row)
        
        # Topics data
        for topic_info in article.get('topics', []):
            topic_row = {
                'article_title': article.get('title', ''),
                'time_published': article.get('time_published', ''),
                'topic': topic_info.get('topic', ''),
                'relevance_score': topic_info.get('relevance_score', '')
            }
            topics.append(topic_row)
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save to CSV files
    csv_files = []
    
    if articles:
        articles_df = pd.DataFrame(articles)
        articles_file = f'data/{filename_prefix}_articles_{timestamp}.csv'
        articles_df.to_csv(articles_file, index=False, encoding='utf-8')
        csv_files.append(articles_file)
        print(f"✅ Articles saved to: {articles_file} ({len(articles)} rows)")
    
    if ticker_sentiments:
        ticker_df = pd.DataFrame(ticker_sentiments)
        ticker_file = f'data/{filename_prefix}_ticker_sentiments_{timestamp}.csv'
        ticker_df.to_csv(ticker_file, index=False, encoding='utf-8')
        csv_files.append(ticker_file)
        print(f"✅ Ticker sentiments saved to: {ticker_file} ({len(ticker_sentiments)} rows)")
    
    if topics:
        topics_df = pd.DataFrame(topics)
        topics_file = f'data/{filename_prefix}_topics_{timestamp}.csv'
        topics_df.to_csv(topics_file, index=False, encoding='utf-8')
        csv_files.append(topics_file)
        print(f"✅ Topics saved to: {topics_file} ({len(topics)} rows)")
    
    # Also save the raw JSON for reference
    json_file = f'data/{filename_prefix}_raw_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    csv_files.append(json_file)
    print(f"✅ Raw JSON saved to: {json_file}")
    
    return csv_files

# Fetch the data and convert to CSV
url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=TCS.NS&apikey={os.getenv("ALPHA_VANTAGE_API_KEY")}'
r = requests.get(url)
data = r.json()

print("📊 Converting JSON to CSV files...")
print(f"📈 API Response contains {len(data.get('feed', []))} articles")

# Convert to CSV
csv_files = json_to_csv(data, 'aapl_news_sentiment')

print(f"\n🎉 Conversion complete! {len(csv_files)} files created:")
for file in csv_files:
    print(f"   📁 {file}")