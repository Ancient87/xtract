from typing import List, Dict
import requests
import pickle
import logging
import os

TMP_DIR = "tmp"

logger = logging.getLogger(__name__)


class FinancialApi:
    def __init__(self, tmp_dir: str = TMP_DIR):
        self.tmp_dir = tmp_dir

    def get_ratios(self, ticker: str = "AMZN") -> List:
        pass

    def get_valuations(self, ticker: str = "AMZN") -> List:
        pass

    def get_dividend_history(self, ticker: str = "AMZN") -> List:
        pass

    def get_financial(self, ticker: str = "AMZN") -> Dict:
        pass

    def _load_and_cache(self, key: str, url: str) -> Dict:
        req = requests.get(url)
        # Write it to tmp
        # logger.debug(valuations.status_code)
        if req.status_code == 200:
            try:
                data = req.json()
                self._store_cache(data=data, key=key)
                return data
            except Exception as e:
                logger.exception(e)
                return False

    def _store_cache(self, key: str, data: Dict) -> bool:
        file_name = f"{self.tmp_dir}/{key}"
        logging.debug(f"Attempting to store in cache {key}")
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "wb+") as f:
            pickle.dump(data, f)
            logging.debug(f"Succeeded to store in cache {key}")
            return True
        logging.debug(f"Failed to store in cache {key}")
        return False

    def _load_cache(self, key: str) -> Dict:
        ret = None
        file_name = f"{self.tmp_dir}/{key}"
        try:
            with open(file_name, "rb") as f:
                ret = pickle.load(f)
        except FileNotFoundError as e:
            return ret
        return ret

    class Financial:
        def __init__(
            self, dividend_yield: str, beta: float, company_name: str,
        ):
            self.dividend_yield = dividend_yield
            self.beta = beta
            self.company_name = company_name

    class Ratio:
        def __init__(
            self,
            date: str,
            revenue: float,
            gross_margin: float,
            operating_income: float,
            operating_margin: float,
            net_income: float,
            earnings_per_share: float,
            dividend: float,
            payout_ratio: float,
            current_ratio: float,
            debt_equity: float,
        ):
            self.date = date
            self.revenue = revenue
            self.gross_margin = gross_margin
            self.operating_income = operating_income
            self.operating_margin = operating_margin
            self.net_income = net_income
            self.earnings_per_share = earnings_per_share
            self.dividend = dividend
            self.payout_ratio = payout_ratio
            self.current_ratio = current_ratio
            self.debt_equity = debt_equity

    class Valuation:
        def __init__(self, date: str, valuation: float):
            self.date = date
            self.valuation = valuation

    class DividendPayment:
        def __init__(
            self, date: str, dividend_yield: float,
        ):
            self.date = date
            self.dividend_yield = dividend_yield
