import requests, re, time, logging, smtplib
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import FirefoxOptions
from datetime import datetime
from functools import wraps
from bs4 import BeautifulSoup
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

headers = {'Accept': 'text/html',
           'Accept-Language': 'en-US',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
           'Referer': 'http://www.google.com/'}

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f'Function {func.__name__} Took {total_time:.4f} seconds - {args} {kwargs}')
        return result
    return timeit_wrapper

def configure_logging(file_path=None, streaming=None, level=logging.INFO):
    '''
    Initiates the logger
    '''

    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if not len(logger.handlers):
        # Add a filehandler to output to a file
        if file_path:
            file_handler = logging.FileHandler(file_path, mode='w')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Add a streamhandler to output to console
        if streaming:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)    

    return logger

logger = configure_logging(f"logs/app.log")

@timeit
def get_job_links(keyword: str, start_page: int, pages: int)-> tuple:    
    '''Function to retrieve all job links over specified number of pages and search
    Inputs:
        keyword: str - job title and other keywords
        start_page: int - page to start
        pages: int - number of pages to retrieve
    Returns 
        dictionary counter of Job links
    '''
    def custom_selector(tag):
        '''
        Helper function used to identify a href tag with belongs to the job link
        Inputs:
            soup tag
        Returns soup tag
        '''
        return tag.name == "a" and tag.has_attr("href") and keyword in tag.get('href')
    
    title = re.sub(' ', '%20', keyword.lower()) # This is used for building url
    keyword = re.sub(' ', '-', keyword.lower()) # This is used inside custom_selector's scope   

    logger.info(f'Searching for {keyword}')
    job_links = {}
    jobId_list = []
    position = start_page
    currentJobId = None
    
    for page in range(pages):
        try:
            logger.info(f'Searching using JobId: {currentJobId}')
            if not currentJobId:
                url = f"https://www.linkedin.com/jobs/search/?distance=25&geoId=102454443&keywords={title}&location=Singapore&start={position}"
            else:
                # url = f"https://www.linkedin.com/jobs/search/?currentJobId={currentJobId}&geoId=102454443&keywords={title}&location=Singapore&start={position}"
                # url = f"https://www.linkedin.com/jobs/search/?currentJobId={currentJobId}&distance=25&geoId=102454443&keywords={title}&origin=JOB_SEARCH_PAGE_KEYWORD_HISTORY&refresh=true&start={position}"
                url = f"https://www.linkedin.com/jobs/search/?currentJobId={currentJobId}&distance=25&geoId=102454443&keywords={title}&currentJobId={currentJobId}&position=1&pageNum=0&start={position}"
            
            response = requests.get(url, headers=headers)
            logger.info(f"Page {page} : {response.status_code}")
            soup = BeautifulSoup(response.text,'html.parser')
            tags = soup.find_all(custom_selector)

            # Get the link and jobid for each listed job
            for tag in tags:
                link = tag.get('href')
                link = link.split('?')[0] # Tidy up the link to remove the trackingid
                job_links.setdefault(link, 0)
                job_links[link] +=1

                # Get JobID from links
                jobId = re.findall('-([0-9]{6,})', link)[0]
                jobId_list.append(jobId) 
                
            # Sort the JobId to get the latest number
            jobId_list.sort(reverse=True)
            jobId = jobId_list[0]
            if currentJobId is None:
                currentJobId = jobId
            elif currentJobId == jobId:
                position += 25
            else:
                currentJobId = jobId
                position = 0
            logger.info(f'\t- Cumulative unique links: {len(job_links)}')
        except Exception as e:
            logger.error(f'Error at page {page}, {e}')
    return job_links

