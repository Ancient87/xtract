# Module that deals with data access to the Morningstar and TBC APIs to create information for the Divgro calculations

from flask import jsonify
import json
import pickle
import traceback
from database.database import db_session
from database.stockdatamodel import *
from database import stockdatamodel
from datetime import date, datetime, timedelta
import os
import requests
import logging
import pickle
import financial_api.financialmodelingprep

FINANCIAL_API = "https://financialmodelingprep.com/api/v3"
INCOME_STATEMENT_ENDPOINT = f"{FINANCIAL_API}/income-statement"
COMPANY_KEY_METRICS_ENDPOINT = f"{FINANCIAL_API}/company-key-metrics"
RATIOS_ENDPOINT = f"{FINANCIAL_API}/financial-ratios"
PROFILE_ENDPOINT = f"{FINANCIAL_API}/beta"
DIVIDEND_ENDPOINT = f"{FINANCIAL_API}/historical-price-full/stock_dividend"

logger = logging.getLogger(__name__)


class StockDataService:
    def __init__(self):
        logger.debug("Instantiated StockDataService")
        if not os.path.exists("tmp"):
            logger.debug("Creating tmp dir")
            os.makedirs("tmp")
        self.api = financial_api.financialmodelingprep.FinancialModelingPrep()

    def _getDividendHistoryDB(self, ticker):
        # TODO: From DB
        return {"dividend_history": []}

    def _getStockDataResponse(self, key_ratios):
        # Return as per API contract
        return {}

    def getInfo(self, ticker="ACN", exchange="XNYS"):
        logger.debug("Info request for {ticker}".format(ticker=ticker))

        financial = None
        try:
            financial = selfself._get_financial(ticker, dirty=True).dump()
        except Exception as e:
            logger.exception(
                "Failed to retrieve data for {ticker}".format(ticker=ticker)
            )
            return "Not found", 404

        financial["ratios"] = []
        financial["valuations"] = []

        stockdata = {
            "symbol": ticker,
            "name": ticker,
            "financials": financial,
            "dividend_history": [],
        }

        return jsonify(stockdata)

    def getTicker(self, ticker="ACN", exchange="XNYS", refresh=False):
        """
        This function goes and pulls the financials from the DBs if they exist or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec
        :return Ratios object
        """

        # Build financials
        logger.debug(
            "Request for {0} forcing_refresh {1}".format(ticker, refresh)
        )
        # financial = {}

        financial = None
        stockdate = None
        ratios = None
        alt_ticker = None

        # Horrendous hack for Morningstar Index specific symbols e.g. "XNAS:MSFT vs MSFT"
        if ":" in ticker:
            alt_ticker = ticker
            ticker = ticker.split(":")[1]
            exchange = ticker.split(":")[0]
            logger.debug(
                ": ticker {ticker} {alt_ticker}".format(
                    ticker=ticker, alt_ticker=alt_ticker
                )
            )
        try:
            financial = self._get_financial(ticker, refresh).dump()
            logger.debug(
                "This is the financial {financial}".format(financial=financial)
            )
        except Exception as e:
            logger.exception(
                "Failed to retrieve data for {ticker}".format(ticker=ticker)
            )
            return "Not found", 404

        # Get Key Ratios (incl health)
        ratios = [
            val.dump()
            for val in self._get_key_ratios(ticker, refresh, exchange=exchange)
        ]

        # Get Valuation
        valuations = [
            val.dump()
            for val in self._getValuations(ticker, refresh, exchange=exchange)
        ]
        logger.debug(valuations)

        financial["ratios"] = ratios
        financial["valuations"] = valuations

        # TODO: Get Dividend history
        dividend_history = [
            val.dump() for val in self._getDividends(ticker, refresh)
        ]

        # Assemble stock data
        stockdata = {
            "symbol": ticker,
            "name": ticker,
            "financials": financial,
            "dividend_history": dividend_history,
        }

        return jsonify(stockdata)

    def _getValuations(self, ticker="ACN", refresh=False, exchange="XNYS"):
        """
        Gets the Valuation from the DB if it exists and isn't forced to be refreshed OR is out of date
        Tries the DB then triest Morningstar via soup
        If soup file exists it won't tax MS
        """

        # Try the database
        year_ref = datetime.today().year
        year_object = datetime(year_ref, 12, 31)

        query = stockdatamodel.Valuation.query.filter(
            stockdatamodel.Valuation.ticker == ticker
        ).filter(stockdatamodel.Valuation.year == year_object)
        if not refresh and query.count() == 1:
            logger.debug("Gotcha")
            query = stockdatamodel.Valuation.query.filter(
                stockdatamodel.Valuation.ticker == ticker
            )
            return query.all()

        # Get the data
        VALUATION_BASE_URL = "http://financials.morningstar.com/valuate/valuation-history.action?&type=price-earnings"
        ms_ticker = ticker
        if ticker != "":
            ms_ticker = "{exchange}:{ticker}".format(exchange=exchange, ticker=ticker)
        # Check the file doesn't exist
        val_file = "tmp/{ticker}_pe".format(ticker=ticker)
        if not os.path.isfile(val_file) or refresh:
            # Get the file from Morningstar
            rurl = "{val_base_url}&t={ms_ticker}".format(
                val_base_url=VALUATION_BASE_URL, ms_ticker=ms_ticker
            )
            # logger.debug("Getting {0}".format(rurl))
            valuations = requests.get(rurl)
            # Write it to tmp
            # logger.debug(valuations.status_code)
            if valuations.status_code == 200:
                try:
                    # logger.debug(valuations.text)
                    with open(val_file, "w") as f:
                        f.write(valuations.text)
                except Exception as e:
                    logger.exception(e)
                    return False

        try:
            with open(val_file, "rb") as f:
                soup = BeautifulSoup(f, "html.parser")
                # <th abbr="Price/Earnings for AAPL" class="row_lbl" scope="row">AAPL</th>
                pe = soup.find(abbr="Price/Earnings for {ticker}".format(ticker=ticker))
                # [<td class="row_data">15.9</td>, <td class="row_data">20.6</td>, <td class="row_data">18</td>, <td class="row_data">14.6</td>, <td class="row_data">12.1</td>, <td class="row_data">14.1</td>, <td class="row_data">17.1</td>, <td class="row_data">11.4</td>, <td class="row_data">13.9</td>, <td class="row_data">18.4</td>, <td class="row_data_0">20.2</td>]
                pes = pe.parent.findAll("td")
                year_ref = datetime.today().year
                year_object = datetime(year_ref, 12, 31)
                valuations = []
                for index, td in enumerate(reversed(pes)):
                    pe = self._sanitise(list(td.children)[0])
                    year = datetime(year_ref - index, 12, 31)
                    # Skip valuations we already have
                    q = Valuation.query.filter(Valuation.year == year).filter(
                        Valuation.ticker == ticker
                    )
                    if q.count() > 0:
                        continue
                    logger.debug(
                        "<year: {year} valuation:{valuation}>".format(
                            year=year, valuation=pe
                        )
                    )
                    valuation = stockdatamodel.Valuation(
                        ticker=ticker, year=year, valuation=pe
                    )
                    logger.debug(valuation)
                    db_session.add(valuation)
                    db_session.commit()

                query = stockdatamodel.Valuation.query.filter(
                    stockdatamodel.Valuation.ticker == ticker
                )
                return query.all()

        except Exception as e:
            logger.exception(e)
            return False

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
                or updated < yesterday.date()
            ):
                logger.debug(
                    "Retrieving financials for {0} q.count {1} updated {2}".format(
                        ticker, count, updated
                    )
                )
                data = self.api.get_financial(
                    ticker=ticker, refresh=refresh
                )

                div_yield = data.dividend_yield
                beta = data.beta
                company_name = data.company_name
                if q.count() == 1:
                    logger.debug(
                        "Entry for {0} already exists - refreshing".format(ticker)
                    )
                    financial = q.first()
                    financial.beta = beta
                    financial.dividend_yield = div_yield
                    financial.company_name = company_name
                    financial.updated = today
                    db_session.commit()
                    logger.debug(
                        "Returning financial {financial}".format(financial=financial)
                    )
                    return financial

                else:
                    f = Financial(
                        ticker=ticker,
                        dividend_yield=div_yield,
                        beta=beta,
                        updated=today,
                        company_name=company_name,
                    )
                    logger.debug("Added Financials for {ticker}".format(ticker=ticker))
                db_session.add(f)
                db_session.commit()
                return f
        except Exception as e:
            logger.exception(e)
        else:
            logger.debug("We already have {0} so we are returning it".format(ticker))
            return q.first()

    def _get_key_ratios(self, ticker="ACN", refresh=False, exchange="XNYS"):
        """
        This function goes and pulls the financials from the DB if it exists or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec

        :return Ratios object
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

    def _sanitise(self, number):
        #       logger.debug("number {0}".format(number))
        if number != number:
            #            logger.debug("{0} is NaN".format(number))
            return 0.0
        try:
            return float(number)
        except Exception as e:
            logger.exception(e)
            return 0.0

    def _get_ratios_db(self, ticker, refresh):
        """
        Uses API provider
        """
        
        ratios = self.api.get_ratios(ticker=ticker,refresh=refresh)
        
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
                if query.count() < 1 or refresh:
                    logger.debug(
                        f"Decided to refresh {refresh} {ticker} {period}"
                    )
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
                    db_session.add(f)
                
                else:
                    f = query.first()
                    logger.debug(f)
                    # If we need to force refresh update it
                    if refresh:
                        logger.debug(
                            f"We are force refreshing {ticker} {period}"
                        )
                        # f.ticker = ticker
                        # f.period = period
                        f.revenue=year_ratio.revenue,
                        f.gross_margin=year_ratio.gross_margin,
                        f.operating_income=year_ratio.operating_income,
                        f.operating_margin=year_ratio.operating_margin,
                        f.net_income=year_ratio.net_income,
                        f.eps=year_ratio.earnings_per_share,
                        f.dividends=year_ratio.dividend,
                        f.payout_ratio=year_ratio.payout_ratio,
                        f.current_ratio=year_ratio.current_ratio,
                        f.debt_equity=year_ratio.debt_equity,
            
            db_session.commit()
            
            # Return the thing
            query = stockdatamodel.Ratio.query.filter(
                    stockdatamodel.Ratio.ticker == ticker
            )
            
            return query.all()

    def _getDividends(self, ticker, refresh=False):
        """ Retrieves the dividend history for the given ticker

        If we already have it and it's in date (not older than a month) return that. Otherwise we
        grab it from yahoo finance

        self -- this class
        ticker -- the ticker symbol of this
        refresh -- refresh even if in date
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
            if refresh or dividend_history_query.count() < 1:
                self._refreshDividendsDB(ticker, refresh)
            # Pull them and return
            dividend_history_query = stockdatamodel.Dividend.query.filter(
                stockdatamodel.Dividend.ticker == ticker
            )
            return dividend_history_query.all()

            # If they don't exist error
        except Exception as e:
            logger.exception(e)
            return 400, "Ratios not found for {0}".format(ticker)

    def _refreshDividendsDB(self, ticker, refresh=False):

        # 1 Use yahoo reader to scrape
        res = []
        dividends = None
        try:
            dividends = yahoo_reader.yahoo_reader.get_dividend(ticker, refresh)
        except Exception as e:
            logger.exception(
                "Failed to parse dividends for {ticker}".format(ticker=ticker)
            )
            return res

        # 2 Add to TB and return
        for index, row in dividends.iterrows():

            period = row[0]
            dividend = row[1]
            # Check if it exists
            query = stockdatamodel.Dividend.query.filter(
                stockdatamodel.Dividend.ticker == ticker
            ).filter(stockdatamodel.Dividend.period == period)
            if query.count() < 1:
                logger.debug(
                    "Don't have this dividend yet {ticker} {period} ".format(
                        ticker=ticker, period=period
                    )
                )
                d = stockdatamodel.Dividend(
                    ticker=ticker, period=period, dividend=dividend,
                )
                try:
                    db_session.add(d)
                    res.append(d)
                except Exception as e:
                    logger.exception("Failed to add dividend to DB")
            else:
                d = query.first()
                # logger.debug(d)
                # If we need to force refresh update it
                if refresh:
                    logger.debug(
                        "We are force refreshing dividend {ticker} {period}".format(
                            ticker=ticker, period=period
                        )
                    )
                    d.dividend = dividend
                res.append(d)
        try:
            db_session.commit()
            return res
        except Exception as e:
            logger.exception("Failed to commit dividend to DB")
