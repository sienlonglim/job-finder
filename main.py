import sys
import logging
from datetime import datetime

import yaml

from modules.job_finder import LinkedInJobFinder

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
    log = logging.getLogger()
    log.info(f"{'-'*20} Started new run @ {datetime.now().strftime('%Y-%m-%d:%H%M')} {'-'*20}")
    job_finder_resource = LinkedInJobFinder()
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        LIST_OF_JOB_TITLES = config['job_titles']
        PAGES = config['pages']
        EMAIL_CONFIG = config['email_config']

    for keyword in LIST_OF_JOB_TITLES:
        log.info(f"-----------------------------  GETTING LINKS : {keyword} ----------------------------")
        job_finder_resource.retrieve_linkedin_jobs_by_keywords(
            keyword=keyword,
            pages=5
        )
        log.info(f"-----------------------------  GETTING INFO : {keyword} ----------------------------")
        dictionary_file = job_finder_resource.get_individual_job_informations()
