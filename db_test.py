import unittest
import database
import stockdatamodel
#import date from datetime

TEST_TICKER = "ACN"
TEST_PERIOD = "2055-12-31"
TEST_FCF = 9.93

class DatabaseConnectionTestCase(unittest.TestCase):

    def setUp(self):
        print("Setting up the DB")
        self.db = database.init_db()
        self.delete_test_financial()


    def test_1_write_and_read_back_StockData(self):
        print("Writing some stuff {tick} {period} {FCF}".format(tick = TEST_TICKER, period = TEST_PERIOD, FCF = TEST_FCF))
        f = stockdatamodel.Financials(
                ticker = TEST_TICKER,
                period = TEST_PERIOD,
                gross_margin = 34,
                operating_income = 2.0,
                net_income = 2000.33,
                eps = 3.3,
                dividends = 2.0,
                payout_ratio = 9.2,
                shares = 400000,
                bps = 20.2,
                operating_cash_flow = 4.0,
                cap_spending = 3.2,
                fcf = TEST_FCF,
                working_capital = 2.3
                )
        print("Adding {0}".format(f))
        database.db_session.add(f)
        database.db_session.commit()

        # check it's there
        print("Reading it back")
        read_q = self.read_test_financial()
        assert(read_q.count() == 1)

        # check it is what it should be

        print("Checking it's correct")
        test_fin  = read_q.first()
        assert(test_fin.fcf == TEST_FCF)

        # Clean up
        print("Nuking it")
        self.delete_test_financial()

        # Check it's gone
        print("Checking it's gone")
        read_q = self.read_test_financial()

        assert(read_q.count() == 0)

    def read_test_financial(self):
        query = stockdatamodel.Financials.query.filter(stockdatamodel.Financials.ticker == TEST_TICKER).filter(stockdatamodel.Financials.period == TEST_PERIOD)
        return query

    def delete_test_financial(self):
        print("Checking if we need to delete our test financial")
        test_fin = self.read_test_financial()
        #print(test_fin)
        if test_fin.count() == 1:
            print("Deleting our test financial")
            database.db_session.delete(test_fin.first())
            database.db_session.commit()



if __name__ == '__main__':
    print("Here we go ")
    unittest.main()
