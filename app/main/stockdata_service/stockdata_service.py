# Module that deals with data access to the Morningstar and TBC APIs to create information for the Divgro calculations

from flask import jsonify
import json
import pickle
from app.main.model.stockdatamodel import *
from app.main.model import stockdatamodel
from app.main import db
from datetime import date, datetime, timedelta
import os
import requests
import logging
import pickle
from app.main.financial_api.financialmodelingprep import FinancialModelingPrep

FINANCIAL_API = "https://financialmodelingprep.com/api/v3"
INCOME_STATEMENT_ENDPOINT = f"{FINANCIAL_API}/income-statement"
COMPANY_KEY_METRICS_ENDPOINT = f"{FINANCIAL_API}/company-key-metrics"
RATIOS_ENDPOINT = f"{FINANCIAL_API}/financial-ratios"
PROFILE_ENDPOINT = f"{FINANCIAL_API}/beta"
DIVIDEND_ENDPOINT = f"{FINANCIAL_API}/historical-price-full/stock_dividend"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class StockDataService:
    def __init__(self):
        #db.session_maker = database.Session
        #db.session = None
        logger.debug("Instantiated StockDataService")
        if not os.path.exists("tmp"):
            logger.debug("Creating tmp dir")
            os.makedirs("tmp")
        self.api = FinancialModelingPrep()


    def _getStockDataResponse(self, key_ratios):
        # Return as per API contract
        return {}

    def getInfo(self, ticker="ACN", exchange="XNYS"):
        logger.debug("Info request for {ticker}".format(ticker=ticker))

        financial = None
        try:
            financial = self._get_financial(ticker).dump()
        except Exception as e:
            logger.exception(
                "Failed to retrieve data for {ticker}".format(ticker=ticker)
            )
            return "Not found", 404

        financial["ratios"] = []
        financial["valuations"] = []

        stockdata = {
            "symbol": ticker,
            "name": financial["company_name"],
            "financials": financial,
            "dividend_history": [],
        }

        return jsonify(stockdata)

    def get_ticker(self, ticker="ACN", refresh=False):
        """
        This function goes and pulls the financials from the DBs if they exist or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec
        :return Ratios object
        """
        
        # Build financials
        logger.debug("Request for {0} forcing_refresh {1}".format(ticker, refresh))
        # financial = {}

        financial = None
        stockdate = None
        ratios = None
        alt_ticker = None

        try:
            financial_item = self._get_financial(ticker, refresh)
            financial = financial_item.dump()
            
            today = datetime.today().date()
            if financial_item.updated.year < today.year or financial_item.updated.month < today.month:
                refresh = True
            # Get Key Ratios (incl health)
            logger.debug(
                f"This is the financial {financial} REFRESH {refresh}"
            )
            
            ratios = [val.dump() for val in self._get_key_ratios(ticker, refresh)]
    
            # Get Valuation
            valuations = [val.dump() for val in self._get_valuation_history(ticker, refresh)]
            logger.debug(valuations)
            

            financial["ratios"] = ratios
            financial["valuations"] = valuations
    
            # TODO: Get Dividend history
            dividend_history = [val.dump() for val in self._get_dividend_history(ticker, refresh)]
            
            if (refresh):
                financial_item.updated = today
                db.session.commit()
    
            # Assemble stock data
            stockdata = {
                "symbol": ticker,
                "name": financial["company_name"],
                "financials": financial,
                "dividend_history": dividend_history,
            }
    
            return jsonify(stockdata)
            
        except Exception as e:
            logger.exception(
                "Failed to retrieve data for {ticker}".format(ticker=ticker)
            )
            return "Not found", 404

        

    def _get_valuation_history(self, ticker="ACN", refresh=False):
        """
        Gets the Valuation from the DB if it exists and isn't 
        forced to be refreshed OR is out of date
        """

        # Try the database
        year_ref = datetime.today().year-1
        year_object = datetime(year_ref, 12, 31)

        query = stockdatamodel.Valuation.query.filter(
            stockdatamodel.Valuation.ticker == ticker
        ).filter(stockdatamodel.Valuation.year == year_object)
        if not refresh and query.count() == 1:
            query = stockdatamodel.Valuation.query.filter(
                stockdatamodel.Valuation.ticker == ticker
            )
            return query.all()

        # Else go and fetch
        data = self.api.get_valuation_history(ticker=ticker, refresh=refresh)
        for valuation_i in data:
            date = datetime.strptime(valuation_i.date, "%Y-%M-%d")
            date = datetime(year=date.year, month=12, day=31)
            query = stockdatamodel.Valuation.query.filter(
                stockdatamodel.Valuation.ticker == ticker
            ).filter(stockdatamodel.Valuation.year == date)
            count = query.count()
            if not refresh and count == 1:
                continue
            elif count < 1:
                # Else build a new one
                valuation = stockdatamodel.Valuation(
                    ticker=ticker, year=date, valuation=valuation_i.valuation
                )
                logger.debug(valuation)
                db.session.add(valuation)
            elif refresh:
                valuation = query.first()
                valuation.valuation = valuation_i.valuation
        db.session.commit()

        query = stockdatamodel.Valuation.query.filter(
            stockdatamodel.Valuation.ticker == ticker
        )
        return query.all()

    def _get_financial(self, ticker="ACN", refresh=False, dirty=False):
        """
        This function pulls the financial from the DB
        :return Financials object
        """
        try:
            # Try looking it up in the database
            q = stockdatamodel.Financial.query.filter(
                stockdatamodel.Financial.ticker == ticker
            )
            financial_item = None
            count = 0
            count = q.count()
            first = None
            updated = None
            if count > 0:
                first = q.first()
                updated = first.updated
            logger.debug("Query for {0} returned {1} results".format(ticker, count))
            today = datetime.today()
            yesterday = datetime.today() - timedelta(days=1)
            # Decide whether to refresh
            if (
                refresh
                or count == 0
                or first == None
                or updated == None
                #or updated < yesterday.date()
            ):
                logger.debug(
                    "Retrieving financials for {0} q.count {1} updated {2}".format(
                        ticker, count, updated
                    )
                )
                data = self.api.get_financial(ticker=ticker, refresh=refresh)

                div_yield = data.dividend_yield
                beta = data.beta
                company_name = data.company_name
                quote = data.quote
                if q.count() == 1:
                    logger.debug(
                        "Entry for {0} already exists - refreshing".format(ticker)
                    )
                    financial_item = q.first()
                    financial_item.beta = beta
                    financial_item.dividend_yield = div_yield
                    financial_item.company_name = company_name
                    financial_item.updated = today
                    financial_item.quote = quote
                    db.session.commit()
                    
                    logger.debug(
                        "Returning financial {financial}".format(financial=financial_item)
                    )
                    
                    return financial_item

                else:
                    financial_item = Financial(
                        ticker=ticker,
                        dividend_yield=div_yield,
                        beta=beta,
                        updated=today,
                        company_name=company_name,
                        quote = quote,
                    )
                    
                    logger.debug(f"Added Financials for {ticker} {financial_item}")
                db.session.add(financial_item)
                db.session.commit()
                return stockdatamodel.Financial.query.filter(
                stockdatamodel.Financial.ticker == ticker
                ).first()
        except Exception as e:
            logger.exception(e)
        else:
            logger.debug("We already have {0} so we are returning it".format(ticker))
            return q.first()

    def _get_key_ratios(self, ticker="ACN", refresh=False):
        """
        This function goes and pulls the financials from the DB if it exists or 
        else (or if forced) reloads the DB. Then is constructs the JSON response 
        required for DivGro and returns it as an object complying with swagger 
        spec.
        """
        try:
            # See if they exist for this month
            today = datetime.today()
            # LAST_YEAR/01/01
            datem = datetime(today.year - 1, 1, 1)

            key_ratios_query = stockdatamodel.Ratio.query.filter(
                stockdatamodel.Ratio.ticker == ticker
            ).filter(stockdatamodel.Ratio.period >= datem)

            ratios = None
            # We need to refresh if we don't have it
            if key_ratios_query.count() < 1:
                refresh = True

            return self._get_ratios_db(ticker=ticker, refresh=refresh)

            # If they don't exist error
        except Exception as e:
            logger.exception(e)
            return 400, "Ratios not found for {0}".format(ticker)

    def _datefromperiod(self, year):
        logger.debug("Converting {0}".format(year))
        return datetime.strptime("{year}-12-31".format(year=year), "%Y-%m-%d")

    def _get_ratios_db(self, ticker, refresh):
        """
        Uses API provider
        """
        if refresh:
            ratios = self.api.get_ratios(ticker=ticker, refresh=refresh)
            if ratios:
                # Deal with the key ratios and write them to the DB
                call = []
                # Key Financials
    
                # Loop through the result
                for year_ratio in ratios:
                    period = year_ratio.date
                    # Check if it exists
                    query = stockdatamodel.Ratio.query.filter(
                        stockdatamodel.Ratio.ticker == ticker
                    ).filter(stockdatamodel.Ratio.period == period)
                    
                    if query.count() < 1:
                        
                        logger.debug(f"Decided to refresh {refresh} {ticker} {period}")
                        f = stockdatamodel.Ratio(
                            ticker=ticker,
                            period=period,
                            revenue=year_ratio.revenue,
                            gross_margin=year_ratio.gross_margin,
                            operating_income=year_ratio.operating_income,
                            operating_margin=year_ratio.operating_margin,
                            net_income=year_ratio.net_income,
                            eps=year_ratio.earnings_per_share,
                            dividends=year_ratio.dividend,
                            payout_ratio=year_ratio.payout_ratio,
                            current_ratio=year_ratio.current_ratio,
                            debt_equity=year_ratio.debt_equity,
                            shares=0.0,
                            bps=0.0,
                            operating_cash_flow=0.0,
                            cap_spending=0.0,
                            fcf=0.0,
                            working_capital=0.0,
                        )
                        db.session.add(f)
    
                    else:
                        f = query.first()
                        logger.debug(f)
                        # If we need to force refresh update it
                        if refresh:
                            logger.debug(f"We are force refreshing {ticker} {period}")
                            # f.ticker = ticker
                            # f.period = period
                            f.revenue = year_ratio.revenue
                            f.gross_margin = year_ratio.gross_margin
                            f.operating_income = year_ratio.operating_income
                            f.operating_margin = year_ratio.operating_margin
                            f.net_income = year_ratio.net_income
                            f.eps = year_ratio.earnings_per_share
                            f.dividends = year_ratio.dividend
                            f.payout_ratio = year_ratio.payout_ratio
                            f.current_ratio = year_ratio.current_ratio
                            f.debt_equity = year_ratio.debt_equity
    
                db.session.commit()

        # Return the thing
        query = stockdatamodel.Ratio.query.filter(
            stockdatamodel.Ratio.ticker == ticker
        )
    
        return query.all()

    def _get_dividend_history(self, ticker, refresh=False):
        """ Retrieves the dividend history for the given ticker

        If we already have it and it's in date (not older than a month) return 
        that. Otherwise we grab it from the API
        """

        # Step 1 Check the database
        try:
            # See if they exist for this year
            today = datetime.today()
            datey = today.year

            # Check if we have any dividends for this year
            # TODO: Optimization to account for checked already
            dividend_history_query = stockdatamodel.Dividend.query.filter(
                stockdatamodel.Dividend.ticker == ticker
            ).filter(stockdatamodel.Dividend.period >= datey)

            # Refresh if need be and return
            if dividend_history_query.count() < 1:
                refresh = True
            res = self._get_dividend_history_db(ticker=ticker, refresh=refresh)
            return res
            # If they don't exist error
        except Exception as e:
            logger.exception(e)
            return 400, "Ratios not found for {0}".format(ticker)

    def _get_dividend_history_db(self, ticker, refresh=False):

        # Only if we don't have last year
        period = self._datefromperiod(datetime.today().year-1)
        # See if we have any dividends already
        query = stockdatamodel.Dividend.query.filter(
            stockdatamodel.Dividend.ticker == ticker
        ).filter(stockdatamodel.Dividend.period >= period)
        if query.count() < 1:
            logger.debug(
                "Don't have this dividend yet {ticker} {period} ".format(
                    ticker=ticker, period=period
                )
            )
            refresh = True
        if refresh:
            dividends = self.api.get_dividend_history(ticker=ticker, refresh = refresh)

            for dividend in dividends:
                query = stockdatamodel.Dividend.query.filter(
                    stockdatamodel.Dividend.ticker == ticker
                ).filter(stockdatamodel.Dividend.period == dividend.date)
                if query.count() > 0:
                    continue
                d = stockdatamodel.Dividend(
                    ticker=ticker, period=dividend.date, dividend=dividend.dividend,
                )
                try:
                    db.session.add(d)
                except Exception as e:
                    logger.debug("Failed to add dividend to DB")

        try:
            db.session.commit()
        except Exception as e:
            #db.session.rollback()
            logger.debug("Failed to commit dividend to DB")

        return stockdatamodel.Dividend.query.filter(
            stockdatamodel.Dividend.ticker == ticker).all()