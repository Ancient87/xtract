import unittest
import financial_api
import financial_api.financialmodelingprep
import logging

logger = logging.getLogger(__name__)

TEST_TICKER="MSFT"
FORCE_REFRESH = False

class DatabaseConnectionTestCase(unittest.TestCase):
    def setUp(self):
        print("Setting up the ModelingAPI")
        self.prep = financial_api.financialmodelingprep.FinancialModelingPrep()
        
    def test_get_income_statement(self):
        data = self.prep._get_financial_ratios(ticker = TEST_TICKER, refresh = FORCE_REFRESH)
        logger.debug(f"The data is {data}")
        assert len(data.keys()) > 1
        
    def test_get_company_key_matrics(self):
        data = self.prep._get_company_key_metrics(ticker = TEST_TICKER, refresh = FORCE_REFRESH)
        logger.debug(f"The data is {data}")
        assert len(data.keys()) > 1
        
    def test_get_profile(self):
        data = self.prep._get_profile(ticker = TEST_TICKER, refresh = FORCE_REFRESH)
        logger.debug(f"The data is {data}")
        assert len(data.keys()) > 1
        
    def test_get_financials_ratios(self):
        data = self.prep._get_financial_ratios(ticker = TEST_TICKER, refresh = FORCE_REFRESH)
        logger.debug(f"The data is {data}")
        assert len(data.keys()) > 1
        
    def test_get_dividends(self):
        data = self.prep._get_dividends(ticker = TEST_TICKER, refresh = FORCE_REFRESH)
        logger.debug(f"The data is {data}")
        assert len(data.keys()) > 1
    
if __name__ == "__main__":
    print("Here we go ")
    unittest.main()