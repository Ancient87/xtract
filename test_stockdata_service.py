import unittest
import stockdata_service


class StockDataTestCase(unittest.TestCase):

    def setUp(self):
        self.sd = stockdata_service.StockDataService()


    def testRatios(self):
        print("Gettings ratios for ACN")
        ratios = self.sd.getTicker("ACN", force_refresh = False)
        for ratio in ratios:
            print(ratio)
        ratios = self.sd.getTicker("AMZN", force_refresh = False)
        for ratio in ratios:
            print(ratio)
if __name__ == '__main__':
    unittest.main()
