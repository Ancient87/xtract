import unittest
import xtract
from xtract import db
import xtract.model.stockdatamodel
import os
import tempfile
import pytest
# import date from datetime

TEST_TICKER = "GLUMANDA"
TEST_PERIOD = "2055-12-31"
TEST_FCF = 9.93
TEST_FD = 999.99


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    

    with app.test_client() as client:
        with app.app_context():
            app.init_db()
        yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

class DatabaseConnectionTestCase(unittest.TestCase):
    def setUp(self):
        print("Setting up the DB")
        
        self.app, self.app_connex, self.port = xtract.create_app(os.getenv('BOILERPLATE_ENV') or 'dev')
        
        self.app.app_context().push()
        
        #self.db = db.init_db()
        self.delete_test_financial()

    def test_1_write_and_read_back_StockData(self):
        print(
            "Writing some stuff {tick} {period} {FCF}".format(
                tick=TEST_TICKER, period=TEST_PERIOD, FCF=TEST_FCF
            )
        )

        financial = xtract.model.stockdatamodel.Financial(
            ticker=TEST_TICKER, beta=TEST_FD, dividend_yield=TEST_FD,
        )
        db.session.add(financial)
        db.session.commit()

        f = xtract.model.stockdatamodel.Ratio(
            ticker=TEST_TICKER,
            period=TEST_PERIOD,
            gross_margin=34,
            operating_income=2.0,
            net_income=2000.33,
            eps=3.3,
            dividends=2.0,
            payout_ratio=9.2,
            shares=400000,
            bps=20.2,
            operating_cash_flow=4.0,
            cap_spending=3.2,
            fcf=TEST_FCF,
            working_capital=2.3,
            current_ratio=10.0,
            debt_equity=10.0,
        )
        print("Adding {0}".format(f))
        db.session.add(f)
        db.session.commit()

        # check it's there
        print("Reading it back")
        read_q = self.read_test_ratios()
        assert read_q.count() == 1

        # check it is what it should be

        print("Checking Ratio it's correct")
        test_fin = read_q.first()
        assert test_fin.fcf == TEST_FCF

        read_q = self.read_test_financial()
        assert read_q.count() == 1

        print("Checking Financial is correct")
        test_fin = read_q.first()
        assert test_fin.beta == TEST_FD

        # Clean up
        print("Nuking it")
        self.delete_test_financial()

        # Check it's gone
        print("Checking it's gone")
        read_q = self.read_test_financial()

        assert read_q.count() == 0

    def read_test_financial(self):
        query = xtract.model.stockdatamodel.Financial.query.filter(
            xtract.model.stockdatamodel.Financial.ticker == TEST_TICKER
        )
        return query

    def read_test_ratios(self):
        query = xtract.model.stockdatamodel.Ratio.query.filter(
            xtract.model.stockdatamodel.Ratio.ticker == TEST_TICKER
        ).filter(xtract.model.stockdatamodel.Ratio.period == TEST_PERIOD)
        return query

    def delete_test_financial(self):
        print("Checking if we need to delete our test financial")
        test_ratios = self.read_test_ratios()
        test_financial = self.read_test_financial()
        # print(test_fin)
        if test_ratios.count() == 1:
            db.session.delete(test_ratios.first())

        db.session.commit()

        if test_financial.count() == 1:
            print("Deleting our test financials")
            db.session.delete(test_financial.first())

        db.session.commit()


if __name__ == "__main__":
    print("Here we go ")
    unittest.main()
