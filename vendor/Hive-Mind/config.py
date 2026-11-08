"""
Configuration settings for NSE & BSE data fetcher
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for market data fetcher"""
    
    # API Settings
    NSE_BASE_URL = "https://www.nseindia.com"
    BSE_BASE_URL = "https://api.bseindia.com"
    
    # Rate limiting
    REQUEST_DELAY = 1  # seconds between requests
    MAX_RETRIES = 3
    
    # Data settings
    DEFAULT_INTERVAL = '1D'
    MAX_SYMBOLS_PER_REQUEST = 10
    
    # Real-time settings
    REALTIME_UPDATE_INTERVAL = 2  # seconds
    
    # Market hours (IST)
    MARKET_OPEN_TIME = "09:15"
    MARKET_CLOSE_TIME = "15:30"
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Optional API keys (if you have premium data sources)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    QUANDL_API_KEY = os.getenv('QUANDL_API_KEY')
    
    # File paths
    DATA_DIR = 'data'
    CACHE_DIR = 'cache'
    
    @classmethod
    def get_nse_symbols(cls):
        """Get list of popular NSE symbols"""
        return [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'HINDUNILVR', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
            'LT', 'AXISBANK', 'ASIANPAINT', 'MARUTI', 'NESTLEIND'
        ]
    
    @classmethod
    def get_bse_symbols(cls):
        """Get list of popular BSE symbols with their codes"""
        return {
            '500325': 'RELIANCE',
            '532540': 'TCS', 
            '500180': 'HDFCBANK',
            '500209': 'INFY',
            '532174': 'ICICIBANK',
            '500696': 'HINDUNILVR',
            '500112': 'SBIN',
            '532454': 'BHARTIARTL',
            '500875': 'ITC',
            '500247': 'KOTAKBANK'
        }
    
    @classmethod
    def get_intervals(cls):
        """Get supported data intervals"""
        return ['1m', '5m', '15m', '30m', '1H', '1D', '1W', '1M']