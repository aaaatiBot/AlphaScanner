"""
Example usage of the NSE & BSE tick data fetcher
"""

import asyncio
from datetime import datetime, timedelta
from market_data_fetcher import MarketDataFetcher
from data_utils import DataProcessor
from config import Config

async def example_historical_analysis():
    """Example: Fetch and analyze historical data"""
    print("=== Historical Data Analysis Example ===\n")
    
    fetcher = MarketDataFetcher()
    processed_data = DataProcessor()
    
    # Fetch historical data for RELIANCE
    symbol = 'RELIANCE'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Last 3 months
    
    print(f"Fetching 3 months of data for {symbol}...")
    
    data = await fetcher.get_historical_data(
        symbol=symbol,
        exchange='NSE',
        start_date=start_date,
        end_date=end_date,
        interval='1D'
    )
    
    #print(type(data), f'\n {data}')

    if data:
        print(f"Retrieved {len(data)} records")
        
        # Add technical indicators
        print("Calculating technical indicators...")
        data_with_indicators = processed_data.technical_analysis(data)
        
        # Get latest data with indicators
        latest = data_with_indicators[-1]
        print(f"\nLatest data for {symbol}:")
        print(f"  Price: ₹{latest['close']:.2f}")
        print(f"  RSI: {latest.get('rsi', 'N/A'):.2f}" if latest.get('rsi') else "  RSI: N/A")
        print(f"  SMA(20): ₹{latest.get('sma_20', 'N/A'):.2f}" if latest.get('sma_20') else "  SMA(20): N/A")
        
        # Detect patterns
        patterns = processed_data.detect_patterns(data)
        print(f"\nDetected patterns: {patterns.get('patterns', [])}")
        
        # Save data
        processed_data.save_data_to_csv(data_with_indicators, f"{symbol}_historical.csv")
        
        # Get market summary
        summary = processed_data.get_market_summary(data)
        print(f"\nMarket Summary:")
        print(f"  Records: {summary['total_records']}")
        print(f"  Price Range: ₹{summary['price_stats']['low']:.2f} - ₹{summary['price_stats']['high']:.2f}")
        print(f"  Average Volume: {summary['volume_stats']['average']:,.0f}")

async def example_multi_symbol_comparison():
    """Example: Compare multiple symbols"""
    print("\n=== Multi-Symbol Comparison Example ===\n")
    
    fetcher = MarketDataFetcher()
    symbols = ['RELIANCE', 'TCS', 'INFY']
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    comparison_data = {}
    
    for symbol in symbols:
        print(f"Fetching data for {symbol}...")
        data = await fetcher.get_historical_data(
            symbol=symbol,
            exchange='NSE',
            start_date=start_date,
            end_date=end_date
        )
        
        if data:
            # Calculate returns
            first_price = data[0]['close']
            last_price = data[-1]['close']
            returns = ((last_price - first_price) / first_price) * 100
            
            comparison_data[symbol] = {
                'start_price': first_price,
                'end_price': last_price,
                'returns': returns,
                'records': len(data)
            }
    
    # Display comparison
    print("\n30-Day Performance Comparison:")
    print("-" * 50)
    for symbol, metrics in comparison_data.items():
        print(f"{symbol:10} | ₹{metrics['start_price']:8.2f} → ₹{metrics['end_price']:8.2f} | {metrics['returns']:+6.2f}%")

async def example_realtime_monitoring():
    """Example: Monitor real-time data with alerts"""
    print("\n=== Real-time Monitoring Example ===\n")
    
    fetcher = MarketDataFetcher()
    symbols = ['RELIANCE', 'TCS']
    
    # Set up price alerts
    price_alerts = {
        'RELIANCE': {'upper': 2500, 'lower': 2300},
        'TCS': {'upper': 3500, 'lower': 3200}
    }
    
    print(f"Monitoring {symbols} for price alerts...")
    print("Price Alerts:")
    for symbol, alerts in price_alerts.items():
        print(f"  {symbol}: Alert if price > ₹{alerts['upper']} or < ₹{alerts['lower']}")
    
    print("\nReal-time data (Press Ctrl+C to stop):")
    print("-" * 60)
    
    try:
        tick_count = 0
        async for tick_data in fetcher.get_realtime_data(symbols, 'NSE'):
            tick_count += 1
            symbol = tick_data['symbol']
            price = tick_data['ltp']
            
            # Check alerts
            alert_msg = ""
            if symbol in price_alerts:
                alerts = price_alerts[symbol]
                if price > alerts['upper']:
                    alert_msg = " 🔴 HIGH ALERT!"
                elif price < alerts['lower']:
                    alert_msg = " 🟡 LOW ALERT!"
            
            print(f"[{tick_data['timestamp']}] {symbol:8} | ₹{price:8.2f} | Vol: {tick_data['volume']:6,}{alert_msg}")
            
            # Stop after 20 ticks for demo
            if tick_count >= 20:
                print("\nDemo completed (20 ticks received)")
                break
                
    except KeyboardInterrupt:
        print("\nReal-time monitoring stopped by user")

async def example_portfolio_tracking():
    """Example: Track a sample portfolio"""
    print("\n=== Portfolio Tracking Example ===\n")
    
    fetcher = MarketDataFetcher()
    processed_data = DataProcessor()
    
    # Sample portfolio
    portfolio = [
        {'symbol': 'RELIANCE', 'quantity': 100, 'exchange': 'NSE'},
        {'symbol': 'TCS', 'quantity': 50, 'exchange': 'NSE'},
        {'symbol': 'INFY', 'quantity': 75, 'exchange': 'NSE'}
    ]
    
    print("Sample Portfolio:")
    print("-" * 40)
    
    portfolio_with_prices = []
    
    for holding in portfolio:
        # Get current price
        symbol_info = await fetcher.get_symbol_info(holding['symbol'], holding['exchange'])
        current_price = symbol_info.get('current_price', 0)
        
        holding_with_price = {
            **holding,
            'current_price': current_price,
            'company_name': symbol_info.get('company_name', 'N/A')
        }

        print(type(holding_with_price), f'\n {holding_with_price}')

        portfolio_with_prices.append(holding_with_price)
        
        value = holding['quantity'] * current_price
        print(f"{holding['symbol']:8} | {holding['quantity']:3} shares | ₹{current_price:8.2f} | {processed_data.format_currency(value)}")
    
    # Calculate portfolio metrics
    metrics = processed_data.calculate_portfolio_metrics(portfolio_with_prices)
    
    print(f"\nPortfolio Summary:")
    print(f"Total Value: {processed_data.format_currency(metrics['total_value'])}")
    print(f"Total Holdings: {metrics['total_holdings']}")
    
    print(f"\nHoldings Breakdown:")
    for breakdown in metrics['holdings_breakdown']:
        print(f"  {breakdown['symbol']:8} | {processed_data.format_currency(breakdown['value'])} ({breakdown['percentage']:.1f}%)")




async def main():
    """Run all examples"""
    print("NSE & BSE Market Data Fetcher - Examples\n")
    
    examples = [
        ("Historical Analysis", example_historical_analysis),
        ("Multi-Symbol Comparison", example_multi_symbol_comparison),
        ("Portfolio Tracking", example_portfolio_tracking),
        ("Real-time Monitoring", example_realtime_monitoring)
    ]

    print("Available analyses:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    choice = input("\nSelect example to run (1-4, or 'all'): ").strip()
    
    if choice.lower() == 'all':
        for name, func in examples:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print('='*60)
            await func()
            await asyncio.sleep(2)  # Brief pause between examples
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func = examples[int(choice) - 1]
        print(f"\nRunning: {name}")
        await func()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())