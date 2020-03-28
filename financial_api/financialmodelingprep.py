from financial_api.financial_api import FinancialApi
import requests
from typing import List, Dict
import pickle
import logging

logger = logging.getLogger(__name__)

FINANCIAL_API = "https://financialmodelingprep.com/api/v3"
INCOME_STATEMENT_ENDPOINT = f"{FINANCIAL_API}/financials/income-statement"
COMPANY_KEY_METRICS_ENDPOINT = f"{FINANCIAL_API}/company-key-metrics"
RATIOS_ENDPOINT = f"{FINANCIAL_API}/financial-ratios"
PROFILE_ENDPOINT = f"{FINANCIAL_API}/profile"
DIVIDEND_ENDPOINT = f"{FINANCIAL_API}/historical-price-full/stock_dividend"
TMP_DIR = f"tmp"

DATA_TYPE_INCOME_STATEMENT = "income_statement"
DATA_TYPE_COMPANY_KEY_METRICS = "company_key_metrics"
DATA_TYPE_FINANCIAL_RATIOS = "financial_ratios"
DATA_TYPE_PROFILE = "profile"
DATA_TYPE_DIVIDEND_HISTORY = "dividend_history"

class FinancialModelingPrep(FinancialApi):
    
    def __init__(self):
        super().__init__()
    
    def _get_cache_key(self, ticker:str, data_type: str):
        return f"{ticker}/{data_type}"
    
    
    def _get_data(self, ticker:str, data_type: str, refresh = False):
        # Try and load it
        key = self._get_cache_key(ticker = ticker, data_type = data_type)
        if not refresh:
            logger.debug(f"Attempting to load {key}")
            stored_data = self._load_cache(key = key)
            if stored_data:
                return stored_data
        # If we get here we need to retrieve it
        url = f"{INCOME_STATEMENT_ENDPOINT}/{ticker}"
        logger.debug(f"Attempting to refresh {url}")
        data = self._load_and_cache(url = url ,key = key)
        
        return data
    
    def _get_income_statement(self, ticker:str, refresh = False):
        return self._get_data(
            ticker = ticker, data_type = DATA_TYPE_INCOME_STATEMENT, refresh = refresh
        )
        
    def _get_company_key_metrics(self, ticker:str, refresh = False):
        return self._get_data(
            ticker = ticker, data_type = DATA_TYPE_COMPANY_KEY_METRICS, refresh = refresh
        )
    
    def _get_financial_ratios(self, ticker:str, refresh = False):
        return self._get_data(
            ticker = ticker, data_type = DATA_TYPE_FINANCIAL_RATIOS, refresh = refresh
        )
    
    def _get_profile(self, ticker:str, refresh = False):
        return self._get_data(
            ticker = ticker, data_type = DATA_TYPE_PROFILE, refresh = refresh
        )
        
    def _get_dividends(self, ticker:str, refresh = False):
        return self._get_data(
            ticker = ticker, data_type = DATA_TYPE_DIVIDEND_HISTORY, refresh = refresh
        )
    
    def get_ratios(self, ticker:str = "AMZN", refresh=False) -> List[FinancialApi.Ratio]:
        pass
    
    def get_valuations(self, ticker:str = "AMZN", refresh=False) -> List[FinancialApi.Valuation]:
        pass
    
    def get_dividend_history(self, ticker:str = "AMZN", refresh=False) ->List[FinancialApi.DividendPayment]:
        pass