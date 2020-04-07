# Handler for reading Tickers
from stockdata_service import stockdata_service
import logging
import database.base

sd = stockdata_service.StockDataService(db_session=database.base.db_session)

# Handler for getting a ticker
def get(ticker, force_refresh):
    # Invoke the stock data extractor
    logging.getLogger(__name__).debug(
        f"From the handler Request for {ticker} {force_refresh}"
    )
    return sd.get_ticker(ticker=ticker, refresh=force_refresh)


def put(ticker):
    return 1
