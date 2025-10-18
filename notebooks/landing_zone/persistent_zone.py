
import boto3
import os
from dotenv import load_dotenv
from tqdm import tqdm
import connection


landing_zone = "landing-zone"
persistent_landing = "persistent-landing"
new_bucket = "persistent-landing"

class PersistentZone(StrategyLandingZone):
    
    def executar(self):
        minio_client = connection.Connection()
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")
        paginator = minio_client.get_paginator("list_objects_v2")
        file_extensions = set()
        for page in paginator.paginate(Bucket=landing_zone):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                if "." in key:
                    extension = os.path.splitext(key)[1].lower()
                    if extension:
                        file_extensions.add(extension)
        print(f"File types discovered: {file_extensions}")
        folder_map = {
            ".mp3": "audio",
            ".wav": "audio",
            ".ogg": "audio",
            ".png": "images",
            ".jpg": "images",
            ".jpeg": "images",
            ".csv": "tabular",
            ".parquet": "tabular",
            ".txt": "text",
            ".md": "text",
            ".json": "text",
        }
        for page in paginator.paginate(Bucket=landing_zone):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")

                file_ext = os.path.splitext(key)[1].lower()
                dest_folder = folder_map.get(file_ext, file_ext.strip("."))
                if not dest_folder:
                    dest_folder = "others"
                new_key = f"{dest_folder}/{os.path.basename(key)}"
                copy_source = {
                    'Bucket': landing_zone,
                    'Key': key
                }
                minio_client.copy_object(
                    CopySource=copy_source,
                    Bucket=persistent_landing,
                    Key=new_key
                )
        print("Files have been organized in the persistent landing bucket.")
        for page in paginator.paginate(Bucket=landing_zone):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                minio_client.delete_object(Bucket=landing_zone, Key=key)
        print("Temporary landing files have been removed.")