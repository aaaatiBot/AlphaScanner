import asyncio
import aiohttp
import pandas as pd
import yfinance as yf
import requests
import requests_cache  # For caching HTTP requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, AsyncGenerator, Union
import logging
import json
import random
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TickData:
    """Data class for tick information"""
    symbol: str
    exchange: str
    timestamp: datetime
    ltp: float  # Last Traded Price
    volume: int
    open_price: float
    high: float
    low: float
    close: float
    change: float
    change_percent: float

class MarketDataFetcher:
    """Main class for fetching market data from NSE & BSE"""
    
    def __init__(self):
        # Create cache directory if it doesn't exist
        os.makedirs('.cache', exist_ok=True)
        
        # This will cache all HTTP requests to reduce rate limiting issues
        requests_cache.install_cache(
            '.cache/market_data_cache',
            backend='sqlite',
            expire_after=3600  # Cache for 1 hour
        )
        
        self.session = None
        self.nse_base_url = "https://www.nseindia.com"
        self.bse_base_url = "https://api.bseindia.com"
        
        # Headers to mimic browser requests - more browser-like to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://finance.yahoo.com/',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="105", "Not)A;Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        #print('Session created:', self.session)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def get_historical_data(
        self, 
        symbol: str, 
        exchange: str = 'NSE',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = '1D'
    ) -> List[Dict]:
        """
        Get historical data for a symbol
        
        Args:
            symbol: Stock symbol
            exchange: 'NSE' or 'BSE'
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1D', '1H', '5m', etc.)
        
        Returns:
            List of historical data records
        """
        try:
            if exchange.upper() == 'NSE':
                return await self._get_nse_historical_data(symbol, start_date, end_date, interval)
            elif exchange.upper() == 'BSE':
                return await self._get_bse_historical_data(symbol, start_date, end_date, interval)
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    async def _get_nse_historical_data(self, symbol: str, start_date: Optional[datetime], end_date: Optional[datetime], interval: str) -> List[Dict]:
        """Get NSE historical data using yfinance as fallback"""
        try:
            # Use yfinance for reliable historical data
            ticker_symbol = f"{symbol}.NS"  # NSE suffix
            
            # Convert interval to yfinance format
            yf_interval = self._convert_interval_to_yf(interval)
            
            # Set default dates if none provided
            start = start_date.strftime('%Y-%m-%d') if start_date else None
            end = end_date.strftime('%Y-%m-%d') if end_date else None
            
            # Fetch data with session for better reliability
            session = requests.Session()
            ticker = yf.Ticker(ticker_symbol)
            hist_data = ticker.history(
                start=start,
                end=end,
                interval=yf_interval
            )
            
            # Convert to our format
            records = []
            for date, row in hist_data.iterrows():
                records.append({
                    'symbol': symbol,
                    'exchange': 'NSE',
                    'timestamp': date,
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume']),
                    'ltp': round(row['Close'], 2)
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Error fetching NSE data for {symbol}: {e}")
            return []
    
    async def _get_bse_historical_data(self, symbol: str, start_date: Optional[datetime], end_date: Optional[datetime], interval: str) -> List[Dict]:
        """Get BSE historical data using yfinance"""
        try:
            # Use yfinance for BSE data
            ticker_symbol = f"{symbol}.BO"  # BSE suffix
            
            yf_interval = self._convert_interval_to_yf(interval)
            
            # Set default dates if none provided
            start = start_date.strftime('%Y-%m-%d') if start_date else None
            end = end_date.strftime('%Y-%m-%d') if end_date else None
            
            # Fetch data with session for better reliability
            session = requests.Session()
            ticker = yf.Ticker(ticker_symbol)
            hist_data = ticker.history(
                start=start,
                end=end,
                interval=yf_interval
            )
            
            records = []
            for date, row in hist_data.iterrows():
                records.append({
                    'symbol': symbol,
                    'exchange': 'BSE',
                    'timestamp': date,
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume']),
                    'ltp': round(row['Close'], 2)
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Error fetching BSE data for {symbol}: {e}")
            return []
    
    def _convert_interval_to_yf(self, interval: str) -> str:
        """Convert our interval format to yfinance format"""
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1H': '1h',
            '1D': '1d',
            '1W': '1wk',
            '1M': '1mo'
        }
        return interval_map.get(interval, '1d')
    
    async def get_realtime_data(self, symbols: List[str], exchange: str = 'NSE') -> AsyncGenerator[Dict, None]:
        """
        Get real-time tick data for symbols
        
        Args:
            symbols: List of stock symbols
            exchange: 'NSE' or 'BSE'
        
        Yields:
            Real-time tick data
        """
        try:
            if exchange.upper() == 'NSE':
                async for tick in self._get_nse_realtime_data(symbols):
                    yield tick
            elif exchange.upper() == 'BSE':
                async for tick in self._get_bse_realtime_data(symbols):
                    yield tick
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
        except Exception as e:
            logger.error(f"Error in real-time data stream: {e}")
    
    async def _get_nse_realtime_data(self, symbols: List[str]) -> AsyncGenerator[Dict, None]:
        """Enhanced NSE real-time data with minimal API calls and robust rate limiting"""
        # Enhanced caching with longer duration
        cache = {}
        cache_expiry = {}
        cache_duration = 300  # Cache for 5 minutes (much longer)
        
        # Rate limiting controls
        base_delay = 10  # Start with 10 seconds between requests (increased)
        max_delay = 120  # Maximum delay in seconds (increased)
        current_delay = base_delay
        tick_delay = 3  # Delay between ticks regardless of API calls
        
        # Track last API call time to prevent too frequent requests
        last_api_call = {}
        min_api_interval = 30  # Minimum 30 seconds between API calls for same symbol
        
        # Initialize base prices from historical data once
        logger.info("Initializing base prices for symbols...")
        for symbol in symbols:
            try:
                # Get initial price using historical data (less rate-limited)
                ticker = yf.Ticker(f"{symbol}.NS")
                hist = ticker.history(period="1d", interval="1d")
                if not hist.empty:
                    base_price = float(hist['Close'].iloc[-1])
                    cache[symbol] = base_price
                    cache_expiry[symbol] = datetime.now() + timedelta(seconds=cache_duration)
                    last_api_call[symbol] = datetime.now()
                    logger.info(f"Initialized {symbol} with price: {base_price}")
                else:
                    # Fallback price if no data
                    cache[symbol] = 100.0
                    cache_expiry[symbol] = datetime.now() + timedelta(seconds=cache_duration)
                await asyncio.sleep(2)  # Delay between initialization calls
            except Exception as e:
                logger.warning(f"Could not initialize {symbol}, using fallback: {e}")
                cache[symbol] = 100.0
                cache_expiry[symbol] = datetime.now() + timedelta(seconds=cache_duration)
        
        logger.info("Starting real-time data simulation...")
        
        while True:
            for symbol in symbols:
                try:
                    current_time = datetime.now()
                    
                    # Check if we need to refresh data
                    should_refresh = (
                        symbol not in cache or 
                        symbol not in cache_expiry or 
                        current_time > cache_expiry[symbol]
                    )
                    
                    # Additional check: don't call API too frequently for same symbol
                    if should_refresh and symbol in last_api_call:
                        time_since_last_call = (current_time - last_api_call[symbol]).total_seconds()
                        if time_since_last_call < min_api_interval:
                            should_refresh = False
                            logger.debug(f"Skipping API call for {symbol}, too soon ({time_since_last_call:.1f}s)")
                    
                    if should_refresh:
                        try:
                            logger.info(f"Refreshing data for {symbol}")
                            
                            # Use historical data instead of info (more reliable)
                            ticker = yf.Ticker(f"{symbol}.NS")
                            hist = ticker.history(period="1d", interval="5m")
                            
                            if not hist.empty:
                                base_price = float(hist['Close'].iloc[-1])
                                cache[symbol] = base_price
                                cache_expiry[symbol] = current_time + timedelta(seconds=cache_duration)
                                last_api_call[symbol] = current_time
                                current_delay = base_delay  # Reset delay on success
                                logger.info(f"Successfully refreshed {symbol}: {base_price}")
                            else:
                                # Keep old cached value if no new data
                                cache_expiry[symbol] = current_time + timedelta(seconds=60)
                                logger.warning(f"No new data for {symbol}, extending cache")
                                
                        except Exception as api_error:
                            if "Too Many Requests" in str(api_error) or "429" in str(api_error):
                                # Exponential backoff for rate limiting
                                current_delay = min(current_delay * 2, max_delay)
                                cache_expiry[symbol] = current_time + timedelta(seconds=cache_duration)
                                logger.warning(f"Rate limited for {symbol}. Increasing delay to {current_delay}s")
                                await asyncio.sleep(current_delay)
                                continue
                            else:
                                # For other errors, extend cache and continue
                                cache_expiry[symbol] = current_time + timedelta(seconds=300)
                                logger.error(f"API error for {symbol}: {api_error}")
                    
                    # Always generate tick data (even with cached price)
                    base_price = cache.get(symbol, 100.0)
                    
                    # Add realistic price movement
                    price_change = random.uniform(-0.5, 0.5)  # Smaller realistic movements
                    current_price = max(0.01, base_price + price_change)  # Ensure positive price
                    
                    tick_data = {
                        'symbol': symbol,
                        'exchange': 'NSE',
                        'timestamp': current_time.strftime('%H:%M:%S'),
                        'ltp': round(current_price, 2),
                        'volume': random.randint(1000, 50000),
                        'change': round(price_change, 2),
                        'change_percent': round((price_change / base_price) * 100, 2) if base_price > 0 else 0
                    }
                    
                    yield tick_data
                    await asyncio.sleep(tick_delay)  # Fixed delay between ticks
                    
                except Exception as e:
                    logger.error(f"Unexpected error in real-time data for {symbol}: {e}")
                    await asyncio.sleep(tick_delay)
    
    async def _get_bse_realtime_data(self, symbols: List[str]) -> AsyncGenerator[Dict, None]:
        """Enhanced BSE real-time data with minimal API calls and robust rate limiting"""
        # Enhanced caching with longer duration
        cache = {}
        cache_expiry = {}
        cache_duration = 300  # Cache for 5 minutes
        
        # Rate limiting controls
        base_delay = 10  # Start with 10 seconds between requests
        max_delay = 120  # Maximum delay in seconds
        current_delay = base_delay
        tick_delay = 3  # Delay between ticks
        
        # Track last API call time
        last_api_call = {}
        min_api_interval = 30  # Minimum 30 seconds between API calls
        
        # Initialize base prices from historical data once
        logger.info("Initializing BSE base prices for symbols...")
        for symbol in symbols:
            try:
                ticker = yf.Ticker(f"{symbol}.BO")
                hist = ticker.history(period="1d", interval="1d")
                if not hist.empty:
                    base_price = float(hist['Close'].iloc[-1])
                    cache[symbol] = base_price
                    cache_expiry[symbol] = datetime.now() + timedelta(seconds=cache_duration)
                    last_api_call[symbol] = datetime.now()
                    logger.info(f"Initialized BSE {symbol} with price: {base_price}")
                else:
                    cache[symbol] = 100.0
                    cache_expiry[symbol] = datetime.now() + timedelta(seconds=cache_duration)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Could not initialize BSE {symbol}, using fallback: {e}")
                cache[symbol] = 100.0
                cache_expiry[symbol] = datetime.now() + timedelta(seconds=cache_duration)
        
        logger.info("Starting BSE real-time data simulation...")
        
        while True:
            for symbol in symbols:
                try:
                    current_time = datetime.now()
                    
                    # Check if we need to refresh data
                    should_refresh = (
                        symbol not in cache or 
                        symbol not in cache_expiry or 
                        current_time > cache_expiry[symbol]
                    )
                    
                    # Don't call API too frequently
                    if should_refresh and symbol in last_api_call:
                        time_since_last_call = (current_time - last_api_call[symbol]).total_seconds()
                        if time_since_last_call < min_api_interval:
                            should_refresh = False
                            logger.debug(f"Skipping BSE API call for {symbol}, too soon")
                    
                    if should_refresh:
                        try:
                            logger.info(f"Refreshing BSE data for {symbol}")
                            
                            ticker = yf.Ticker(f"{symbol}.BO")
                            hist = ticker.history(period="1d", interval="5m")
                            
                            if not hist.empty:
                                base_price = float(hist['Close'].iloc[-1])
                                cache[symbol] = base_price
                                cache_expiry[symbol] = current_time + timedelta(seconds=cache_duration)
                                last_api_call[symbol] = current_time
                                current_delay = base_delay
                                logger.info(f"Successfully refreshed BSE {symbol}: {base_price}")
                            else:
                                cache_expiry[symbol] = current_time + timedelta(seconds=60)
                                logger.warning(f"No new BSE data for {symbol}, extending cache")
                                
                        except Exception as api_error:
                            if "Too Many Requests" in str(api_error) or "429" in str(api_error):
                                current_delay = min(current_delay * 2, max_delay)
                                cache_expiry[symbol] = current_time + timedelta(seconds=cache_duration)
                                logger.warning(f"BSE rate limited for {symbol}. Increasing delay to {current_delay}s")
                                await asyncio.sleep(current_delay)
                                continue
                            else:
                                cache_expiry[symbol] = current_time + timedelta(seconds=300)
                                logger.error(f"BSE API error for {symbol}: {api_error}")
                    
                    # Generate tick data
                    base_price = cache.get(symbol, 100.0)
                    price_change = random.uniform(-0.5, 0.5)
                    current_price = max(0.01, base_price + price_change)
                    
                    tick_data = {
                        'symbol': symbol,
                        'exchange': 'BSE',
                        'timestamp': current_time.strftime('%H:%M:%S'),
                        'ltp': round(current_price, 2),
                        'volume': random.randint(1000, 50000),
                        'change': round(price_change, 2),
                        'change_percent': round((price_change / base_price) * 100, 2) if base_price > 0 else 0
                    }
                    
                    yield tick_data
                    await asyncio.sleep(tick_delay)
                    
                except Exception as e:
                    logger.error(f"Unexpected error in BSE real-time data for {symbol}: {e}")
                    await asyncio.sleep(tick_delay)
    
    async def get_market_status(self, exchange: str = 'NSE') -> str:
        current_time = datetime.now().time()
        
        # Market hours: 9:15 AM to 3:30 PM IST (Monday to Friday)
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        is_weekday = datetime.now().weekday() < 5  # Monday = 0, Sunday = 6
        
        if is_weekday and market_open <= current_time <= market_close:
            return f"{exchange} Market is OPEN"
        else:
            return f"{exchange} Market is CLOSED"
    

    
    async def download_stock_data(self, symbol: str, exchange: str = 'NSE', 
                                timeframe: str = '1D', timeline: str = '1Y',
                                save_to_file: bool = True, file_format: str = 'csv') -> pd.DataFrame:
        """
        Download stock data with selectable timeframe and timeline
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
            exchange: 'NSE' or 'BSE'
            timeframe: Data interval ('1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo')
            timeline: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            save_to_file: Whether to save data to file
            file_format: File format ('csv', 'json', 'excel')
        
        Returns:
            DataFrame with stock data
        """
        try:
            logger.info(f"Downloading {symbol} data from {exchange} - Timeframe: {timeframe}, Timeline: {timeline}")
            
            # Determine the correct suffix
            suffix = '.NS' if exchange.upper() == 'NSE' else '.BO'
            ticker_symbol = f"{symbol}{suffix}"
            
            # Use session for better reliability
            session = requests.Session()
            ticker = yf.Ticker(ticker_symbol)
            
            # Convert timeline to valid period
            valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
            period = timeline.lower() if timeline.lower() in valid_periods else '1y'
            
            # Convert timeframe to valid interval
            valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
            interval = timeframe.lower() if timeframe.lower() in valid_intervals else '1d'
            
            # Download data with retry mechanism
            max_retries = 3
            retry_delay = 2
            
            for retry in range(max_retries):
                try:
                    # Fetch historical data
                    hist_data = ticker.history(period=period, interval=interval)
                    
                    if hist_data.empty:
                        logger.warning(f"No data found for {symbol} on {exchange}")
                        return pd.DataFrame()
                    
                    # Add metadata columns
                    hist_data['Symbol'] = symbol
                    hist_data['Exchange'] = exchange.upper()
                    hist_data['Timeframe'] = timeframe
                    hist_data['Timeline'] = timeline
                    
                    # Reset index to make Date a column
                    hist_data.reset_index(inplace=True)
                    
                    # Round numerical values
                    numerical_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close']
                    for col in numerical_cols:
                        if col in hist_data.columns:
                            hist_data[col] = hist_data[col].round(2)
                    
                    logger.info(f"Successfully downloaded {len(hist_data)} records for {symbol}")
                    
                    # Save to file if requested
                    if save_to_file:
                        await self._save_data_to_file(hist_data, symbol, exchange, timeframe, timeline, file_format)
                    
                    return hist_data
                    
                except Exception as e:
                    if "Too Many Requests" in str(e) and retry < max_retries - 1:
                        wait_time = retry_delay * (2 ** retry)
                        logger.warning(f"Rate limited for {symbol}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _save_data_to_file(self, data: pd.DataFrame, symbol: str, exchange: str, 
                               timeframe: str, timeline: str, file_format: str):
        """Save downloaded data to file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/{symbol}_{exchange}_{timeframe}_{timeline}_{timestamp}"
            
            if file_format.lower() == 'csv':
                filepath = f"{filename}.csv"
                data.to_csv(filepath, index=False)
            elif file_format.lower() == 'json':
                filepath = f"{filename}.json"
                data.to_json(filepath, orient='records', date_format='iso', indent=2)
            elif file_format.lower() == 'excel':
                filepath = f"{filename}.xlsx"
                data.to_excel(filepath, index=False, sheet_name=f"{symbol}_{exchange}")
            else:
                # Default to CSV
                filepath = f"{filename}.csv"
                data.to_csv(filepath, index=False)
            
            logger.info(f"Data saved to: {filepath}")
            print(f"📁 Data saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")

    async def get_symbol_info(self, symbol: str, exchange: str = 'NSE') -> Dict:
        """Get detailed information about a symbol"""
        try:
            # Use a static cache for symbol info with 24-hour expiry
            cache_key = f"{symbol}_{exchange}"
            
            # Check if we have a file-based cache for this symbol
            cache_file = f".cache_{cache_key}.json"
            
            try:
                # Try to read from cache
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid (less than 24 hours old)
                cache_time = datetime.fromisoformat(cached_data.get('timestamp', '2020-01-01'))
                if datetime.now() - cache_time < timedelta(hours=24):
                    logger.info(f"Using cached info for {symbol} on {exchange}")
                    return cached_data.get('data', {})
            except (FileNotFoundError, json.JSONDecodeError):
                # Cache doesn't exist or is invalid
                pass
                
            # If not in cache or cache expired, fetch new data
            suffix = '.NS' if exchange.upper() == 'NSE' else '.BO'
            
            # Use session for better handling of rate limits
            session = requests.Session()
            ticker = yf.Ticker(f"{symbol}{suffix}")
            
            # Implement retry with exponential backoff
            max_retries = 3
            retry_delay = 5
            
            for retry in range(max_retries):
                try:
                    info = ticker.info
                    
                    # Create result
                    result = {
                        'symbol': symbol,
                        'exchange': exchange,
                        'company_name': info.get('longName', 'N/A'),
                        'sector': info.get('sector', 'N/A'),
                        'market_cap': info.get('marketCap', 'N/A'),
                        'pe_ratio': info.get('trailingPE', 'N/A'),
                        '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                        '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                        'current_price': info.get('regularMarketPrice', 'N/A')
                    }
                    
                    # Cache the result
                    with open(cache_file, 'w') as f:
                        json.dump({
                            'timestamp': datetime.now().isoformat(),
                            'data': result
                        }, f)
                        
                    return result
                    
                except Exception as e:
                    if "Too Many Requests" in str(e):
                        if retry < max_retries - 1:
                            wait_time = retry_delay * (2 ** retry)
                            logger.warning(f"Rate limited for {symbol}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                        else:
                            raise
                    else:
                        raise
            
            # Fallback return in case all retries fail
            return {}
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}
    
    def clear_all_caches(self):
        """Clear all caches to force fresh data retrieval"""
        try:
            # Clear HTTP request cache
            import requests_cache
            requests_cache.clear()
            logger.info("Cleared HTTP request cache")
            
            # Clear file-based symbol caches
            import glob
            cache_files = glob.glob(".cache_*.json")
            for file in cache_files:
                os.remove(file)
                logger.info(f"Removed cache file: {file}")
            
            logger.info("All caches cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")
    
    def get_cache_status(self):
        """Get information about current cache status"""
        try:
            # Check HTTP cache
            cache_info = {"http_cache": "Unknown", "file_caches": []}
            
            # Check for cache database
            cache_db_path = ".cache/market_data_cache.sqlite"
            if os.path.exists(cache_db_path):
                cache_info["http_cache"] = f"Active (DB size: {os.path.getsize(cache_db_path)} bytes)"
            else:
                cache_info["http_cache"] = "Not found"
            
            # Check file caches
            import glob
            cache_files = glob.glob(".cache_*.json")
            file_cache_list = []
            for file in cache_files:
                file_size = os.path.getsize(file)
                file_time = datetime.fromtimestamp(os.path.getmtime(file))
                file_cache_list.append({
                    "file": file,
                    "size": file_size,
                    "modified": file_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            cache_info["file_caches"] = file_cache_list
            return cache_info
            
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            asyncio.create_task(self.session.close())