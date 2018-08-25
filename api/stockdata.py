# Handler for reading Tickers
import stockdata_service

sd = stockdata_service.StockDataService()

# Handler for getting a ticker
def get(ticker):
    # Invoke the stock data extractor
    sd.getKeyRatios(ticker, False)
    return 'lol'

def put(ticker):
    return 1
