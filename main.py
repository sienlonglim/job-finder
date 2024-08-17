import sys
import logging
from datetime import datetime

import yaml

from modules.job_finder import LinkedInJobFinder
from modules.mailer import EmailServer

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
    log = logging.getLogger()
    log.info(f"{'-'*20} Started new run @ {datetime.now().strftime('%Y-%m-%d:%H%M')} {'-'*20}")
    job_finder_resource = LinkedInJobFinder()
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        JOB_TITLES = config['job_titles']
        PAGES = config['pages']
        EMAIL_CONFIG = config['email_config']

    for keyword in JOB_TITLES:
        log.info(f"{'-'*20} GETTING LINKS : {keyword} {'-'*20}")
        job_finder_resource.retrieve_linkedin_jobs_by_keywords(
            keyword=keyword,
            pages=5
        )
        log.info(f"{'-'*20}  GETTING INFO : {keyword} {'-'*20}")
        job_infos = job_finder_resource.get_all_individual_job_informations()
        df = LinkedInJobFinder.process_df(
            data=job_infos,
            remove_duplicates=True,
            remove_nulls=True
        )

    mailer = EmailServer()
    mailer.send_email(
        subject=EMAIL_CONFIG['subject'],
        body=f'Total of {len(df)} jobs retrieved',
        recipients=EMAIL_CONFIG['recipients']
    )
