import os
import sys
import logging
from typing import Any

import boto3

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
log = logging.getLogger()


class AmazonS3:
    def __init__(
        self,
    ) -> None:
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("REGION")
        )
        log.info("Connected to S3")

    def list_buckets(
        self,
    ) -> None:
        response = self.client.list_buckets()
        for bucket in response['Buckets']:
            log.info(bucket["Name"])

    def upload_object(
        self,
        object: Any,
        bucket_name: str,
        path: str,
        filename: str
    ) -> None:
        keypath = os.path.join(path, filename).replace(os.path.sep, '/')
        self.client.put_object(
            Bucket=bucket_name,
            Key=keypath,
            Body=object
        )
        log.info(f"Uploaded {filename} successfully")


if __name__ == "__main__":
    s3_client = AmazonS3()
