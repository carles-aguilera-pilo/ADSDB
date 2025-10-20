from abc import ABC, abstractmethod
from src.minio_connection import MinIOConnection
from src.dataobj.ImageObj import ImageObj

supported_modals = ["image", "audio", "text"]

class AZone(ABC):

    def __init__(self, bucket_origin, bucket_destination):
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination

    @abstractmethod
    def treatData(obj):
        pass

    def execute(self):
        minio_client = MinIOConnection()
        try:
            minio_client.create_bucket(Bucket=self.bucket_destination)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{self.bucket_destination}' already exists")
        
        paginator = minio_client.get_paginator("list_objects_v2")

        for modal in self.supported_modals:
            for page in paginator.paginate(Bucket=self.bucket_origin, Prefix=modal):
                for obj in page["Contents"]:
                    key = obj["Key"]
                    response = minio_client.get_object(Bucket=self.bucket_origin, Key=key)
                    
                    ###########################################
                    # Apply factory pattern
                    o = None
                    if modal == "images":
                        o = ImageObj(key, response["Body"].read())
                    #elif modal == "audios":
                    #    o = AudioObj(key, response["Body"].read())
                    #elif modal == "texts":
                    #    o = TextObj(key, response["Body"].read())
                    ###########################################

                    self.treatData(o)