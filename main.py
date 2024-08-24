import sys
import os
import logging
from datetime import datetime

from config import MainConfig
from modules.job_finder.job_finder import LinkedInJobFinder
from modules.mailer import EmailServer

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
    log = logging.getLogger()
    start_time = datetime.now()
    log.info(f"{'-'*20} Started new run @ {start_time.strftime('%Y-%m-%d:%H%M')} {'-'*20}")

    job_finder_resource = LinkedInJobFinder()
    for keyword, pages in MainConfig.jobs.items():
        log.info(f"{'-'*20} GETTING LINKS : {keyword} {'-'*20}")
        job_finder_resource.retrieve_linkedin_jobs_by_keywords(
            keyword=keyword,
            pages=pages
        )
        log.info(f"{'-'*20}  GETTING INFO : {keyword} {'-'*20}")
        job_infos = job_finder_resource.get_all_individual_job_informations()
        df = LinkedInJobFinder.process_dict_to_df(
            data=job_infos,
            remove_duplicates=True,
            remove_nulls=True
        )

    mailer = EmailServer()
    mailer.send_email(
        subject=MainConfig.email_subject,
        body=f"Completed run with total of {len(df)} jobs retrieved"
        f"\nStart time: {start_time.strftime('%Y-%m-%d:%H%M')}"
        f"\nEnd time: {datetime.now().strftime('%Y-%m-%d:%H%M')}"
        f"\n\n{MainConfig.email_subject}",
        recipients=MainConfig.email_recipients
    )
