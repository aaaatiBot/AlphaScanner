"""
Utility functions for processing and analyzing market data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

class DataProcessor:
    """Class for processing and analyzing market data"""
    
    @staticmethod
    def technical_analysis(data: List[Dict]) -> List[Dict]:
        """
        Calculate technical indicators for the given data
        
        Args:
            data: List of OHLCV data dictionaries
            
        Returns:
            Data with technical indicators added
        """
        if not data:
            return data
        
        df = pd.DataFrame(data)
        
        # Simple Moving Averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        df['rsi'] = DataProcessor._calculate_rsi(df['close'])
        
        # Bollinger Bands
        bb_data = DataProcessor._calculate_bollinger_bands(df['close'])
        df['bb_upper'] = bb_data['upper']
        df['bb_middle'] = bb_data['middle']
        df['bb_lower'] = bb_data['lower']
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=10).mean()
        
        # Price change indicators
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = df['close'].diff()
        
        return df.to_dict('records')
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    @staticmethod
    def detect_patterns(data: List[Dict]) -> Dict:
        """
        Detect common chart patterns
        
        Args:
            data: List of OHLCV data
            
        Returns:
            Dictionary with detected patterns
        """
        if len(data) < 10:
            return {'patterns': []}
        
        df = pd.DataFrame(data)
        patterns = []
        
        # Detect bullish/bearish trends
        recent_closes = df['close'].tail(5).values
        if len(recent_closes) >= 5:
            if all(recent_closes[i] <= recent_closes[i+1] for i in range(4)):
                patterns.append('Bullish Trend')
            elif all(recent_closes[i] >= recent_closes[i+1] for i in range(4)):
                patterns.append('Bearish Trend')
        
        # Detect support and resistance levels
        highs = df['high'].rolling(window=5).max()
        lows = df['low'].rolling(window=5).min()
        
        current_price = df['close'].iloc[-1]
        resistance_levels = highs[highs > current_price].unique()
        support_levels = lows[lows < current_price].unique()
        
        return {
            'patterns': patterns,
            'resistance_levels': resistance_levels.tolist()[:3] if len(resistance_levels) > 0 else [],
            'support_levels': support_levels.tolist()[:3] if len(support_levels) > 0 else [],
            'current_price': current_price
        }
    
    @staticmethod
    def save_data_to_csv(data: List[Dict], filename: str, directory: str = 'data'):
        """Save data to CSV file"""
        try:
            os.makedirs(directory, exist_ok=True)
            df = pd.DataFrame(data)
            filepath = os.path.join(directory, filename)
            df.to_csv(filepath, index=False)
            print(f"Data saved to {filepath}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    @staticmethod
    def load_data_from_csv(filename: str, directory: str = 'data') -> List[Dict]:
        """Load data from CSV file"""
        try:
            filepath = os.path.join(directory, filename)
            df = pd.read_csv(filepath)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    @staticmethod
    def calculate_portfolio_metrics(holdings: List[Dict]) -> Dict:
        """
        Calculate portfolio-level metrics
        
        Args:
            holdings: List of holdings with symbol, quantity, current_price
            
        Returns:
            Portfolio metrics
        """
        total_value = sum(h['quantity'] * h['current_price'] for h in holdings)
        
        metrics = {
            'total_value': total_value,
            'total_holdings': len(holdings),
            'largest_holding': max(holdings, key=lambda x: x['quantity'] * x['current_price']) if holdings else None,
            'holdings_breakdown': []
        }
        
        for holding in holdings:
            value = holding['quantity'] * holding['current_price']
            percentage = (value / total_value) * 100 if total_value > 0 else 0
            
            metrics['holdings_breakdown'].append({
                'symbol': holding['symbol'],
                'value': value,
                'percentage': round(percentage, 2)
            })
        
        return metrics
    
    @staticmethod
    def format_currency(amount: float, currency: str = 'INR') -> str:
        """Format currency amounts"""
        if currency == 'INR':
            if amount >= 10000000:  # 1 crore
                return f"₹{amount/10000000:.2f} Cr"
            elif amount >= 100000:  # 1 lakh
                return f"₹{amount/100000:.2f} L"
            else:
                return f"₹{amount:,.2f}"
        else:
            return f"{currency} {amount:,.2f}"
    
    @staticmethod
    def get_market_summary(data: List[Dict]) -> Dict:
        """Get summary statistics for market data"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        return {
            'total_records': len(df),
            'date_range': {
                'start': df['timestamp'].min() if 'timestamp' in df.columns else None,
                'end': df['timestamp'].max() if 'timestamp' in df.columns else None
            },
            'price_stats': {
                'current': df['close'].iloc[-1] if len(df) > 0 else None,
                'high': df['high'].max(),
                'low': df['low'].min(),
                'average': df['close'].mean(),
                'volatility': df['close'].std()
            },
            'volume_stats': {
                'total': df['volume'].sum(),
                'average': df['volume'].mean(),
                'max': df['volume'].max()
            }
        }