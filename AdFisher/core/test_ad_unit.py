import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import ad_unit

class GetAds(unittest.TestCase):
    ''' Test collecting ads from sites using ad_unit driver '''

    def setUp(self):
        self.browser =  ad_unit.AdUnit(easyList=True)
        self.driver = self.browser.driver

    def test_browse_yahoo_news(self):
        self.browser.visit_url("http://news.yahoo.com/")
        self.browser.find_ads()
        self.browser.check_tag("script")
        self.browser.check_tag("img")
        assert self.driver.page_source != None

    def test_browse_fox_news(self):
        self.browser.visit_url("http://www.foxnews.com/")
        self.browser.find_ads()
        self.browser.check_tag("script")
        self.browser.check_tag("img")
        assert self.driver.page_source != None

    def test_browse_cnn_news(self):
        self.browser.visit_url("http://www.cnn.com/")
        self.browser.find_ads()
        self.browser.check_tag("script")
        self.browser.check_tag("img")
        assert self.driver.page_source != None
    
    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
   
    suite = unittest.TestLoader().loadTestsFromTestCase(GetAds)
    unittest.TextTestRunner(verbosity=2).run(suite)

