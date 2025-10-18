
import boto3
import os
from dotenv import load_dotenv
import connection

class TemporalZone(StrategyLandingZone):
    
    def executar(self):
        minio_client = connection.Connection()
        new_bucket = "landing-zone"
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")
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