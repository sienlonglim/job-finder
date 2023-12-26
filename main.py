import yaml
import os
from datetime import datetime
from modules.utils import *

if __name__ == '__main__':
    logger_main = configure_logging(f"logs/main_app_{datetime.now().strftime('%Y-%m-%d')}.log")
    logger_main.info(f"----------------------------- Started new run @ {datetime.now().strftime('%Y-%m-%d:%H%M')} ----------------------------")
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        keyword_list = config['job_titles']
        pages = config['pages']
    
    df_list = []
    try:
        for keyword in keyword_list:
            logger_main.info(f'-------------- GETTING JOB LINKS : {keyword} --------------')
            links = get_job_links(keyword, start_page=0, pages=pages)
            main = {}
            logger_main.info(f'-------------- GETTING JOB INFO : {keyword} ---------------')
            for index, link in enumerate(links):
                main[index] = get_job_info(link, index)
            df = process_df(main, remove_nulls=True, remove_duplicates=True)
            df_list.append(df)

        # Get latest file by date  
        mainfile = sorted(os.listdir('files'))[-1]
        main_df = update_main('files/'+mainfile, df_list)
        main_df.to_excel(f"files/MAIN_{datetime.now().strftime('%Y-%m-%d')}.xlsx", engine='xlsxwriter')

    except Exception as e:
        # Log any errors and save the soups as pickle
        logger_main.error(e)
    finally:
        handlers = logger_main.handlers[:]
        for handler in handlers:
            logger_main.removeHandler(handler)

    