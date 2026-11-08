import yfinance as yf

# Example: Infosys (NSE)
ticker = yf.Ticker("INFY.NS")   # .NS for NSE

# Get historical data
data = ticker.history(period="1y", interval="1d")  
# period can be "1d", "5d", "1mo", "6mo", "1y", "5y", "max"
# interval can be "1m","5m","15m","1h","1d","1wk","1mo"

# Save as CSV / Excel
data.to_csv("INFY.csv")
#data.to_excel("INFY.xlsx")

print(data.head())
