import unittest
import stockdata_service
from xtract import *
from test import *
from flask import current_app

class StockDataTestCase(unittest.TestCase):
    def setUp(self):

        self.sd = stockdata_service.stockdata_service.StockDataService()

    '''
    def testRatios(self):
        with application.app_context():
            print("Gettings Ticker for AAPL")
            ticker = self.sd.getTicker("AAPL", force_refresh=False)
            print(ticker)
        """
        ratios = self.sd.getTicker("AMZN", force_refresh = False)
        for ratio in ratios:
            print(ratio)
        """
    '''
    
    def test_financial(self):
        with application.app_context():
            print("Gettings Ticker for AAPL")
            financial = self.sd._get_financial(ticker = TEST_TICKER)
            assert financial.company_name == TEST_COMPANY_NAME
            
    
        


if __name__ == "__main__":
    unittest.main()
