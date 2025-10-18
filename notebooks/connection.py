import boto3
import os
from dotenv import load_dotenv

class Connection:
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            load_dotenv()
            access_key_id = os.getenv("ACCESS_KEY_ID")
            secret_access_key = os.getenv("SECRET_ACCESS_KEY")
            minio_url = "http://" + os.getenv("S3_API_ENDPOINT")
            cls._instance = boto3.client(
                "s3",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                endpoint_url=minio_url
            )
        return cls._instance