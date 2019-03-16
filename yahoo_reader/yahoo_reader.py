from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import time
import requests
import dateutil.parser
import traceback
import logging

logger = logging.getLogger(__name__)

def get_dividend(ticker, force_refresh = False):

    div_file = "tmp/{ticker}_div".format(ticker = ticker)

    if force_refresh or not os.path.isfile(div_file):
        # Check if we have a file already or we are ovveriding
        dividend_url = "https://finance.yahoo.com/quote/{ticker}/history?period1=0&period2=2222222222&interval=div|split&filter=div&frequency=1mo".format(ticker = ticker)
        logger.debug("Calling {url}".format(url = dividend_url))
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        #chrome_options.add_experimental_option("profile.default_content_settings.popups", 0)
        #chrome_options.add_experimental_option("download.prompt_for_download", "false")
        #chrome_options.add_experimental_option("download.default_directory", "/tmp")
        download_dir = "tmp/"
        preferences = {"download.default_directory": download_dir ,
               "directory_upgrade": True,
               "safebrowsing.enabled": True }
        chrome_options.add_experimental_option("prefs", preferences)

        # Browse to page with Selenium
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.set_window_size(1920, 1080)
        size = driver.get_window_size()
        logger.debug("Window size: width = {}px, height = {}px.".format(size["width"], size["height"]))
        driver.get(dividend_url)


        # Handle annoying redirect
        #python_button = driver.find_elements_by_xpath("//button[@name='agree']") #FHSU
        python_button = driver.find_elements_by_xpath("/html/body/div[1]/div[2]/div[4]/div/div[2]/form[1]/div/input")
        if  len(python_button) > 0:
            logger.debug("Agreement screen")
            logger.debug(driver.page_source)
            python_button = python_button[0]
            logger.debug(python_button)
            python_button.click() #click link

            logger.debug("After the click")
            logger.debug(driver.page_source[:10000])
            company_xpath = "//a"
            logger.debug("Waiting for {0}".format(company_xpath))
            try:
                next_page = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.LINK_TEXT, 'here')))
                driver.find_element_by_link_text("here").click()

                logger.debug("Found next link")
            except Exception as e:
                logger.debug("Failed to pass splash-screen")
                logger.debug(driver.page_source[:10000])
                logger.debug(e)

        '''
        # Get CSV link
        try:
            link = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Download Data')))
            logger.debug("Linky link {0}".format(link))
            #something = link.click()
            #logger.debug("Something {0}".format(something))
            link = link.get_attribute('href')
            logger.debug(link)
            driver.get(link)
            #res = requests.get(link)
            #logger.debug(res)
            with open(div_file, "w") as f:
                f.write(res.text)
        except Exception as e:
            logger.debug("Error saving file {error}".format(error = e))
            logger.debug(e)

        '''
        # Invoke JS to load all history
        last_height = driver.execute_script("return document.body.scrollHeight")

        logger.debug("STARTING SCROLLY SCROLL {0}".format(last_height))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        i = 0
        while i < 2:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight*10000);")
            time.sleep(1)
            # Calculate new scroll height and compare with last scroll height
            #new_height = driver.execute_script("return document.body.scrollHeight")
            #last_height = new_height
            #driver.send_keys(Keys.SPACE)
            i = i + 1
            logger.debug("Scroll {i}".format(i = i))
        # Save temporary code
        try:
            with open(div_file, "w") as f:
                mess = BeautifulSoup(driver.page_source, 'lxml')
                #logger.debug(mess)
                f.write(driver.page_source)
        except Exception as e:
            logger.debug("Error saving file {error}".format(error = e))

        div_source = None

    try:
        with open(div_file, "r") as f:

            mess = BeautifulSoup(f, 'lxml')
            #logger.debug(mess)
            # All table rows contain dividends
            rows = mess.find("table", {"data-test" : "historical-prices"})
            #rows = mess.findAll("tr")
            #logger.debug("ALL DIVIDENDS")

            data = []
            labels = ["Date", "Dividend"]
            # parse rows and build Pandas
            # <tr class="BdT Bdc($c-fuji-grey-c) Ta(end) Fz(s) Whs(nw)" data-reactid="48"><td class="Py(10px) Ta(start) Pend(10px)" data-reactid="49"><span data-reactid="50">Nov 21, 2018</span></td><td class="Ta(c) Py(10px) Pstart(10px)" colspan="6" data-reactid="51"><strong data-reactid="52">1.36</strong><!-- react-text: 53 --> <!-- /react-text --><span data-reactid="54">Dividend</span></td></tr>
            rows = rows.findAll("tr", {"class": "BdT"})

            rows = rows[:-1]
            for row in rows:
                try:
                    #logger.debug("ROW {0}".format(row))
                    # Date
                    date = row.find("span")
                    date_text = date.renderContents().strip()
                    #date_text = date_text.lower().replace("rd", "").replace("nd", "").replace("st", "")
                    date_text = dateutil.parser.parse(date_text).date()
                    # Dividend
                    dividend = row.find("strong")
                    dividend_text = dividend.renderContents().strip()
                    dividend_text = float(dividend_text)
                    logger.debug("Date: {0}, Dividend {1}".format(date_text, dividend_text))
                    data.append((date_text, dividend_text))
                except Exception as e:
                    logger.exception("Failed to parse {0}".format(row))

            div_frame = pd.DataFrame.from_records(data, columns=labels)
            return div_frame
    except Exception as e:
        logger.exception("Failed to parse dividend")


if __name__ == "__main__":
    frame = get_dividend("AFL")
    logger.debug(frame)
