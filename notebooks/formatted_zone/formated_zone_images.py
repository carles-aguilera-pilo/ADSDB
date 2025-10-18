# %% [markdown]
# # Formatted Zone (Images)
#
# This notebook contains the scripts needed for the extraction of images from the persistent landing zone, its processing and storage to the formatted zone. The formatted zone is represented by another bucket and aims to replicate the same folder structure as the persistent landing zone. The difference is that the data format in the formatted zone has been homogenized, as one of the steps of our data pipeline. 
#
# This notebook focuses only on images data (the equivalent notebooks for the other types of data can be found in the same folder). Particularly, the following scripts are responsible of the following tasks:
# 1. Extraction of images from persistent landing zone.
# 2. Homogenization of data. In this case, that will consist on ensuring that all images are converted to .png files.
# 3. Formatted data storage into the formatted zone.
#
# First, we will connect to MinIO and prepare the new bucket:

# %%
import boto3
import os
from dotenv import load_dotenv

load_dotenv()
access_key_id = os.getenv("ACCESS_KEY_ID")
secret_access_key = os.getenv("SECRET_ACCESS_KEY")
minio_url = "http://" + os.getenv("S3_API_ENDPOINT")


minio_client = boto3.client(
    "s3",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    endpoint_url=minio_url
)

new_bucket = "formatted-zone"
try:
    minio_client.create_bucket(Bucket=new_bucket)
except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
    print(f"Bucket '{new_bucket}' already exists")

# %% [markdown]
# Now, for each image in the persistent landing zone the following script will donwload it, convert it to png format and store it in the formatted zone. Notice that the old versions are kept in the persistent landing zone so the raw data is still available if it is needed.
# 
# The script uses Pillow to perform image manipulation, so the range of supported image formats of our pipeline depends on this library (which can be found in the [docs](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html). Some of them are .png, .jpg/.jpeg, .bmp, .tif/.tiff, .gif and .webp.

# %%
from PIL import Image
import botocore.exceptions
import io

bucket_origin = "persistent-landing"
bucket_destination = "formatted-zone"
path_prefix = "images/"

paginator = minio_client.get_paginator("list_objects_v2") # We use paginators because the list_objects method response is limitted to a maximum of 1,000 objects 

for page in paginator.paginate(Bucket=bucket_origin, Prefix=path_prefix):
    for obj in page["Contents"]:
        key = obj["Key"]
        split_filename = os.path.splitext(key.split("/")[1])
        filename = split_filename[0]
        format = split_filename[1].lower()
        
        try:
            response = minio_client.get_object(Bucket=bucket_origin, Key=key)

            # Image conversion to png
            image_data = response["Body"].read()
            image = Image.open(io.BytesIO(image_data))
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            # Upload image to formatted zone
            new_key = path_prefix + filename + ".png"
            minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=new_key)
            minio_client.head_object(Bucket=bucket_destination, Key=new_key) # Checks if the file was uploaded successfully and throws an exception otherwise.
        except botocore.exceptions.ClientError as e:
            print(f"[ERROR]: An error occurred while moving {filename} between zones: {e}")
        except Exception as e:
            print(f"[ERROR]: An error occurred while manipulating {filename}: {e}")

# %% [markdown]
# After this, all images should have been successfully uploaded to the formatted zone.


