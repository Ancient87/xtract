import unittest
import stockdata_service
from xtract import *
from test import *
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class StockDataTestCase(unittest.TestCase):
    def setUp(self):
        self.sd = stockdata_service.stockdata_service.StockDataService()
    
    def test_ticker(self):
        with application.app_context():
            logger.debug(f"Gettings Ticker for {TEST_TICKER}")
            ticker = self.sd.get_ticker(TEST_TICKER, refresh=FORCE_REFRESH)
            logger.debug(ticker)
    
    def test_financial(self):
        with application.app_context():
            logger.debug(f"Gettings Ticker for {TEST_TICKER}")
            financial = self.sd._get_financial(
                ticker=TEST_TICKER, refresh=FORCE_REFRESH
            )
            assert financial.company_name == TEST_COMPANY_NAME

    def test_ratios(self):
        with application.app_context():
            logger.debug(f"Gettings ratios for {TEST_TICKER}")
            ratios = self.sd._get_key_ratios(ticker=TEST_TICKER, refresh=FORCE_REFRESH)
            assert len(ratios) > 0
            ratio_one = ratios[0]
            assert isinstance(ratio_one.revenue, float)
            assert ratio_one.revenue != 0.0

    def test_valuations(self):
        with application.app_context():
            logger.debug(f"Gettings valuation for {TEST_TICKER}")
            valuations = self.sd._get_valuation_history(
                ticker=TEST_TICKER, refresh=FORCE_REFRESH
            )
            assert len(valuations) > 0
            valuation_one = valuations[0]
            assert isinstance(valuation_one.valuation, float)
            assert valuation_one.valuation != 0.0

    def test_dividends(self):
        with application.app_context():
            logger.debug(f"Gettings dividend history for {TEST_TICKER}")
            dividends = self.sd._get_dividend_history(
                ticker=TEST_TICKER, refresh=FORCE_REFRESH
            )
            assert len(dividends) > 0
            div_one = dividends[0]
            assert isinstance(div_one.ticker, str)
            assert div_one.ticker == TEST_TICKER


if __name__ == "__main__":
    unittest.main()
