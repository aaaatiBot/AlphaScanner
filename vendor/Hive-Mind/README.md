# NSE & BSE Tick Data Fetcher

A comprehensive Python application to fetch historical and real-time tick data from NSE (National Stock Exchange) and BSE (Bombay Stock Exchange).

## Features

- **Historical Data**: Fetch OHLCV data for any time period
- **Real-time Data**: Stream live tick data for multiple symbols
- **Technical Indicators**: Calculate RSI, MACD, Bollinger Bands, Moving Averages
- **Pattern Detection**: Identify bullish/bearish trends and support/resistance levels
- **Portfolio Tracking**: Monitor portfolio performance and metrics
- **Multi-Exchange Support**: Works with both NSE and BSE
- **Data Export**: Save data to CSV for further analysis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nse-bse-tick-data
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the main application:
```bash
python main.py
```

This will present you with a menu to:
1. Get Historical Data (NSE)
2. Get Historical Data (BSE)
3. Start Real-time Data Stream (NSE)
4. Start Real-time Data Stream (BSE)
5. Get Current Market Status
6. Exit

### Advanced Examples

Run the examples script to see advanced usage:
```bash
python examples.py
```

### Programmatic Usage

```python
import asyncio
from datetime import datetime, timedelta
from market_data_fetcher import MarketDataFetcher
from data_utils import DataProcessor

async def fetch_data():
    fetcher = MarketDataFetcher()
    
    # Get historical data
    data = await fetcher.get_historical_data(
        symbol='RELIANCE',
        exchange='NSE',
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        interval='1D'
    )
    
    # Add technical indicators
    processor = DataProcessor()
    data_with_indicators = processor.calculate_technical_indicators(data)
    
    return data_with_indicators

# Run the function
data = asyncio.run(fetch_data())
```

## Supported Symbols

### NSE Symbols
- RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK
- HINDUNILVR, SBIN, BHARTIARTL, ITC, KOTAKBANK
- LT, AXISBANK, ASIANPAINT, MARUTI, NESTLEIND

### BSE Symbols (with codes)
- 500325 (RELIANCE), 532540 (TCS), 500180 (HDFCBANK)
- 500209 (INFY), 532174 (ICICIBANK), 500696 (HINDUNILVR)
- 500112 (SBIN), 532454 (BHARTIARTL), 500875 (ITC)

## Data Intervals

Supported intervals for historical data:
- `1m`, `5m`, `15m`, `30m` - Intraday intervals
- `1H` - Hourly
- `1D` - Daily (default)
- `1W` - Weekly
- `1M` - Monthly

## Technical Indicators

The application calculates the following technical indicators:
- **Moving Averages**: SMA (5, 10, 20), EMA (12, 26)
- **MACD**: MACD line, Signal line, Histogram
- **RSI**: Relative Strength Index (14-period)
- **Bollinger Bands**: Upper, Middle, Lower bands
- **Volume Indicators**: Volume SMA

## Configuration

Edit `config.py` to customize:
- API endpoints and rate limits
- Default intervals and symbols
- Market hours
- Data directories

## Data Sources

The application uses multiple data sources:
- **yfinance**: Primary source for historical data
- **NSE/BSE APIs**: For real-time data (when available)
- **Fallback mechanisms**: Ensures data availability

## Market Hours

- **NSE/BSE Trading Hours**: 9:15 AM to 3:30 PM IST (Monday to Friday)
- **Pre-market**: 9:00 AM to 9:15 AM IST
- **Post-market**: 3:40 PM to 4:00 PM IST

## Error Handling

The application includes comprehensive error handling:
- Network timeouts and retries
- Invalid symbol handling
- Market closure detection
- Rate limiting compliance

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the main application: `python main.py`
3. Select option 1 to fetch historical NSE data
4. Try option 3 for real-time data streaming

## File Structure

```
├── main.py                 # Main application entry point
├── market_data_fetcher.py  # Core data fetching logic
├── data_utils.py          # Data processing and analysis utilities
├── config.py              # Configuration settings
├── examples.py            # Advanced usage examples
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This software is for educational and research purposes only. It is not intended for live trading or investment decisions. Always verify data from official sources before making financial decisions.

## Roadmap

- [ ] WebSocket support for real-time data
- [ ] More technical indicators
- [ ] Options and futures data
- [ ] Database integration
- [ ] Web dashboard
- [ ] Mobile app support