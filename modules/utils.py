import requests
import re
import pandas as pd
from datetime import datetime
from time import perf_counter
from functools import wraps
from bs4 import BeautifulSoup
import logging

headers = {'Accept': 'text/html',
           'Accept-Language': 'en-US',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
           'Referer': 'http://www.google.com/'}

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
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
            file_handler = logging.FileHandler(file_path, mode='a')
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
        list of job links
        list of actual urls used
        counter dictionary of JobId
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
    try:
        for page in range(pages):
            logger.info(f'Searching using JobId: {currentJobId}')
            if not currentJobId:
                url = f"https://www.linkedin.com/jobs/search/?distance=25&geoId=102454443&keywords={title}&location=Singapore&start={position}"
            else:
                # url = f"https://www.linkedin.com/jobs/search/?currentJobId={currentJobId}&geoId=102454443&keywords={title}&location=Singapore&start={position}"
                # url = f"https://www.linkedin.com/jobs/search/?currentJobId={currentJobId}&distance=25&geoId=102454443&keywords={title}&origin=JOB_SEARCH_PAGE_KEYWORD_HISTORY&refresh=true&start={position}"
                url = f"https://www.linkedin.com/jobs/search/?currentJobId={currentJobId}&distance=25&geoId=102454443&keywords={title}&currentJobId={currentJobId}&position=1&pageNum=0&start={position}"
            
            response = requests.get(url, headers=headers)
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
            logger.info(f'Page {page} - Cumulative unique links: {len(job_links)}')
    except Exception as e:
        logger.error(f'Error at page {page}, {e}')
        raise(e)
    finally:
        return job_links
    
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
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text,'html.parser')
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
        # try:
        #     info['level'] = criteria[0]
        #     info['job_type'] = criteria[1]
        #     info['industry1'] = criteria[2]
        #     info['industry2'] = criteria[3]
        # except Exception as e:
        #     logger.error(f'Index {index}: {e, criteria, url}')

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
        # subset_duplicates = ['company', 'job_title', 'level', 'job_type', 'degree', 'experience', 'spark', 'descriptions', 'industry1']
        wDups = len(df)
        df = df[~df.index.duplicated(keep='first')]
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
        main_df = main_df[~main_df.index.duplicated(keep='first')] # This drops by index instead

    logger.info(f'\tAdded rows: {len(main_df)-original_rows}')
    
    return main_df