# Handler for reading Tickers
from stockdata_service import stockdata_service
import logging

sd = stockdata_service.StockDataService()

# Handler for getting a ticker
def get(ticker, force_refresh, exchange):
    # Invoke the stock data extractor
    logging.getLogger(__name__).debug("From the handler Request for {0} {1} {2}".format(ticker, force_refresh, exchange))
    return sd.getTicker(ticker = ticker, exchange = exchange, force_refresh = force_refresh)


def put(ticker):
    return 1
