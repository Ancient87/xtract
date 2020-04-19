# Handler for reading Tickers
from stockdata_service import stockdata_service
import logging
import database.base

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

#breakpoint()

sd = stockdata_service.StockDataService(db_session=database.base.db_session)
logger.debug(f"I just created a new session and who knows why?")
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
