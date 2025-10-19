
import boto3
import os
from dotenv import load_dotenv
import botocore.exceptions
import io
import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from connection import Connection
from src.formatted_zone.aStrategyFormatted import StrategyFormattedZone

bucket_origin = "persistent-landing"
bucket_destination = "formatted-zone"
path_prefix = "text/"
new_bucket = "formatted-zone"


class FormatedZoneText(StrategyFormattedZone):
    
    def executar(self):

        minio_client = Connection()
        self.provar_existencia_bucket(new_bucket, minio_client)

        paginator = minio_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket_origin, Prefix=path_prefix):
            for obj in page["Contents"]:
                key = obj["Key"]
                split_filename = os.path.splitext(key.split("/")[1])
                filename = split_filename[0]
                format = split_filename[1].lower()
                try:
                    response = minio_client.get_object(Bucket=bucket_origin, Key=key)
                    text_data = response["Body"].read()
                    buffer = io.BytesIO(text_data)
                    new_key = path_prefix + filename + ".txt"
                    minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=new_key)
                    minio_client.head_object(Bucket=bucket_destination, Key=new_key)
                except botocore.exceptions.ClientError as e:
                    print(f"[ERROR]: An error occurred while moving {filename} between zones: {e}")
                except Exception as e:
                    print(f"[ERROR]: An error occurred while manipulating {filename}: {e}")
                    
    def provar_existencia_bucket(self, bucket_name, minio_client):
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")