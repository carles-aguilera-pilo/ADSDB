
import boto3
import os
from dotenv import load_dotenv
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
import io
from tqdm import tqdm
import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from connection import Connection
from notebooks.trusted_zone.aStrategyTrusted import StrategyTrustedZone

new_bucket = "trusted-zone"
bucket_origen = "formatted-zone"
bucket_desti = "trusted-zone"
prefix_origen = "images/"
mida_final = (600, 450)


class TrustedZoneImages(StrategyTrustedZone):
    
    def executar(self):
        minio_client = Connection()
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")
        analysis = []
        paginator = minio_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket="formatted-zone", Prefix="images/"):
            for obj in tqdm(page.get("Contents", []), desc="Processant imatges"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket="formatted-zone", Key=key)
                image_data = response["Body"].read()
                analysis.append(self.analisi_imagen(image_data))
        df= pd.DataFrame(analysis)
        df.head()
        paginator = minio_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_origen, Prefix=prefix_origen):
            for obj in tqdm(page.get("Contents", []), desc="Processant imatges"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket=bucket_origen, Key=key)
                image_data = response["Body"].read()
                try:
                    img = Image.open(io.BytesIO(image_data)).convert("RGB")
                except Exception as e:
                    print(f"Error amb {filename}: {e}")
                    continue
                img = img.resize(mida_final)
                brightness_enhancer = ImageEnhance.Brightness(img)
                img = brightness_enhancer.enhance(1.1)  # +10% brillo
                contrast_enhancer = ImageEnhance.Contrast(img)
                img = contrast_enhancer.enhance(1.15)  # +15% contraste
                color_enhancer = ImageEnhance.Color(img)
                img = color_enhancer.enhance(1.05)  # +5% saturación
                img = img.filter(ImageFilter.GaussianBlur(radius=0.3))  # Suavizado ligero
                img = img.filter(ImageFilter.SHARPEN)
                buffer = io.BytesIO()
                img.save(buffer, format="PNG", optimize=True)
                buffer.seek(0)
                new_key = f"images/{filename}"
                minio_client.put_object(
                    Bucket=bucket_desti,
                    Key=new_key,
                    Body=buffer
                )
                
        analysis_2 = []
        for page in paginator.paginate(Bucket="trusted-zone", Prefix="images/"):
            for obj in tqdm(page.get("Contents", []), desc="Processant imatges"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket="trusted-zone", Key=key)
                image_data = response["Body"].read()
                analysis_2.append(self.analisi_imagen(image_data))
        df= pd.DataFrame(analysis_2)
        df.head()


    def analisi_imagen(img):
        
        img = Image.open(BytesIO(img))
        modo = img.mode
        width, height = img.size
        image_np = np.array(img)
        brillo = np.mean(image_np)
        contraste = np.std(image_np)
        fosca = False
        brillant = False
        contrast = False
        
        if brillo < 80:
            fosca = True
        elif brillo > 200:
            brillant = True
        
        if contraste < 10:
            contrast = True

        necessita_nitidez = False
        variance = cv2.Laplacian(cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var()
        if variance < 50:
            necessita_nitidez = True
        
        #---- NOISE ----
        noise = ""
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (3,3), 0)
        diff = cv2.absdiff(gray, blur)
        local_variance = np.var(diff)
        
        if local_variance < 50:
            noise = 'Low'
        elif local_variance < 150:
            noise = 'Medium'
        else:
            noise = 'High'
        
        return{
            'brillo': brillo,
            'contraste': contraste,
            'fosc': fosca,
            'brillant': brillant,
            'contrast': contrast,
            'nitidez': necessita_nitidez,
            'noise': noise
        }