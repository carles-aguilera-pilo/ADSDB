
import boto3
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from connection import Connection
from src.landing_zone.aStrategyLanding import StrategyLandingZone
class TemporalZone(StrategyLandingZone):
    
    def executar(self):
        print("Executing Temporal Zone...")
        minio_client = Connection()
        print(minio_client)
        new_bucket = "landing-zone"
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")
        DATASET_COUNT = 3
        for i in range(1, DATASET_COUNT + 1):
            dataset_path = f"output/dataset{i}/"
            if os.path.exists(dataset_path):
                for root, dirs, files in os.walk(dataset_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            minio_client.upload_file(file_path, new_bucket, file)
                        except Exception as e:
                            print(f"Failed to upload {file}: {e}")
            else:
                print(f"Path {dataset_path} does not exist")