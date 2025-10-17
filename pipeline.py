# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/data-collection.ipynb
import os
from os import mkdir
# Get the path to the folder named ADSDB
BASE_DIR = os.getcwd().split("ADSDB")[0] + "ADSDB/"
OUTPUT_DIR = os.path.join(BASE_DIR, "output/")
datasets = 3

for i in range(1, datasets + 1):
    try:
        mkdir(OUTPUT_DIR + f"dataset{i}/")
    except FileExistsError:
        pass



# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/data-collection.ipynb
import os
from datasets import load_dataset
from PIL import Image

ds = load_dataset("abaryan/ham10000_bbox")
data = ds['train']
sample_data = data.shuffle(seed=42).select(range(100))

for item in sample_data:
    image: Image.Image = item['image']
    image_id: str = item['image_id']
    filename = f"{image_id}.jpg"
    save_path = os.path.join(OUTPUT_DIR+"/dataset1", filename)
    image.save(save_path)

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/data-collection.ipynb
import requests
from bs4 import BeautifulSoup

topics = ["skin_cancer", "melanoma", "basal_cell_carcinoma", "squamous_cell_carcinoma", "actinic_keratosis"]

def wikipedia_scrapper(topics):
    for topic in topics:
        url = 'https://en.wikipedia.org/wiki/' + topic
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        res = requests.get(url, headers={'User-Agent': user_agent})
        soup = BeautifulSoup(res.text, 'html.parser')

        data = ''
        for p in soup.find_all('p'):
            data += p.get_text()
            data += '\n'
        
        data = data.strip()

        for j in range(1, 750):
            data = data.replace('[' + str(j) + ']', '')


        fd = open(OUTPUT_DIR + "dataset2/" + topic + '.txt', 'w')
        fd.write(data)
        fd.close()

wikipedia_scrapper(topics)

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/data-collection.ipynb
import pandas as pd

df = pd.read_json("hf://datasets/Moaaz55/skin_cancer_questions_answers/dataset.json", lines=True)

df = df.sample(n=100, random_state=42)
df = df.apply(lambda row: f"A: {row['Answer']}\n", axis=1)

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/data-collection.ipynb
import wave
from piper import PiperVoice
import os

voice = PiperVoice.load(os.path.join(BASE_DIR, "en_US-lessac-medium.onnx"))

for i, text in enumerate(df):
    text = text.replace("A: ", "").strip()
    with wave.open(os.path.join(OUTPUT_DIR, f"dataset3/answer_{i}.wav"), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/temporal_zone.ipynb
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


# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/temporal_zone.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/persistent_zone.ipynb
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

new_bucket = "persistent-landing"
try:
    minio_client.create_bucket(Bucket=new_bucket)
except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
    print(f"Bucket '{new_bucket}' already exists")

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/landing_zone/persistent_zone.ipynb
import os
from tqdm import tqdm

landing_zone = "landing-zone"
persistent_landing = "persistent-landing"
paginator = minio_client.get_paginator("list_objects_v2")

file_extensions = set()

for page in paginator.paginate(Bucket=landing_zone):
    for obj in page.get("Contents", []):
        key = obj.get("Key", "")
        if "." in key:
            extension = os.path.splitext(key)[1].lower()
            if extension:
                file_extensions.add(extension)

print(f"File types discovered: {file_extensions}")

# Map file extensions to folder names
folder_map = {
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".png": "images",
    ".jpg": "images",
    ".jpeg": "images",
    ".csv": "tabular",
    ".parquet": "tabular",
    ".txt": "text",
    ".md": "text",
    ".json": "text",
}

for page in paginator.paginate(Bucket=landing_zone):
    for obj in page.get("Contents", []):
        key = obj.get("Key", "")

        file_ext = os.path.splitext(key)[1].lower()
        dest_folder = folder_map.get(file_ext, file_ext.strip("."))
        if not dest_folder:
            dest_folder = "others"
        
        new_key = f"{dest_folder}/{os.path.basename(key)}"
        copy_source = {
            'Bucket': landing_zone,
            'Key': key
        }
        
        minio_client.copy_object(
            CopySource=copy_source,
            Bucket=persistent_landing,
            Key=new_key
        )

print("Files have been organized in the persistent landing bucket.")
for page in paginator.paginate(Bucket=landing_zone):
    for obj in page.get("Contents", []):
        key = obj.get("Key", "")
        minio_client.delete_object(Bucket=landing_zone, Key=key)
print("Temporary landing files have been removed.")

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/formatted_zone/formated_zone_audio.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/formatted_zone/formated_zone_audio.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/formatted_zone/formated_zone_images.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/formatted_zone/formated_zone_images.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/formatted_zone/formated_zone_text.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/formatted_zone/formated_zone_text.ipynb
import botocore.exceptions
import io

bucket_origin = "persistent-landing"
bucket_destination = "formatted-zone"
path_prefix = "text/"

paginator = minio_client.get_paginator("list_objects_v2") # We use paginators because the list_objects method response is limitted to a maximum of 1,000 objects 

for page in paginator.paginate(Bucket=bucket_origin, Prefix=path_prefix):
    for obj in page["Contents"]:
        key = obj["Key"]
        split_filename = os.path.splitext(key.split("/")[1])
        filename = split_filename[0]
        format = split_filename[1].lower()
        
        try:
            response = minio_client.get_object(Bucket=bucket_origin, Key=key)

            # Text conversion to .txt. Here, the only transformation is the extension 
            text_data = response["Body"].read()
            buffer = io.BytesIO(text_data)

            # Upload text to formatted zone
            new_key = path_prefix + filename + ".txt"
            minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=new_key)
            minio_client.head_object(Bucket=bucket_destination, Key=new_key) # Checks if the file was uploaded successfully and throws an exception otherwise.
        except botocore.exceptions.ClientError as e:
            print(f"[ERROR]: An error occurred while moving {filename} between zones: {e}")
        except Exception as e:
            print(f"[ERROR]: An error occurred while manipulating {filename}: {e}")

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/trusted_zone/trusted_zone_audio.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/trusted_zone/trusted_zone_audio.ipynb
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import split_on_silence, detect_silence
import io
from tqdm import tqdm

