import os
import requests, re, time, logging
from typing import Optional
from datetime import datetime
from functools import wraps


import pandas as pd
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import FirefoxOptions
from bs4 import BeautifulSoup

from .config import DEBUG, HEADER


log = logging.basicConfig()


class JobFinder:
    def __init__(
        self,
        header: Optional[dict] = HEADER,
        debug: Optional[bool] = False
    ):
        self.header = header
        self.debug = debug
        self.driver = None

    def _create_firefox_driver(
        self,
        mode: str = "--headless"
    ) -> None:
        firefox_options = FirefoxOptions()
        if not DEBUG:
            firefox_options.add_argument(mode)
        self.driver = webdriver.Firefox(options=firefox_options)
        self.driver.implicitly_wait(30)

    def _get_past_authentication_wall(
        self,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> WebDriver:
        self._create_firefox_driver()
        if (self.driver is not None) and (retry_count < max_retries):
            self.driver.get(f"https://www.linkedin.com/jobs/search/?distance=25&geoId=102454443&keywords={self.current_title_for_url}&location=Singapore&start=0")
            html_source = self.driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')
            if soup.content is not None:
                if "Sign Up | LinkedIn" in soup.find('title').text:
                    log.debug("\tRan into AuthWall, trying again in 5 secs...")
                else:
                    return self.driver
            else:
                log.debug("\tEmpty soup, trying again in 5 secs...")
            self.driver.quit()
            time.sleep(5)
            return self._get_past_authentication_wall(retry_count+1)

    def _scroll_pages(
        self,
        pages: int
    ) -> None:
        for _ in range(0, pages):
            time.sleep(2)
            webdriver.ActionChains(self.driver).scroll_by_amount(0, -10).perform()  # Need to scroll up a little to trigger infinite scroll
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:  # Occasionally there will be a click to see more button appear, need to click on it, sometimes two clicks are needed
                element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="main-content"]/section[2]/button')))
                if element:
                    self.driver.execute_script("arguments[0].click()", element)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click()", element)
            except Exception as e:
                print(e)

    def _get_job_url_soup(
        self,
        keyword: str,
        pages: int,
    ) -> BeautifulSoup:
        self.current_title_for_url = re.sub(' ', '%20', keyword.lower())
        self.current_keyword = re.sub(' ', '-', keyword.lower())
        log.info(f'Searching for {keyword}')
        self._get_past_authentication_wall(max_retries=3)
        self._scroll_pages(pages=pages)

        log.info('Getting page_source')
        html_source = self.driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        self.driver.quit()
        return soup
    
    def get_job_urls_from_soup(
        self,
        soup: BeautifulSoup,
    ) -> dict:
        data_dict = {}
        def custom_selector(tag):
            return tag.name == "a" and tag.has_attr("href") and self.keyword in tag.get('href')
        tags = soup.find_all(custom_selector)

        # Get the link and jobid for each listed job
        for tag in tags:
            link = tag.get('href')
            link = link.split('?')[0] # Tidy up the link to remove the trackingid
            if 'login' not in link: # To handle a login link that shows at the end
                data_dict.setdefault(link, 0)
                data_dict[link] += 1
        log.info(f'Unique links: {len(data_dict)}')
        if self.debug:
            return data_dict, soup
        else:
            return data_dict
        
