import dataclasses
import os


@dataclasses
class MainConfig:
    jobs = {
        'data scientist': 10,
        'data analyst': 10,
        'data engineer': 10
    }
    email_subject = ""
    email_recipients = os.environ['email_recipients']
