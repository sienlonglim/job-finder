import os

import boto3


class AmazonS3:
    def __init__(
        self,
    ):
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("REGION")
        )