def get_job_links_selenium(keyword: str, pages: int, debug: bool = False)-> tuple:    
    '''Function to retrieve all job links over specified number of pages and search
    Inputs:
        keyword: str - job title and other keywords
        pages: int - number of pages to retrieve, achieved through scrolling with Selenium
        debug: bool - if True, returns the page_source 
    Returns 
        dictionary counter of Job links
    '''
    
    title = re.sub(' ', '%20', keyword.lower()) # This is used for building url
    keyword = re.sub(' ', '-', keyword.lower()) # This is used inside custom_selector's scope   

    logger.info(f'Searching for {keyword}')
    data = {}

    # Not using context manager, because we may need to close and restart if running into an authentication wall
    opts = FirefoxOptions()
    if not debug:
        # This will run FireFox without a display, needed to work with GitHub actions
        opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    driver.implicitly_wait(30)
    driver.get(f"https://www.linkedin.com/jobs/search/?distance=25&geoId=102454443&keywords={title}&location=Singapore&start=0")
    html_source = driver.page_source
    soup = BeautifulSoup(html_source,'html.parser')
    retry_count = 0
    # Sometimes we will run into an authentication wall, retry again until successful
    while retry_count < 5 and "Sign Up | LinkedIn" in soup.find('title').text:
        print(f"\tRan into AuthWall, trying again in 5 secs...")
        driver.quit()
        time.sleep(5)
        driver = webdriver.Firefox(options=opts)
        driver.get(f"https://www.linkedin.com/jobs/search/?distance=25&geoId=102454443&keywords={title}&location=Singapore&start=0")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source,'html.parser')
        retry_count +=1

    for _ in range(0,pages):
        time.sleep(2)
        webdriver.ActionChains(driver).scroll_by_amount(0, -10).perform() # Need to scroll up a little to trigger infinite scroll
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try: # Occasionally there will be a click to see more button appear, need to click on it, sometimes two clicks are needed
            element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located(
                    (By.XPATH,'//*[@id="main-content"]/section[2]/button')))
            if element:
                driver.execute_script("arguments[0].click()", element)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click()", element)
        except Exception as e:
            print(e)
        
    # Get the full html after scrolling is complete, then parse via bs4
    logger.info('Getting page_source')
    html_source = driver.page_source
    soup = BeautifulSoup(html_source,'html.parser')
    driver.quit()
    def custom_selector(tag):
        '''
        Helper function used to identify a href tag with belongs to the job link
        Inputs:
            soup tag
        Returns soup tag
        '''
        return tag.name == "a" and tag.has_attr("href") and keyword in tag.get('href')
    tags = soup.find_all(custom_selector)

    # Get the link and jobid for each listed job
    for tag in tags:
        link = tag.get('href')
        link = link.split('?')[0] # Tidy up the link to remove the trackingid
        if 'login' not in link: # To handle a login link that shows at the end
            data.setdefault(link, 0)
            data[link] += 1
    logger.info(f'Unique links: {len(data)}')
    if debug:
        return data, soup
    else:
        return data

def get_job_info(url: str, index: int, return_soup: bool=False):
    '''
    Function to retrieve information for an individual job page
    Inputs:
        url: str - url for job page
        index: int - index of file for tracking
        return_soup: bool - whether to return the soup object for debugging
    Returns
        dict
    '''
    retry_count = 0
    response = requests.get(url, headers=headers)
    logger.info(f"Index {index} : {response.status_code}")
    soup = BeautifulSoup(response.text,'html.parser')

    # Sometimes we will run into an authentication wall, retry again until successful
    while retry_count < 5 and "https://www.linkedin.com/authwall?trk=" in soup.find('script').text:
        logger.info(f"\tRan into AuthWall, trying again in 5 secs...")
        time.sleep(5)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text,'html.parser')
        retry_count +=1
    if retry_count>0:
        logger.info(f"\tSuccess : {response.status_code}")
        
    info = {}

    # JobID
    jobid = re.findall('-(\d{8,})', url) # removed [\?/] from pattern because of url cleaning ? away in new version
    if len(jobid) == 1 :
        info['job_id'] = str(jobid[0])
    else:
        logger.error(f'Index {index}: Found no Job ID or multiple Job IDs for {url}')
    
    info['date_logged'] = datetime.now().strftime('%Y-%m-%d')

    # Page title
    title = soup.find('title')
    if title:
        info['company'] = title.text.split(' hiring')[0]
    else:
        logger.error(f'Index {index}: Found no company name for {url}')

    # Job title
    job_title = soup.find('h1')
    if job_title:
        info['job_title'] = job_title.text
    else:
        logger.error(f'Index {index}: Found no job title for {url}')

    # Job level, type (full time etc), sector
    criteria = soup.find_all('span', class_="description__job-criteria-text description__job-criteria-text--criteria")
    if criteria:
        criteria = [x.text.strip(' \n') for x in criteria]
        fields = ['level', 'job_type', 'industry1', 'industry2']
        for field, criterion in zip(fields, criteria):
            info[field] = criterion

    # Job scope and requirements
    descriptions = soup.find(class_ = "show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden")
    if descriptions:
        # Create empty strings to append to
        line_by_line_desc = ''
        experience = ''
        spark = ''
        degree = ''

        for tag in descriptions.children: # children is a generator of all the tags contained, the alternative to the full tags is .content
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
            if ('PySpark' in description) or ('Spark' in description):
                spark += '\u2022' + description + '\n'
            if 'degree' in description:
                degree += '\u2022' + description + '\n'

            info['descriptions'] = line_by_line_desc
            info['degree'] = degree
            info['experience'] = experience   
            info['spark'] = spark 
    else: # Print notification if nothing found
        logger.error(f'Index {index}: Found no description for {url}')

    info['link'] = url            
    
    if return_soup:
        return info, soup
    else:
        return info
    
