import yaml
import os
import time
from datetime import datetime
from modules.utils import *

if __name__ == '__main__':
    logger_main = configure_logging(f"logs/app.log")
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
        mainfile = sorted(os.listdir('files'))[-1]
        main_df = update_main('files/'+mainfile, df_list)
        new_main_file = f"files/MAIN_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        main_df.to_excel(new_main_file, engine='xlsxwriter')
        start_email_server_and_send(config, [new_main_file, 'logs/app.log'])

    except Exception as e:
        # Log any unexpected errors
        logger_main.error(e, exc_info=True)
    finally:
        handlers = logger_main.handlers[:]
        for handler in handlers:
            logger_main.removeHandler(handler)

    