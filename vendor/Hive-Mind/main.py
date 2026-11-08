"""
NSE & BSE Tick Data Fetcher
Supports both historical and real-time data fetching
"""

import asyncio
import logging
from datetime import datetime, timedelta
from market_data_fetcher import MarketDataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Main function to demonstrate tick data fetching"""
    
    # Initialize the market data fetcher
    fetcher = MarketDataFetcher()
    
    # Example symbols
    nse_symbols = ['RELIANCE']               #, 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    bse_symbols = ['500325', '532540', '500209', '500180', '532174']  # BSE codes
    
    print("=== NSE & BSE Tick Data Fetcher ===\n")
    
    # Menu for user selection
    while True:
        print("\nSelect an option:")
        print("1. Get Historical Data (NSE)")
        print("2. Get Historical Data (BSE)")
        print("3. Start Real-time Data Stream (NSE)")
        print("4. Start Real-time Data Stream (BSE)")
        print("5. Download Stock Data (Custom Timeframe & Timeline)")
        print("6. Get Current Market Status")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            await handle_historical_nse(fetcher, nse_symbols)
        elif choice == '2':
            await handle_historical_bse(fetcher, bse_symbols)
        elif choice == '3':
            await handle_realtime_nse(fetcher, nse_symbols)
        elif choice == '4':
            await handle_realtime_bse(fetcher, bse_symbols)
        elif choice == '5':
            await handle_download_stock_data(fetcher)
        elif choice == '6':
            await handle_market_status(fetcher)
        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")



async def handle_historical_nse(fetcher, symbols):
    """Handle historical NSE data fetching"""
    print(f"\nFetching historical data for NSE symbols: {symbols}")
    
    # Get data for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for symbol in symbols[:2]:  # Limit to first 2 symbols for demo
        try:
            data = await fetcher.get_historical_data(
                symbol=symbol,
                exchange='NSE',
                start_date=start_date,
                end_date=end_date,
                interval='1D'
            )
            
            if data:
                print(f"\n{symbol} - Last 5 records:")
                for record in data[-5:]:
                    print(f"  {record}")
            else:
                print(f"No data found for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")


# BSE
async def handle_historical_bse(fetcher, symbols):
    """Handle historical BSE data fetching"""
    print(f"\nFetching historical data for BSE symbols: {symbols}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for symbol in symbols[:2]:  # Limit to first 2 symbols for demo
        try:
            data = await fetcher.get_historical_data(
                symbol=symbol,
                exchange='BSE',
                start_date=start_date,
                end_date=end_date,
                interval='1D'
            )
            
            if data:
                print(f"\nBSE {symbol} - Last 5 records:")
                for record in data[-5:]:
                    print(f"  {record}")
            else:
                print(f"No data found for BSE {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching BSE data for {symbol}: {e}")



async def handle_realtime_nse(fetcher, symbols):
    """Handle real-time NSE data streaming"""
    print(f"\nStarting real-time data stream for NSE symbols: {symbols[:3]}")
    print("Press Ctrl+C to stop the stream\n")
    
    try:
        async for tick_data in fetcher.get_realtime_data(symbols[:3], 'NSE'):
            print(f"[{tick_data['timestamp']}] {tick_data['symbol']}: "
                  f"LTP={tick_data['ltp']}, Volume={tick_data['volume']}")
    except Exception as e:
        logger.error(f"Error in real-time stream: {e}")



async def handle_realtime_bse(fetcher, symbols):
    """Handle real-time BSE data streaming"""
    print(f"\nStarting real-time data stream for BSE symbols: {symbols[:3]}")
    print("Press Ctrl+C to stop the stream\n")
    
    try:
        async for tick_data in fetcher.get_realtime_data(symbols[:3], 'BSE'):
            print(f"[{tick_data['timestamp']}] BSE {tick_data['symbol']}: "
                  f"LTP={tick_data['ltp']}, Volume={tick_data['volume']}")
            
    except KeyboardInterrupt:
        print("\nReal-time stream stopped by user")
    except Exception as e:
        logger.error(f"Error in BSE real-time stream: {e}")



async def handle_download_stock_data(fetcher):
    """Handle custom stock data download with selectable timeframe and timeline"""
    print("\n=== Download Stock Data ===")
    
    # Get user inputs
    symbol = input("Enter stock symbol (e.g., RELIANCE, TCS): ").strip().upper()
    if not symbol:
        print("Invalid symbol. Please try again.")
        return
    
    # Exchange selection
    print("\nSelect Exchange:")
    print("1. NSE")
    print("2. BSE")
    exchange_choice = input("Enter choice (1-2): ").strip()
    
    if exchange_choice == '1':
        exchange = 'NSE'
    elif exchange_choice == '2':
        exchange = 'BSE'
    else:
        print("Invalid choice. Using NSE as default.")
        exchange = 'NSE'
    
    # Timeframe selection
    print("\nSelect Timeframe (Data Interval):")
    print("1. 1 minute (1m)")
    print("2. 5 minutes (5m)")
    print("3. 15 minutes (15m)")
    print("4. 30 minutes (30m)")
    print("5. 1 hour (1h)")
    print("6. 1 day (1d)")
    print("7. 1 week (1wk)")
    print("8. 1 month (1mo)")
    
    timeframe_choice = input("Enter choice (1-8): ").strip()
    timeframe_map = {
        '1': '1m', '2': '5m', '3': '15m', '4': '30m',
        '5': '1h', '6': '1d', '7': '1wk', '8': '1mo'
    }
    timeframe = timeframe_map.get(timeframe_choice, '1d')
    
    # Timeline selection
    print("\nSelect Timeline (Data Period):")
    print("1. 1 day (1d)")
    print("2. 5 days (5d)")
    print("3. 1 month (1mo)")
    print("4. 3 months (3mo)")
    print("5. 6 months (6mo)")
    print("6. 1 year (1y)")
    print("7. 2 years (2y)")
    print("8. 5 years (5y)")
    print("9. 10 years (10y)")
    print("10. Year to date (ytd)")
    print("11. Max available (max)")
    
    timeline_choice = input("Enter choice (1-11): ").strip()
    timeline_map = {
        '1': '1d', '2': '5d', '3': '1mo', '4': '3mo', '5': '6mo',
        '6': '1y', '7': '2y', '8': '5y', '9': '10y', '10': 'ytd', '11': 'max'
    }
    timeline = timeline_map.get(timeline_choice, '1y')
    
    # File format selection
    print("\nSelect File Format:")
    print("1. CSV")
    print("2. JSON")
    print("3. Excel")
    
    format_choice = input("Enter choice (1-3): ").strip()
    format_map = {'1': 'csv', '2': 'json', '3': 'excel'}
    file_format = format_map.get(format_choice, 'csv')
    
    # Confirm download
    print(f"\n📋 Download Summary:")
    print(f"   Symbol: {symbol}")
    print(f"   Exchange: {exchange}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Timeline: {timeline}")
    print(f"   Format: {file_format.upper()}")
    
    confirm = input("\nProceed with download? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Download cancelled.")
        return
    
    try:
        print(f"\n🔄 Downloading {symbol} data...")
        
        # Download the data
        data = await fetcher.download_stock_data(
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            timeline=timeline,
            save_to_file=True,
            file_format=file_format
        )
        
        if not data.empty:
            print(f"\n✅ Download completed successfully!")
            print(f"   Records downloaded: {len(data)}")
            print(f"   Date range: {data['Date'].min().strftime('%Y-%m-%d')} to {data['Date'].max().strftime('%Y-%m-%d')}")
            
            # Show sample data
            print(f"\n📊 Sample data (first 5 records):")
            print(data.head().to_string(index=False))
            
            # Show summary statistics
            print(f"\n📈 Summary Statistics:")
            print(f"   Highest: {data['High'].max():.2f}")
            print(f"   Lowest: {data['Low'].min():.2f}")
            print(f"   Latest Close: {data['Close'].iloc[-1]:.2f}")
            print(f"   Average Volume: {data['Volume'].mean():.0f}")
            
        else:
            print(f"❌ No data found for {symbol} on {exchange}")
            
    except Exception as e:
        logger.error(f"Error downloading data for {symbol}: {e}")
        print(f"❌ Error downloading data: {e}")

async def handle_market_status(fetcher):
    """Handle market status check"""
    try:
        nse_status = await fetcher.get_market_status('NSE')
        bse_status = await fetcher.get_market_status('BSE')
        
        print(f"\nNSE Market Status: {nse_status}")
        print(f"BSE Market Status: {bse_status}")
        
    except Exception as e:
        logger.error(f"Error fetching market status: {e}")

if __name__ == "__main__":
    asyncio.run(main())