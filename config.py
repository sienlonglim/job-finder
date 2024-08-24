from dataclasses import dataclass
import os
import json


@dataclass
class MainConfig:
    jobs = {
        'data scientist': 10,
        # 'data analyst': 10,
        # 'data engineer': 10
    }
    email_subject = "LinkedIn JobFinder Summary"
    email_recipients = json.loads(os.environ['EMAIL_RECIPIENTS'])
    email_body = ""
    bucket_name = os.environ["AMAZON_S3_BUCKET_NAME"]
    bucket_subfolder = os.environ["AMAZON_S3_BUCKET_SUBFOLDER"]
