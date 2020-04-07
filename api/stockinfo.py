from stockdata_service import stockdata_service
import logging
import database.base


db_session = database.base.db_session

sd = stockdata_service.StockDataService(db_session=db_session)

# Handler for getting a ticker
def get(ticker):
    # Invoke the stock data extractor
    logging.getLogger(__name__).debug("From the handler Request for {0}".format(ticker))
    return sd.getInfo(ticker, exchange="")


def put(ticker):
    return 1
