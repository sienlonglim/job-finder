import yaml
import os
import time
from datetime import datetime
from modules.utils import *

if __name__ == '__main__':
    logger_main = configure_logging('utils_logger', "logs/app.log")
    logger_main.info(f"----------------------------- Started new run @ {datetime.now().strftime('%Y-%m-%d:%H%M')} ----------------------------")
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        keyword_list = config['job_titles']
        pages = config['pages']
    
    df_list = []
    try:
        for keyword in keyword_list:
            logger_main.info(f"-----------------------------  GETTING LINKS : {keyword} ----------------------------")
            links = get_job_links_selenium(keyword, pages=pages)
            main = {}
            time.sleep(10)
            logger_main.info(f"-----------------------------  GETTING INFO : {keyword} ----------------------------")
            for index, link in enumerate(links):
                try:
                    main[index] = get_job_info(link, index)
                except AttributeError as e:
                    # Nonetype encountered once, unsure what is the cause yet
                    logger_main.error(e, exc_info=True)
            df = process_df(main, remove_nulls=True, remove_duplicates=True)
            df_list.append(df)

        # Get latest file by date  
        file_directory = sorted([file for file in os.listdir('files') if file.startswith('MAIN')])
        if len(file_directory)>0:
            mainfile = file_directory[-1]
            mainfilepath = f'files/{mainfile}'
            filename = 'MAIN'
        else:
            mainfilepath = None
            filename = 'BATCH'
        
        # Merge and clean files
        main_df = update_main(mainfilepath, df_list)
        save_filepath = f"files/{filename}_{datetime.now().strftime('%Y-%m-%d')}.xlsx" # If not merging, filename will start with BATCH, otherwise it will be MAIN
        main_df.to_excel(save_filepath, engine='xlsxwriter')

        # Read the log file to send
        body = ''
        with open('logs/app.log', 'r') as f:
            for line in f.readlines():
                body += line

        # Send mail, if successful, delete file from repository
        if start_email_server_and_send(config, body, [save_filepath, 'logs/app.log']): 
            if os.path.exists(save_filepath):
                os.remove(save_filepath)
                logger_main.info(f"{save_filepath} deleted")

    except Exception as e:
        # Log any unexpected errors
        logger_main.error(e, exc_info=True)
    finally:
        handlers = logger_main.handlers[:]
        for handler in handlers:
            logger_main.removeHandler(handler)

    