bucket_origen = "formatted-zone"
bucket_desti = "trusted-zone"
prefix_origen = "audio/"
freq_final = 44100

paginator = minio_client.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket=bucket_origen, Prefix=prefix_origen):
    for obj in tqdm(page.get("Contents", []), desc="Processant àudios"):
        key = obj["Key"]
        filename = key.split("/")[-1]

        #Llegir àudio original
        response = minio_client.get_object(Bucket=bucket_origen, Key=key)
        audio_data = response["Body"].read()

        #Obrir amb pydub
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        except Exception as e:
            print(f"Error amb {filename}: {e}")
            continue

        # APLICAR TRATAMIENTOS DE LIMPIEZA Y MEJORA
        
        # 1. Normalizar frecuencia de muestreo
        audio = audio.set_frame_rate(freq_final)
        
        # 2. Limpiar silencios al inicio y final
        # Detectar y eliminar silencios largos al principio y final
        silence_threshold = -50  # dB
        silence_duration = 500   # ms
        
        # Detectar silencios
        silence_ranges = detect_silence(audio, min_silence_len=silence_duration, silence_thresh=silence_threshold)
        
        if silence_ranges:
            # Eliminar silencio del final
            if silence_ranges[-1][1] > len(audio) - 1000:  # Si el último silencio está cerca del final
                audio = audio[:silence_ranges[-1][0]]
            
            # Eliminar silencio del inicio
            if silence_ranges[0][0] < 1000:  # Si el primer silencio está cerca del inicio
                audio = audio[silence_ranges[0][1]:]
        
        # 3. Normalizar volumen (uniformar niveles)
        audio = normalize(audio)
        
        # 4. Compresión dinámica para equilibrar niveles
        audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        
        # 5. Filtro de ruido (reducir ruido de fondo)
        # Aplicar un filtro pasa-altos muy suave para eliminar ruido de baja frecuencia
        audio = audio.high_pass_filter(80)  # Hz
        
        # 6. Filtro de ruido (reducir ruido de alta frecuencia)
        # Aplicar un filtro pasa-bajos para eliminar ruido de alta frecuencia
        audio = audio.low_pass_filter(16000)  # Hz
        
        # 7. Normalización final del volumen
        audio = normalize(audio)
        
        # 8. Ajustar ganancia final (opcional: +2dB para más presencia)
        audio = audio + 2

        # Desa com MP3 i puja al bucket formatted-zone
        buffer = io.BytesIO()
        audio.export(buffer, format="mp3", bitrate="192k")
        buffer.seek(0)

        new_key = f"audio/{filename}"
        minio_client.put_object(
            Bucket=bucket_desti,
            Key=new_key,
            Body=buffer
        )

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/trusted_zone/trusted_zone_images.ipynb
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

# From notebook: /home/oriol/Documentos/MDS/ADSDB/notebooks/trusted_zone/trusted_zone_images.ipynb
from PIL import Image, ImageEnhance, ImageFilter
import io
from tqdm import tqdm

bucket_origen = "persistent-landing"
bucket_desti = "formatted-zone"
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

