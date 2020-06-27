# Handler for reading Tickers

from xtract.stockdata_service import stockdata_service
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

sd = stockdata_service.StockDataService()
logger.debug(f"HELLO FROM{__name__} ")
# Handler for getting a ticker

def get(ticker, force_refresh):
    # Invoke the stock data extractor
    logger.debug(
        f"From the handler Request for {ticker} {force_refresh}"
    )
    return sd.get_ticker(ticker=ticker, refresh=force_refresh)


def put(ticker):
    return 1