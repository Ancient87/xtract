# Module that deals with data access to the Morningstar and TBC APIs to create information for the Divgro calculations

import pickle
import traceback
import good_morning as gm
import pymysql
from database import db_session
import stockdatamodel
from datetime import date, datetime
import os
import pandas as pd
#import stockdatamodel.Financials
#import stockdatamodel.Health

class StockDataService:

    #    def init(self, db_host="localhost:", db_user="ancient", db_pass="lolchu", db_name="divgro"):

    def init(self):
        try:
            #Setup the DB
            database.init_db()
            #conn = pymysql.connect(host = db_host, user = db_user, passwd = db_pass, db = db_name)
            #self.db = conn
        except:
            print("Unexpected error {0}".format(sys.exc_info()[0]))

    def getKeyRatios(self, ticker = "ACN", force_refresh = False):
        """
        This function goes and pulls the financials from the DB if it exists or else (or if forced) reloads the DB. Then is constructs the JSON response required for DivGro and returns it as an object complying with swagger spec

        :return Ratios object
        """
        try:
            # See if they exist for this month
            today = datetime.today()
            datem = datetime(today.year-1, 1, 1)

            key_ratios_query = stockdatamodel.Financials.query.filter(stockdatamodel.Financials.ticker == ticker).filter(stockdatamodel.Financials.period >= datem)

            # Refresh if need be
            if key_ratios_query.count() < 1 or force_refresh == True:
                self._refreshRatiosDB(ticker)

            # Now look them up
            key_ratios = self._getRatiosDB(ticker)
            return key_ratios

            # If they don't exist error
        except Exception as e:
            traceback.print_exc()
            return 400, 'Ratios not found for {0}'.format(ticker)

    def _getRatiosDB(self, ticker, force_refresh = False):
        """
        Gets the ratios from the DB if they exist for the given ticker
        return: Ratios from the DB or null
        """
        financials = stockdatamodel.Financials.query.filter(stockdatamodel.Financials.ticker == ticker)
        if financials.count() < 1:
            print("Financials not found in DB for".format(ticker))
            return

        return financials.all()

    def save_frames_temp(self, frames, ticker):
        fname = "./{ticker}_pickle.pkl".format(ticker = ticker)
        with open(fname, 'wb') as f:
            pickle.dump(frames, f)
        #frames.to_pickle("./{ticker}_pickle.pkl".format(ticker))

    def restore_frames(self, ticker):
        fname = "./{ticker}_pickle.pkl".format(ticker = ticker)
        try:
            with open(fname, 'rb') as f:
                frames = pickle.load(f)
                if len(frames) < 1 :
                    return False
                return frames
        except Exception as e:
            traceback.print_exc()
            return False
    def _datefromperiod(self, year):
        print("Converting {0}".format(year))
        return datetime.strptime(str(year), '%Y')

    def _sanitise(self, number):
#        print("number {0}".format(number))
        if number != number:
#            print("{0} is NaN".format(number))
            return 0.0
        return float(number)

    def _refreshRatiosDB(self, ticker):
        """
        Uses goodmorning to populate ratios
        """
        frames = self.restore_frames(ticker)
        if frames:
            print("Found frames in pickle {ticker}".format(ticker = ticker))
        else:
            pass
            print("Refreshing from GoodMorning {ticker}".format(ticker = ticker))
            kr = gm.KeyRatiosDownloader()
            frames = kr.download(ticker)
            self.save_frames_temp(frames, ticker)

        if frames:
            # Deal with the key ratios and write them to the DB
            call = []
            # Key Financials
            financials = frames[0]
            temp_objects = {}
            for year in financials:

                series = financials[year]
                period = self._datefromperiod(year)
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

                print("Found and starting to build {ticker} {period} {eps}".format(ticker = ticker, period = period, eps = eps))
               #Check if it exists
                query = stockdatamodel.Financials.query.filter(stockdatamodel.Financials.ticker == ticker).filter(stockdatamodel.Financials.period == period)
                if query.count() < 1:
                    print("Don't have this yet {ticker} {period} {eps}".format(ticker = ticker, period = period, eps = eps))
                    f  = stockdatamodel.Financials(
                            ticker = ticker,
                            period = period,
                            gross_margin = gross_margin,
                            operating_income = operating_income,
                            operating_margin = operating_margin,
                            net_income = net_income,
                            eps = eps,
                            dividends = dividends,
                            payout_ratio = payout_ratio,
                            shares = shares,
                            bps = bps,
                            operating_cash_flow = operating_cash_flow,
                            cap_spending = cap_spending,
                            fcf = fcf,
                            working_capital = working_capital,
                            )
                    db_session.add(f)
                else:
                    f = query.first()
                    print(f)

            db_session.commit()

            # Deal with health and write it to the DB

    def getDividends(self):
        pass

