import sys
import re
import time
import logging
from typing import Optional, Union
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import FirefoxOptions
from bs4 import BeautifulSoup
import pandas as pd

from .config import JobFinderConfig


logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
log = logging.getLogger()


class LinkedInJobFinder:
    def __init__(
        self,
        header: Optional[dict] = JobFinderConfig.HEADER,
        debug: Optional[bool] = False
    ):
        self.header = header
        self.debug = debug
        self.driver: Union[None, WebDriver] = None
        self.job_url_links_dict: dict = None
        if self.debug:
            self.soup_list: list[BeautifulSoup] = []

    def _create_firefox_driver(
        self,
        mode: str = "--headless"
    ) -> None:
        firefox_options = FirefoxOptions()
        if not self.debug:
            firefox_options.add_argument(mode)
        self.driver = webdriver.Firefox(options=firefox_options)
        self.driver.implicitly_wait(30)

    def _get_past_authentication_wall(
        self,
        url: str,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> WebDriver:
        self._create_firefox_driver()
        if (self.driver is None) or (retry_count >= max_retries):
            raise ValueError("Ran into maximum retries for authentication walls")
        else:
            self.driver.get(url)
            time.sleep(3)
            html_source = self.driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')
            if self.debug:
                self.soup_list.append(soup)
            titles_to_skip = [
                "Sign Up | LinkedIn",
                "LinkedIn: Log In or Sign Up"
            ]
            if soup.find('title').text in titles_to_skip:
                log.info("\tRan into AuthWall, trying again in 5 secs...")
            else:
                return self.driver
            self.driver.quit()
            time.sleep(5)
            return self._get_past_authentication_wall(
                url=url,
                retry_count=retry_count+1,
                max_retries=max_retries)

    def _scroll_pages(
        self,
        pages: int
    ) -> None:
        for _ in range(0, pages):
            time.sleep(2)
            webdriver.ActionChains(self.driver).scroll_by_amount(0, -10).perform()  # scoll up trigger infinite scroll
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:  # To click on see more, sometimes two clicks are needed
                element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="main-content"]/section[2]/button')))
                if element:
                    self.driver.execute_script("arguments[0].click()", element)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click()", element)
            except Exception as e:
                log.debug(e)

    def _get_job_urls_soup(
        self,
        url: str,
        pages: int
    ) -> BeautifulSoup:
        try:
            driver = self._get_past_authentication_wall(url=url, max_retries=3)
        except ValueError as error_message:
            log.error(error_message)
            return None
        else:
            self._scroll_pages(pages=pages)
            log.info('Completed page scrolls, downloading page_source')
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')
            driver.quit()
            return soup

    def _get_job_urls_from_soup(
        self,
        keyword: str,
        soup: BeautifulSoup,
    ) -> dict:
        job_url_links_dict = {}

        def custom_selector(tag):
            return tag.name == "a" and tag.has_attr("href") and keyword in tag.get('href')
        tags = soup.find_all(custom_selector)

        # Get the link and jobid for each listed job
        for tag in tags:
            url_link = tag.get('href')
            url_link = url_link.split('?')[0]  # Tidy up the link to remove the trackingid
            if 'login' not in url_link:  # To handle a login link that shows at the end
                job_url_links_dict.setdefault(url_link, 0)
                job_url_links_dict[url_link] += 1
        log.info(f'Unique links: {len(job_url_links_dict)}')
        return {
            "job_url_links": job_url_links_dict,
            "soup": soup
            }

    def retrieve_linkedin_jobs_by_keywords(
        self,
        keyword: str,
        pages: int,
    ) -> dict:
        current_title_for_url = re.sub(' ', '%20', keyword.lower())
        current_url = f"https://www.linkedin.com/jobs/search/?distance=25&geoId=102454443&keywords={current_title_for_url}&location=Singapore&start=0"
        current_keyword = re.sub(' ', '-', keyword.lower())
        log.info(f'Searching LinkedIn for {keyword}')

        soup = self._get_job_urls_soup(
            url=current_url,
            pages=pages
        )
        if soup is not None:
            self.job_url_links_dict = self._get_job_urls_from_soup(
                keyword=current_keyword,
                soup=soup
            )
        else:
            log.error(f"No job urls were retrieved for {keyword}")

    def get_all_individual_job_informations(
        self
    ) -> dict:
        if (not self.job_url_links_dict) or (len(self.job_url_links_dict.get('job_url_links')) < 1):
            pass
        else:
            main_dict = {}
            for idx, url_link in enumerate(self.job_url_links_dict['job_url_links']):
                soup = self._get_individual_job_url_soup(url=url_link)
                if soup is not None:
                    individual_job_information_dict = self._get_individual_job_url_details_from_soup(
                        soup=soup,
                        index=idx,
                        url=url_link
                    )
                    main_dict[idx] = individual_job_information_dict
            return main_dict

    def _get_individual_job_url_soup(
        self,
        url: str
    ) -> Union[BeautifulSoup, None]:
        try:
            driver = self._get_past_authentication_wall(url=url, max_retries=3)
        except ValueError as error_message:
            log.error(error_message)
            return None
        else:
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')
            driver.quit()
            return soup

    def _get_individual_job_url_details_from_soup(
        self,
        soup: BeautifulSoup,
        index: int,
        url: str
    ) -> dict:
        info = {}
        # JobID
        jobid = re.findall('-(\d{8,})', url)  # removed [\?/] from pattern because of url cleaning ? away in new version
        if len(jobid) == 1:
            info['job_id'] = str(jobid[0])
        else:
            log.error(f'Index {index}: Found no Job ID or multiple Job IDs for {url}')
        info['date_logged'] = datetime.now().strftime('%Y-%m-%d')

        # Page title
        title = soup.find('title')
        if title:
            info['company'] = title.text.split(' hiring')[0]
        else:
            log.error(f'Index {index}: Found no company name for {url}')

        # Job title
        job_title = soup.find('h1')
        if job_title:
            info['job_title'] = job_title.text
        else:
            log.error(f'Index {index}: Found no job title for {url}')

        # Job level, type (full time etc), sector
        criteria = soup.find_all('span', class_="description__job-criteria-text description__job-criteria-text--criteria")
        if criteria:
            criteria = [x.text.strip(' \n') for x in criteria]
            fields = ['level', 'job_type', 'industry1', 'industry2']
            for field, criterion in zip(fields, criteria):
                info[field] = criterion

        # Job scope and requirements
        descriptions = soup.find(class_="show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden")
        if descriptions:
            line_by_line_desc = ''
            experience = ''
            degree = ''

            for tag in descriptions.children:  # children is a generator of all the tags contained, the alternative to the full tags is .content
                description = tag.text.strip('\n')
                if (tag.name == 'ul') or (tag.name == 'ol'):
                    line_by_line_desc += '\u2022' + description + '\n'
                elif tag.name == 'br':
                    continue
                else:
                    line_by_line_desc += description + '\n'

                # Search for special info interested in
                if 'experience' in description:
                    experience += '\u2022' + description + '\n'
                if 'degree' in description:
                    degree += '\u2022' + description + '\n'

                info['descriptions'] = line_by_line_desc
                info['degree'] = degree
                info['experience'] = experience
        else:  # Print notification if nothing found
            log.error(f'Index {index}: Found no description for {url}')

        info['link'] = url
        return info

    @staticmethod
    def process_dict_to_df(
        data: dict,
        remove_nulls: bool = True,
        remove_duplicates: bool = True
    ) -> pd.DataFrame:
        log.info("Processing to dataframe")
        df = pd.DataFrame.from_dict(data, orient='index')
        df = df.set_index('job_id')

        if remove_nulls:
            df_length_with_nulls = len(df)
            df = df[~(
                df['company'].isnull()
                & df['job_title'].isnull()
                & df['level'].isnull()
                & df['descriptions'].isnull()
            )]
            log.info(f'Removed {df_length_with_nulls - len(df)} empty rows')

        # Deduplication, some jobs are just repostings
        if remove_duplicates:
            duplicate_subset = ['company', 'job_title', 'level', 'job_type', 'descriptions', 'industry1']
            df_length_with_duplicates = len(df)
            df = df.drop_duplicates(subset=duplicate_subset)
            log.info(f'Removed {df_length_with_duplicates - len(df)} duplicates')

        # Sorting order and values
        df = df[[
            'date_logged',
            'company',
            'job_title',
            'level',
            'job_type',
            'experience',
            'degree',
            'descriptions',
            'industry1',
            'industry2',
            'link'
        ]]
        df = df.sort_values(
            by=['company', 'job_title', 'level'],
            ascending=[True, True, True]
        )
        log.info(f'Extracted {len(df)} number of jobs')

        return df
