# Handler for reading Tickers
import stockdata_service

sd = stockdata_service.StockDataService()

# Handler for getting a ticker
def get(ticker):
    # Invoke the stock data extractor
    return [f.dump() for f in sd.getKeyRatios(ticker, False)]


def put(ticker):
    return 1
