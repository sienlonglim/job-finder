import sys
import logging
import json
from datetime import datetime

from config import MainConfig
from modules.job_finder.job_finder import LinkedInJobFinder
from modules.mailer import EmailServer
from modules.clients.amazon_s3 import AmazonS3

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
        json_data = json.dumps(job_infos)
    s3_client = AmazonS3()
    s3_client.upload_object(
        object=json_data,
        bucket_name=MainConfig.bucket_name,
        path=MainConfig.bucket_subfolder,
        filename=f"job-run-{start_time.date().strftime('%Y%m%d')}.json"
    )

    mailer = EmailServer()
    mailer.send_email(
        subject=MainConfig.email_subject,
        body=f"Completed run with total of {len(job_infos)} jobs retrieved"
        f"\nStart time: {start_time.strftime('%Y-%m-%d:%H%M')}"
        f"\nEnd time: {datetime.now().strftime('%Y-%m-%d:%H%M')}"
        f"\n\n{MainConfig.email_subject}",
        recipients=MainConfig.email_recipients
    )
