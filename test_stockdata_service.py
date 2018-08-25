import unittest
import stockdata_service


class StockDataTestCase(unittest.TestCase):

    def setUp(self):
        self.sd = stockdata_service.StockDataService()


    def testRatios(self):
        print("Testing ratios for ACN")
        ratios = self.sd.getKeyRatios("ACN", force_refresh = False)

if __name__ == '__main__':
    unittest.main()
