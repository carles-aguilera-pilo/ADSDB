# %% [markdown]
# # Formatted Zone (Audio)
# 
# This notebook contains the scripts needed for the extraction of audio from the persistent landing zone, its processing and storage to the formatted zone. The formatted zone is represented by another bucket and aims to replicate the same folder structure as the persistent landing zone. The difference is that the data format in the formatted zone has been homogenized, as one of the steps of our data pipeline. 
# 
# This notebook focuses only on images data (the equivalent notebooks for the other types of data can be found in the same folder). Particularly, the following scripts are responsible of the following tasks:
# 1. Extraction of audios from persistent landing zone.
# 2. Homogenization of data. In this case, that will consist on ensuring that all audios are converted to .mp3 files.
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
# Now, for each audio in the persistent landing zone the following script will donwload it, convert it to mp3 format and store it in the formatted zone. Notice that the old versions are kept in the persistent landing zone so the raw data is still available if it is needed.
# 
# The script uses [pydub](https://github.com/jiaaro/pydub/tree/master) to perform image manipulation, so the range of supported image formats of our pipeline depends on this library. Despite some formats such as mp3, wav or raw are natively supported by pydub, it is needed to setup [ffmpeg](https://www.ffmpeg.org/ffmpeg-codecs.html#Audio-Encoders) to unlock a wider range of available options. The instructions to install ffmpeg can be found [here](https://github.com/jiaaro/pydub#getting-ffmpeg-set-up).

# %%
from pydub import AudioSegment
from botocore.exceptions import ClientError
import io

bucket_origin = "persistent-landing"
bucket_destination = "formatted-zone"
path_prefix = "audio/"

paginator = minio_client.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket=bucket_origin, Prefix=path_prefix):
    for obj in page["Contents"]:
        key = obj["Key"]
        split_filename = os.path.splitext(key.split("/")[1])
        filename = split_filename[0]
        format = split_filename[1].lower()
        
        try:
            response = minio_client.get_object(Bucket=bucket_origin, Key=key)

            # Audio conversion to mp3
            audio_data = response["Body"].read()
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            buffer = io.BytesIO()
            audio.export(buffer, format="mp3")
            buffer.seek(0)

            # Upload audio to formatted zone
            new_key = path_prefix + filename + ".mp3"
            minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=new_key)
            minio_client.head_object(Bucket=bucket_destination, Key=new_key) # Checks if the file was uploaded successfully and throws an exception otherwise.
        except ClientError as e:
            print(f"[ERROR]: An error occurred while moving {filename} between zones: {e}")
        except Exception as e:
            print(f"[ERROR]: An error occurred while manipulating {filename}: {e}")


