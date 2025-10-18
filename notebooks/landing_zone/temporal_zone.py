# %% [markdown]
# # Landing Zone
#
# This notebook contains the different steps involved steps in the the extraction of data and its storage in the landing zone of our data management pipeline. Particularly, the following scripts are responsible of the following tasks:
# 1. Environment setup, such as the preparation of the data lake (based on MinIO)
# 2. Obtaining of data from datasources
# 3. Raw data storaging into the temporal landing
# 4. Data shipment from temporal landing to persistent landing
#
# ## Environment Setup
# Before starting to get data from datasources it is needed to prepare our temporal landing. As said before, we will be using MinIO, an S3-compatible object storage implementation, as a data lake to store data as it comes. Before continuing, ensure that a MinIO instance is up and running, which can be done easily with Docker Compose (see the main [README](../../README.md) file for more information).
#
# First of all, we will connect to the MinIo instance, create a bucket for the landing zone and a subfolder that will correspond to the temporal landing. To interact with MinIO programatically we will use the [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-example-creating-buckets.html) Python library.

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

new_bucket = "landing-zone"
try:
    minio_client.create_bucket(Bucket=new_bucket)
except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
    print(f"Bucket '{new_bucket}' already exists")


# %% [markdown]
# # Obtaining data from datasources
# After the connection to the MinIO has been done and the first bucket created, now we need to obtain the data from the different data sources. This datasources have already been created in the first part of the script so we only need to retrieve them and import them into the temporal landing zone inside MinIO.

# %%
import os
DATASET_COUNT = 3
for i in range(1, DATASET_COUNT + 1):
    dataset_path = f"../../output/dataset{i}/"
    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                minio_client.upload_file(file_path, new_bucket, file)
                print(f"Uploaded {file} to s3://{new_bucket}/{file}")
            except Exception as e:
                print(f"Failed to upload {file}: {e}")


