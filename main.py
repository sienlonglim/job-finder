import logging
import yaml
import os
from datetime import datetime
from modules.utils import *

if __name__ == '__main__':
    logger_main = logging.getLogger(__name__)
    logger_main.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(f"logs/app.log_{datetime.now().strftime('%Y-%m-%d')}", mode='w')
    file_handler.setFormatter(formatter)
    logger_main.addHandler(file_handler)
    logger.addHandler(file_handler)

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        keyword_list = config['job_titles']
        pages = config['pages']
    
    most_recent_filepaths = []
    for keyword in keyword_list:
        links, urls = get_job_links(keyword, start_page=0, pages=pages)
        main = {}
        soups = {}
        logger.info(f'-------------------------------- GETTING JOB INFO : {keyword} ----------------------------------')
        for index, link in enumerate(links):
            main[index], soups[index] = get_job_info(link, index)
        df = process_df(main, remove_nulls=True, remove_duplicates=True)
        most_recent_filepath = f"temp/{keyword}_{datetime.now().strftime('%Y-%m-%d-%H%M')}.xlsx"
        df.to_excel(most_recent_filepath, engine='xlsxwriter')
        most_recent_filepaths.append(most_recent_filepath)

    mainfile = sorted(os.listdir('files'))[-1]
    main_df = append_to_main('files/'+mainfile, most_recent_filepaths)
    main_df.to_excel(f"files/MAIN_{datetime.now().strftime('%Y-%m-%d')}.xlsx", engine='xlsxwriter')