from abc import ABC, abstractmethod
from minio_connection import MinIOConnection
from dataobj.ImageObj import ImageObj

class AZone(ABC):

    @abstractmethod
    def treatData(obj):
        pass

    def execute(self):
        minio_client = MinIOConnection()
        #self.provar_existencia_bucket(new_bucket, minio_client)
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