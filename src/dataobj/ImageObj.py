from abc import ABC, abstractmethod
from dataobj.ADataObj import ADataObj
from PIL import Image
from minio_connection import MinIOConnection
import os
import io

class ImageObj(ADataObj):
    # path_prefix
    # filename
    # extension
    # image

    def __init__(self, key, image_data):
        self.path_prefix = os.path.splitext(key.split("/")[0])
        split_filename = os.path.splitext(key.split("/")[1])
        self.filename = split_filename[0]
        self.extension = split_filename[1].lower()
        self.image = Image.open(io.BytesIO(image_data))

    def save(self, bucket_destination):        
        buffer = io.BytesIO()
        self.image.save(buffer, format=self.extension)
        buffer.seek(0)

        key = self.path_prefix + self.filename + self.extension
        minio_client = MinIOConnection()
        minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=key)
        minio_client.head_object(Bucket=bucket_destination, Key=key) # Checks if the file was uploaded successfully and throws an exception otherwise.
   
    def format(self):
        buffer = io.BytesIO()
        self.image.save(buffer, format="PNG")
        buffer.seek(0)
        self.image = Image.open(buffer)
        self.extension = ".png"