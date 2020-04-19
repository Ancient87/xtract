from financial_api.financial_api import FinancialApi
import requests
from typing import List, Dict
import pickle
import logging

logger = logging.getLogger(__name__)

FINANCIAL_API = "https://financialmodelingprep.com/api/v3"
ENDPOINT_INCOME_STATEMENT = f"{FINANCIAL_API}/financials/income-statement"
ENDPOINT_COMPANY_KEY_METRICS = f"{FINANCIAL_API}/company-key-metrics"
ENDPOINT_RATIOS = f"{FINANCIAL_API}/financial-ratios"
ENDPOINT_PROFILE = f"{FINANCIAL_API}/company/profile"
ENDPOINT_DIVIDEND = f"{FINANCIAL_API}/historical-price-full/stock_dividend"

TMP_DIR = f"tmp"

DATA_TYPE_RATIOS = "ratios"
DATA_TYPE_INCOME_STATEMENT = "income_statement"
DATA_TYPE_COMPANY_KEY_METRICS = "company_key_metrics"
DATA_TYPE_FINANCIAL_RATIOS = "financial_ratios"
DATA_TYPE_PROFILE = "profile"
DATA_TYPE_DIVIDEND_HISTORY = "dividend_history"

ENDPOINTS = {
    DATA_TYPE_RATIOS: ENDPOINT_RATIOS,
    DATA_TYPE_INCOME_STATEMENT: ENDPOINT_INCOME_STATEMENT,
    DATA_TYPE_COMPANY_KEY_METRICS: ENDPOINT_COMPANY_KEY_METRICS,
    DATA_TYPE_FINANCIAL_RATIOS: ENDPOINT_RATIOS,
    DATA_TYPE_PROFILE: ENDPOINT_PROFILE,
    DATA_TYPE_DIVIDEND_HISTORY: ENDPOINT_DIVIDEND,
}


class FinancialModelingPrep(FinancialApi):
    def __init__(self):
        super().__init__()

    def _get_cache_key(self, ticker: str, data_type: str):
        return f"{ticker}/{data_type}"

    def get_ratios(self, ticker: str, refresh=False) -> List[FinancialApi.Ratio]:
        # Get cache
        key = self._get_cache_key(ticker=ticker, data_type=DATA_TYPE_RATIOS)
        stored_data = self._load_cache(key=key)
        if stored_data:
            return stored_data
        # Or we need to derive it

        # We need income_statement, and company_key_metrics
        income_statements = self._get_income_statement(ticker=ticker)
        income_statements = income_statements["financials"]
        income_statements = sorted(
            income_statements, key=lambda year: year["date"], reverse=True
        )

        company_key_metrics = self._get_company_key_metrics(ticker=ticker)
        company_key_metrics = company_key_metrics["metrics"]
        company_key_metrics = sorted(
            company_key_metrics, key=lambda year: year["date"], reverse=True
        )

        key_ratios = []

        for income_statement, company_key_metric in zip(
            income_statements, company_key_metrics
        ):
            # get the matching company key metrics
            if not income_statement["date"] == company_key_metric["date"]:
                logger.critical(
                    f"Can't merge {ticker} IS:{income_statement['date']} and IS:{company_key_metric['date']}"
                )
                return None
            ratio = FinancialApi.Ratio(
                date=income_statement["date"],
                revenue=income_statement["Revenue"],
                gross_margin=income_statement["Gross Margin"],
                operating_income=income_statement["Operating Income"],
                operating_margin=income_statement["Gross Margin"],
                net_income=income_statement["Net Income"],
                earnings_per_share=income_statement["EPS"],
                dividend=income_statement["Dividend per Share"],
                payout_ratio=company_key_metric["Payout Ratio"],
                current_ratio=company_key_metric["Current ratio"],
                debt_equity=company_key_metric["Debt to Equity"],
            )

            key_ratios.append(ratio)

        # TODO: CACHE RESULT

        return key_ratios

    def get_financial(self, ticker: str = "AMZN", refresh=False):
        # Get cache
        key = self._get_cache_key(ticker=ticker, data_type=DATA_TYPE_RATIOS)
        stored_data = self._load_cache(key=key)
        if stored_data:
            return stored_data
        # Or we need to derive it profile, financial-ratios
        profile = self._get_profile(ticker=ticker, refresh=refresh)["profile"]
        financial_ratios = self._get_financial_ratios(ticker=ticker, refresh=refresh)[
            "ratios"
        ][0]

        financial = FinancialApi.Financial(
            dividend_yield=financial_ratios["investmentValuationRatios"][
                "dividendYield"
            ],
            beta=profile["beta"],
            company_name=profile["companyName"],
        )

        return financial

    def get_valuation_history(
        self, ticker: str = "AMZN", refresh=False
    ) -> List[FinancialApi.Valuation]:
        # TODO cache
        valuation_history = self._get_financial_ratios(ticker=ticker, refresh=refresh)[
            "ratios"
        ]
        valuations = []
        for valuation in valuation_history:
            ivrs = valuation["investmentValuationRatios"]
            valuation = FinancialApi.Valuation(
                date=valuation["date"], valuation=ivrs["priceEarningsRatio"],
            )

            valuations.append(valuation)
        return valuations

    def get_dividend_history(
        self, ticker: str = "AMZN", refresh=False
    ) -> List[FinancialApi.DividendPayment]:

        # TODO cache
        dividend_history = self._get_dividend_history(ticker=ticker, refresh=refresh)
        dividends = []
        for dividend in dividend_history["historical"]:
            dividend = FinancialApi.DividendPayment(
                date=dividend["date"], dividend=dividend["adjDividend"]
            )

            dividends.append(dividend)
        return dividends

    def _get_data_api(self, ticker: str, data_type: str, refresh=False):
        key = self._get_cache_key(ticker=ticker, data_type=data_type)
        stored_data = self._load_cache(key=key)
        if stored_data and not refresh:
            return stored_data
        # If we get here we need to retrieve it
        url = f"{ENDPOINTS[data_type]}/{ticker}"
        logger.debug(f"Attempting to refresh {url}")
        data = self._load_and_cache(url=url, key=key)

        return data

    def _get_income_statement(self, ticker: str, refresh=False):
        return self._get_data_api(
            ticker=ticker, data_type=DATA_TYPE_INCOME_STATEMENT, refresh=refresh
        )

    def _get_company_key_metrics(self, ticker: str, refresh=False):
        return self._get_data_api(
            ticker=ticker, data_type=DATA_TYPE_COMPANY_KEY_METRICS, refresh=refresh
        )

    def _get_financial_ratios(self, ticker: str, refresh=False):
        return self._get_data_api(
            ticker=ticker, data_type=DATA_TYPE_FINANCIAL_RATIOS, refresh=refresh
        )

    def _get_profile(self, ticker: str, refresh=False):
        return self._get_data_api(
            ticker=ticker, data_type=DATA_TYPE_PROFILE, refresh=refresh
        )

    def _get_dividend_history(self, ticker: str, refresh=False):
        return self._get_data_api(
            ticker=ticker, data_type=DATA_TYPE_DIVIDEND_HISTORY, refresh=refresh
        )
