# Handler for reading Tickers
from stockdata_service import stockdata_service

sd = stockdata_service.StockDataService()

# Handler for getting a ticker
def get(ticker):
    # Invoke the stock data extractor
    return sd.getTicker(ticker, False)


def put(ticker):
    return 1
