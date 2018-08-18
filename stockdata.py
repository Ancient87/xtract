# Module that deals with data access to the Morningstar and TBC APIs to create information for the Divgro calculations

import good_morning as gm
import pymysql
from database import db_session
import stockdatamodel.Financial stockdatamodel.Health

class StockData:

#    def init(self, db_host="localhost:", db_user="ancient", db_pass="lolchu", db_name="divgro"):

    def init(self):
#        try:
#            #Setup the DB
#            conn = pymysql.connect(host = db_host, user = db_user, passwd = db_pass, db = db_name)
#            self.db = conn
#        except:
#            print("Unexpected error {0}".format(sys.exc_info()[0]))
#

    def getKeyRatios(self, ticker = "ACN", force_refresh = False)
    """
    This function goes and pulls the financials from the DB if it exists or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec

    :return Ratios object
    """
        # If force go and refresh the ratios
        self._populateKeyRatiosDB(self, ticker)

        # Try to get the Ratios
	key_ratios = self._getRatiosDB

        # If they don't exist error
        raise RatioNotFoundException r:
            print(r)
            return 400, 'Ratios not found for {0}'.format(ticker)


    def _getRatiosDB(self, ticker, force_refresh = False):
        """
        Gets the ratios from the DB if they exist for the given ticker
        return: Ratios from the DB or null
        """
	financials = stockdatamodel.Financial.query.filter=(Financial.ticker = ticker)
	if financials is None:
		self._refreshRatiosDB(self, ticker)
		financials = stockdatamodel.Financial.query.filter=(Financial.ticker = ticker)
	return financials

    def _refreshRatiosDB(self, ticker):
        """
        Uses goodmorning to populate ratios
        """
        gm.KeyRatiosDownloaded()
        kr_frames = kr.download(ticker)

        if kr_frames:
            # Deal with the key ratios and write them to the DB
            financials = kr_frames[0]
            for year in financials:
                series = financials[year]
		    period = series[0]
		    gross_margin = series[1]
		    operating_income = series[2]
		    operating_margin = series[3]
		    net_income = series[4]
		    eps = series[5]
		    dividends = Column(Float)
		    payout_ratio = Column(Float)
		    shares = Column(Integer)
		    bps = Column(Float)
		    operating_cash_flow = Column(Float)
		    cap_spending = Column(Float)
		    fcf = Column(Float)
		    working_capital = Column(Float)

                f = stockdatamodel.Financial(year, )

            # Deal with health and write it to the DB

    def getDividends(self):
        pass