def process_df(data: dict, remove_nulls: bool=True, remove_duplicates: bool=True)-> pd.DataFrame:
    '''
    Function to process the dictionaries into a Pandas DataFrame
    Inputs:
        data: dict - dictionary with information fields
    Returns:
        pd.DataFrame - dataframe which is deduplicated, and sorted
    '''
    df = pd.DataFrame.from_dict(data, orient='index')
    df = df.set_index('job_id')

    if remove_nulls:
        wNulls = len(df)
        df = df[~(df['company'].isnull() & df['job_title'].isnull() & df['level'].isnull() & df['descriptions'].isnull())]
        logger.info(f'Removed {wNulls - len(df)} empty rows')

    # Deduplication, some jobs are similar but have different link maybe due to their different posting time / reposting
    if remove_duplicates:
        duplicate_subset = ['company', 'job_title', 'level', 'job_type', 'descriptions', 'industry1']
        wDups = len(df)
        # df = df[~df.index.duplicated(keep='first')]
        df = df.drop_duplicates(subset=duplicate_subset)
        logger.info(f'Removed {wDups - len(df)} duplicates')

    # Sorting order and values
    df = df[['date_logged', 'company', 'job_title', 'level', 'job_type', 'experience', 'spark', 'degree', 'descriptions', 'industry1', 'industry2', 'link']]
    df = df.sort_values(by=['company', 'job_title', 'level'],
                        ascending= [True, True, True])
    logger.info(f'Extracted {len(df)} number of jobs')

    return df

def update_main(main_df, df_list: list) -> pd.DataFrame:
    '''
    Function to append a list of pandas dataframes to a main excel file
    Inputs:
        main_df: 
            if str: filepath to mainfile
            if pandas dataframe : main df to append to
        df_list: list - list of dataframes or filepaths to iterate through
    Returns:
        pd.DataFrame: a compiled dataframe
    '''
    # Appending to existing dataframe
    if isinstance(main_df, str):
        logger.info(f'Loading main_df from file: {main_df}')
        main_df = pd.read_excel(main_df, index_col=0)
    elif isinstance(main_df, pd.DataFrame):
        logger.info('Main_df already in memory')
    original_rows = len(main_df)
    logger.info(f'Original rows of main_df: {original_rows}')

    for index, df in enumerate(df_list):
        if isinstance(df, pd.DataFrame):
            pass
        elif isinstance(df, str):
            df = pd.read_excel(df, index_col=0)
        logger.info(f'Read rows from df {index}: {len(df)}')
        main_df = pd.concat([main_df, df])
        duplicate_subset = ['company', 'job_title', 'level', 'job_type', 'descriptions', 'industry1']
    
    # main_df = main_df[~main_df.index.duplicated(keep='first')] # This drops by index instead
    main_df = main_df.drop_duplicates(subset=duplicate_subset)
    logger.info(f'\tAdded rows: {len(main_df)-original_rows}')
    
    return main_df

def _send_email(server: smtplib.SMTP_SSL, subject: str, body: str, recipients: list, attachments: list):
    '''
    Sends an email with the given parameters
    Inputs:
        server: smtplib server object
        subject: str - subject of email
        body: str - body of the email, in html format
        recipients: list of str - email addresses to send to
        attachments: list of str - filepaths of attachments
    '''
    # Create the multipart object
    message = MIMEMultipart()
    # Standard fields
    message['Subject'] = subject
    message['From'] = os.environ['email']
    message['To'] = ', '.join(recipients)

    # HTML body
    html_part = MIMEText(body, 'html')
    message.attach(payload=html_part)

    # Add the attachments:
    if attachments is not None:
        for filepath in attachments:
            with open(filepath, 'rb') as file:
                # Create a MIMEBase object to store the info
                attachment_part = MIMEBase('application', 'octet-stream')
                attachment_part.set_payload((file).read())

            # Encode, add header
            encoders.encode_base64(attachment_part)
            attachment_part.add_header(
            "Content-Disposition",
            "attachment", filename= os.path.basename(filepath)) # This os function takes only the filename
            message.attach(payload=attachment_part)

    server.sendmail(os.environ['email'], recipients, message.as_string())
    print(f"Message sent to {recipients}!")

def start_email_server_and_send(config, attachments):
    subject = config['email']['subject']
    body = config['email']['body']
    recipients = config['email']['recipients']

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(os.environ['email'], os.environ['app_pass'])
        smtp_server.ehlo()
        _send_email(smtp_server, subject, body, recipients, attachments)
        logger.info('Email sent!')