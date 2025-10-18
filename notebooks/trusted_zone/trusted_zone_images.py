# %% [markdown]
# # TRUSTED ZONE (IMAGES)
# This notebook contains the scripts needed for the extraction of images from the formatted zone, its processing and cleaning of the data and storage to the trusted Zone. The trusted zone is represented by another bucket and aims to replicate the same folder structure as the formatted zone. The difference is that the data has been processed and transform in order to clean and ensure a clean images.
#
# This notebook focuses only on images (the equivalent notebooks for the other types of data can be found in the same folder). Particularly, the following scripts are responsible of the following tasks:
#
# Extraction of images from formatted zone. Treatment and processing of the data, to ensure data quality.
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

new_bucket = "trusted-zone"
try:
    minio_client.create_bucket(Bucket=new_bucket)
except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
    print(f"Bucket '{new_bucket}' already exists")

# %% [markdown]
# Here we perform an analysis of the current state of the images to identify any anomalies or extreme values.
# 
# This step is essential to understand the initial condition of our images and to determine which types of treatments should be applied. In this case, we will focus mainly on aspects such as brightness, contrast, sharpness, and also noise levels.
# 
# After conducting this initial analysis, we will proceed with the correction and cleaning of the images. Finally, we will repeat the same study to verify that all detected issues have been successfully resolved.

# %%
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import pandas as pd

def analisi_imagen(img):
    
    img = Image.open(BytesIO(img))
    modo = img.mode
    width, height = img.size
    
    #---- BRIGTH AND CONTRAST ----
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
        
    #---- SHARPNESS ----
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

# %% [markdown]
# In this step, we apply the previously defined function to gather statistics for each image, helping us detect possible issues or anomalies.
# Once all images have been analyzed, we use the head() function to preview the first five entries and evaluate whether the cleaning process will be sufficient.
# 
# Here we can visualize the anomalies detected in each image.
# 
# It is important to note that, in this case, if we have a large number of images, the head() function will only display the first six entries. However, we can still analyze each specific image individually.
# Moreover, if a more detailed data analysis is required, the results can be exported to a CSV file for a complete statistical study in R or even in Python.
# 
# In this context, the analysis performed represents the main evaluation process aimed at improving the overall quality of the images.

# %%
analysis = []

paginator = minio_client.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket="formatted-zone", Prefix="images/"):
    for obj in tqdm(page.get("Contents", []), desc="Processant imatges"):
        key = obj["Key"]
        filename = key.split("/")[-1]
        
        #---- READ IMAGE ----
        response = minio_client.get_object(Bucket="formatted-zone", Key=key)
        image_data = response["Body"].read()
        
        #---- ANALYSIS ----
        analysis.append(analisi_imagen(image_data))
        
        
df= pd.DataFrame(analysis)
df.head()

# %% [markdown]
# This script is responsible for extracting images from the Formatted Zone, processing and cleaning them to ensure their quality, and finally storing them in the Trusted Zone. The process begins by reading all image files from the formatted-zone bucket and then applying various treatments to improve their visual quality.
# 
# First, it resizes all images to a consistent size of 600 by 450 pixels to ensure uniformity and optimize storage. Then, it converts all images to the RGB format to guarantee color compatibility and consistency.
# 
# Next, it applies color normalization to enhance visual appearance: it increases brightness by 10% to make the images lighter, improves contrast by 15% to make details more defined, and increases saturation by 5% to make colors more vivid and appealing.
# 
# The process also includes cleaning and quality enhancement treatments: it applies a slight smoothing using a Gaussian filter with a radius of 0.3 pixels to reduce digital noise, and then compensates for this smoothing by applying a sharpening filter to restore detail definition and maintain image clarity.

# %%
from PIL import Image, ImageEnhance, ImageFilter
import io
from tqdm import tqdm

bucket_origen = "formatted-zone"
bucket_desti = "trusted-zone"
prefix_origen = "images/"
mida_final = (600, 450)

paginator = minio_client.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket=bucket_origen, Prefix=prefix_origen):
    for obj in tqdm(page.get("Contents", []), desc="Processant imatges"):
        key = obj["Key"]
        filename = key.split("/")[-1]

        #Llegir la imatge des del bucket
        response = minio_client.get_object(Bucket=bucket_origen, Key=key)
        image_data = response["Body"].read()
        #Obrir amb PIL per validar i redimensionar
        try:
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            print(f"Error amb {filename}: {e}")
            continue

        #Redimensionar a mida consistent
        img = img.resize(mida_final)
        
        # APLICAR TRATAMIENTOS DE MEJORA
        
        # 1. Normalización de colores (ajustar brillo y contraste)
        # Ajustar brillo (ligeramente más brillante)
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.1)  # +10% brillo
        
        # Ajustar contraste (mejorar contraste)
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.15)  # +15% contraste
        
        # Ajustar saturación (colores más vivos)
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.05)  # +5% saturación
        
        # 2. Suavizado para reducir ruido
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))  # Suavizado ligero
        
        # 3. Aplicar filtro de nitidez para compensar el suavizado
        img = img.filter(ImageFilter.SHARPEN)

        #Desa a memòria i puja a trusted-zone
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)

        new_key = f"images/{filename}"
        minio_client.put_object(
            Bucket=bucket_desti,
            Key=new_key,
            Body=buffer
        )

# %%
analysis = []

for page in paginator.paginate(Bucket="trusted-zone", Prefix="images/"):
    for obj in tqdm(page.get("Contents", []), desc="Processant imatges"):
        key = obj["Key"]
        filename = key.split("/")[-1]
        
        #---- READ IMAGE ----
        response = minio_client.get_object(Bucket="trusted-zone", Key=key)
        image_data = response["Body"].read()
        
        #---- ANALYSIS ----
        analysis.append(analisi_imagen(image_data))
        
        
df= pd.DataFrame(analysis)
df.head()

# %% [markdown]
# It is worth noting that the images we receive, as with the other data formats, generally follow a homogeneous structure and show very few anomalies. However, this is not always guaranteed, we may not always receive images that are perfectly consistent or clean.
# 
# For this reason, even though in this particular case we observe only minor differences between the original and the processed images, the cleaning and enhancement procedures are still applied. This step is essential to ensure that, regardless of the initial quality or format of the incoming images, all files undergo a standardized treatment process that maximizes their consistency, clarity, and overall visual quality.


