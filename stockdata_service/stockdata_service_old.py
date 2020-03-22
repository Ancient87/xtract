# Module that deals with data access to the Morningstar and TBC APIs to create information for the Divgro calculations

from flask import jsonify
import json
import pickle
import traceback
import good_morning as gm
import pymysql
from database.database import db_session
from database.stockdatamodel import *
from database import stockdatamodel
from datetime import date, datetime, timedelta
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yahoo_reader.yahoo_reader
import logging
import pickle

FINANCIAL_API = "https://financialmodelingprep.com/api/v3"

logger = logging.getLogger(__name__)


class StockDataService:
    def __init__(self):
        logger.debug("Instantiated StockDataService")
        if not os.path.exists("tmp"):
            logger.debug("Creating tmp dir")
            os.makedirs("tmp")
        """
        try:
            #Setup the DB
            database.init_db()
            #conn = pymysql.connect(host = db_host, user = db_user, passwd = db_pass, db = db_name)
            #self.db = conn
        except Exception as e:
            logger.exception(e)
        """

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
            financial = self._getFinancial(ticker, dirty=True).dump()
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

    def getTicker(self, ticker="ACN", exchange="XNYS", force_refresh=False):
        """
        This function goes and pulls the financials from the DBs if they exist or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec
        :return Ratios object
        """

        # Build financials
        logger.debug(
            "Request for {0} forcing_refresh {1}".format(ticker, force_refresh)
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
            financial = self._getFinancial(ticker, force_refresh).dump()
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
            for val in self._getKeyRatios(ticker, force_refresh, exchange=exchange)
        ]

        # Get Valuation
        valuations = [
            val.dump()
            for val in self._getValuations(ticker, force_refresh, exchange=exchange)
        ]
        logger.debug(valuations)

        financial["ratios"] = ratios
        financial["valuations"] = valuations

        # TODO: Get Dividend history
        dividend_history = [
            val.dump() for val in self._getDividends(ticker, force_refresh)
        ]

        # Assemble stock data
        stockdata = {
            "symbol": ticker,
            "name": ticker,
            "financials": financial,
            "dividend_history": dividend_history,
        }

        return jsonify(stockdata)

    def _getValuations(self, ticker="ACN", force_refresh=False, exchange="XNYS"):
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
        if not force_refresh and query.count() == 1:
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
        if not os.path.isfile(val_file) or force_refresh:
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

    def _getFinancial(self, ticker="ACN", force_refresh=False, dirty=False):
        """
        This function pulls the financial from the DB
        TODO: check for freshness
        :return Financials object
        """
        try:
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
            # yesterday = datetime.combine(yesterday, datetime.min.time())
            if (
                force_refresh
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
                # Get data from the API
                profile_url = f"{FINANCIAL_API}/company/profile/{ticker}"
                ratios_url = f"{FINANCIAL_API}/financial-ratios/{ticker}"
                stats_file = "tmp/{ticker}_stats".format(ticker=ticker)
                logger.debug(stats_file)
                # Get data if it doesn't exist or we are refreshing
                if not (os.path.isfile(stats_file)) or force_refresh:
                    logger.debug("Requesting {0} {1}".format(profile_url, ratios_url))
                    profile = requests.get(profile_url)
                    ratios = requests.get(ratios_url)
                    if profile.status_code == 200 and ratios.status_code == 200:
                        logger.debug("Got file from api")
                        try:
                            profile_data = json.loads(profile.text)
                            profile_data = profile_data["profile"]
                            ratios_data = json.loads(ratios.text)
                            ratios_data = ratios_data["ratios"][0]["investmentValuationRatios"]
                            
                            profile_data.update(ratios_data)
                            with open(stats_file, "wb") as f:
                                pickle.dump(profile_data, f)
                        except Exception as e:
                            logger.exception(
                                "Failed to write for {ticker} {error}".format(
                                    ticker=ticker, error=e
                                )
                            )
                    else:
                        logger.debug("Failed to get 200 response {0}".format(stats))

                try:
                    f = None
                    with open(stats_file, "rb") as f:
                        logger.debug(f)
                        data = pickle.load(f)
                        div_yield = data["dividendYield"]
                        beta = data["beta"]
                        company_name = data["companyName"]
                        if q.count() == 1:
                            logger.debug(
                                "Entry for {0} already exists - refreshing".format(
                                    ticker
                                )
                            )
                            financial = q.first()
                            financial.beta = beta
                            financial.dividend_yield = div_yield
                            financial.company_name = company_name
                            financial.updated = today
                            db_session.commit()
                            logger.debug(
                                "Returning financial {financial}".format(
                                    financial=financial
                                )
                            )
                            return financial

                        else:
                            # Indicate that this hasn't ever been fully updated
                            if dirty:
                                logger.debug("Dirty read - not updating updated")
                                today = None
                            f = Financial(
                                ticker=ticker,
                                dividend_yield=div_yield,
                                beta=beta,
                                updated=today,
                                company_name=company_name,
                            )
                            logger.debug(
                                "Added Financials for {ticker}".format(ticker=ticker)
                            )
                            db_session.add(f)
                            db_session.commit()
                            return f
                    return f
                except Exception as e:
                    logger.exception(e)
            else:
                logger.debug(
                    "We already have {0} so we are returning it".format(ticker)
                )
                return q.first()

        except Exception as e:
            logger.exception(e)

    def _getKeyRatios(self, ticker="ACN", force_refresh=False, exchange="XNYS"):
        """
        This function goes and pulls the financials from the DB if it exists or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec

        :return Ratios object
        """
        try:
            # See if they exist for this month
            today = datetime.today()
            datem = datetime(today.year - 1, 1, 1)

            key_ratios_query = stockdatamodel.Ratio.query.filter(
                stockdatamodel.Ratio.ticker == ticker
            ).filter(stockdatamodel.Ratio.period >= datem)

            # Refresh if need be
            if key_ratios_query.count() < 1 or force_refresh == True:
                self._refreshRatiosDB(ticker, force_refresh, exchange=exchange)

            # Now look them up
            key_ratios = self._getRatiosDB(ticker)
            return key_ratios

            # If they don't exist error
        except Exception as e:
            logger.exception(e)
            return 400, "Ratios not found for {0}".format(ticker)

    def _getRatiosDB(self, ticker, force_refresh=False):
        """
        Gets the ratios from the DB if they exist for the given ticker
        return: Ratios from the DB or null
        """
        financials = stockdatamodel.Ratio.query.filter(
            stockdatamodel.Ratio.ticker == ticker
        )
        if financials.count() < 1:
            logger.debug("Financials not found in DB for".format(ticker))
            return

        return financials.all()

    def save_frames_temp(self, frames, ticker):
        fname = "tmp/{ticker}_pickle.pkl".format(ticker=ticker)
        with open(fname, "wb") as f:
            pickle.dump(frames, f)
        return frames
        # frames.to_pickle("./{ticker}_pickle.pkl".format(ticker))

    def restore_frames(self, ticker):
        fname = "tmp/{ticker}_pickle.pkl".format(ticker=ticker)
        try:
            with open(fname, "rb") as f:
                frames = pickle.load(f)
                if len(frames) < 1:
                    return False
                return frames
        except Exception as e:
            logger.exception(e)
            return False

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

    def _refreshRatiosDB(self, ticker, force_refresh, exchange="XNYS"):
        """
        Uses goodmorning to populate ratios
        """
        frames = None
        ms_ticker = ticker
        if exchange != "":
            ms_ticker = "{exchange}:{ticker}".format(exchange=exchange, ticker=ticker)
        frames = self.restore_frames(ticker)
        if frames and not force_refresh:
            logger.debug("Found frames in pickle {ticker}".format(ticker=ticker))
        else:
            logger.debug(
                "Refreshing from GoodMorning {ticker} {exchange} {ms_ticker}".format(
                    ticker=ticker, exchange=exchange, ms_ticker=ms_ticker
                )
            )
            kr = gm.KeyRatiosDownloader()
            frames = kr.download(ms_ticker)

        if frames:
            # Deal with the key ratios and write them to the DB
            call = []
            # Key Financials
            financials = frames[0]
            health = frames[9]
            temp_objects = {}
            last_period = True
            for year in sorted(financials, reverse=True):
                series = financials[year]
                period = self._datefromperiod(year)
                # if last_period:
                #    period = self._datefromperiod("1900")
                #    last_period = False
                revenue = self._sanitise(series[0])
                gross_margin = self._sanitise(series[1])
                operating_income = self._sanitise(series[2])
                operating_margin = self._sanitise(series[3])
                net_income = self._sanitise(series[4])
                eps = self._sanitise(series[5])
                dividends = self._sanitise(series[6])
                payout_ratio = self._sanitise(series[7])
                shares = self._sanitise(series[8])
                bps = self._sanitise(series[9])
                operating_cash_flow = self._sanitise(series[10])
                cap_spending = self._sanitise(series[11])
                fcf = self._sanitise(series[12])
                working_capital = self._sanitise(series[13])

                # Matching Health Data
                h_s = health[year]
                current_ratio = self._sanitise(h_s["Current Ratio"])
                debt_equity = self._sanitise(h_s["Debt/Equity"])

                logger.debug(
                    "Found and starting to build {ticker} {period} {eps}".format(
                        ticker=ticker, period=period, eps=eps
                    )
                )
                # Check if it exists
                query = stockdatamodel.Ratio.query.filter(
                    stockdatamodel.Ratio.ticker == ticker
                ).filter(stockdatamodel.Ratio.period == period)
                if query.count() < 1:
                    logger.debug(
                        "Don't have this yet {ticker} {period} {eps}".format(
                            ticker=ticker, period=period, eps=eps
                        )
                    )
                    f = stockdatamodel.Ratio(
                        ticker=ticker,
                        period=period,
                        revenue=revenue,
                        gross_margin=gross_margin,
                        operating_income=operating_income,
                        operating_margin=operating_margin,
                        net_income=net_income,
                        eps=eps,
                        dividends=dividends,
                        payout_ratio=payout_ratio,
                        shares=shares,
                        bps=bps,
                        operating_cash_flow=operating_cash_flow,
                        cap_spending=cap_spending,
                        fcf=fcf,
                        working_capital=working_capital,
                        current_ratio=current_ratio,
                        debt_equity=debt_equity,
                    )
                    db_session.add(f)
                else:
                    f = query.first()
                    logger.debug(f)
                    # If we need to force refresh update it
                    if force_refresh:
                        logger.debug(
                            "We are force refreshing {ticker} {period}".format(
                                ticker=ticker, period=period
                            )
                        )
                        # f.ticker = ticker
                        # f.period = period
                        f.revenue = revenue
                        f.gross_margin = gross_margin
                        f.operating_income = operating_income
                        f.operating_margin = operating_margin
                        f.net_income = net_income
                        f.eps = eps
                        f.dividends = dividends
                        f.payout_ratio = payout_ratio
                        f.shares = shares
                        f.bps = bps
                        f.operating_cash_flow = operating_cash_flow
                        f.cap_spending = cap_spending
                        f.fcf = fcf
                        f.working_capital = working_capital
                        f.current_ratio = current_ratio
                        f.debt_equity = debt_equity

            db_session.commit()

            # Deal with health and write it to the DB

    def _getDividends(self, ticker, force_refresh=False):
        """ Retrieves the dividend history for the given ticker

        If we already have it and it's in date (not older than a month) return that. Otherwise we
        grab it from yahoo finance

        self -- this class
        ticker -- the ticker symbol of this
        force_refresh -- refresh even if in date
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
            if force_refresh or dividend_history_query.count() < 1:
                self._refreshDividendsDB(ticker, force_refresh)
            # Pull them and return
            dividend_history_query = stockdatamodel.Dividend.query.filter(
                stockdatamodel.Dividend.ticker == ticker
            )
            return dividend_history_query.all()

            # If they don't exist error
        except Exception as e:
            logger.exception(e)
            return 400, "Ratios not found for {0}".format(ticker)

    def _refreshDividendsDB(self, ticker, force_refresh=False):

        # 1 Use yahoo reader to scrape
        res = []
        dividends = None
        try:
            dividends = yahoo_reader.yahoo_reader.get_dividend(ticker, force_refresh)
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
                if force_refresh:
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
