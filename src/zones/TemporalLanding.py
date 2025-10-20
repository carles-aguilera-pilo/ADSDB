import os
from src.minio_connection import MinIOConnection
from src.zones.AZone import AZone

class TemporalLanding(AZone):
    def __init__(self, bucket_origin, bucket_destination):
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination
        self.supported_modals = ["image", "audio", "text"] # TODO: Change to according values JOWI

    def treatData(self, dataobj):
        dataobj.save(self.bucket_destination)

    def execute(self):
        minio_client = MinIOConnection()
        try:
            minio_client.create_bucket(Bucket=self.bucket_destination)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{self.bucket_destination}' already exists")
        
        folder_map = {
            ".mp3": "audios",
            ".wav": "audios",
            ".ogg": "audios",
            ".png": "images",
            ".jpg": "images",
            ".jpeg": "images",
            ".txt": "texts",
            ".md": "texts",
            ".json": "texts",
        }
        
        paginator = minio_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket_origin):
            for obj in page.get("Contents",[]):
                key = obj["Key"]
                response = minio_client.get_object(Bucket=self.bucket_origin, Key=key)
                
                file_ext = os.path.splitext(key)[1].lower()
                dest_folder = folder_map.get(file_ext, file_ext.strip("."))
                if not dest_folder:
                    dest_folder = "others"
        
                new_key = f"{dest_folder}/{os.path.basename(key)}"
                copy_source = {
                    'Bucket': self.bucket_origin,
                    'Key': key
                }
                
                minio_client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.bucket_destination,
                    Key=new_key
                )
        
