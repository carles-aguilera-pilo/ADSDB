from bs4 import BeautifulSoup
from datasets import load_dataset
import os
from PIL import Image
import requests
from src.minio_connection import MinIOConnection
import pandas as pd
import wave
from piper import PiperVoice


class DataCollection():
    BASE_DIR = os.getcwd().split("ADSDB")[0] + "ADSDB/"
    OUTPUT_DIR = os.path.join(BASE_DIR, "output/")

    @classmethod
    def wikipedia_scrapper(cls, topics):
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


            fd = open(cls.OUTPUT_DIR + "texts/" + topic + '.txt', 'w')
            fd.write(data)
            fd.close()

    @classmethod
    def collect_data(cls):
        cls.collect_images()
        cls.collect_texts()
        cls.collect_audios()

    @classmethod
    def collect_audios(cls):
        try:
            os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
            os.makedirs(cls.OUTPUT_DIR + f"audios", exist_ok=True)
        except FileExistsError:
            pass

        df = pd.read_json("hf://datasets/Moaaz55/skin_cancer_questions_answers/dataset.json", lines=True)
        df = df.sample(n=100, random_state=42)
        df = df.apply(lambda row: f"A: {row['Answer']}\n", axis=1)

        voice = PiperVoice.load(os.path.join(cls.BASE_DIR, "en_US-lessac-medium.onnx"))

        for i, text in enumerate(df):
            text = text.replace("A: ", "").strip()
            with wave.open(os.path.join(cls.OUTPUT_DIR, f"audios/answer_{i}.wav"), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)

    @classmethod
    def collect_images(cls): 
        try:
            os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
            os.makedirs(cls.OUTPUT_DIR + f"images", exist_ok=True)
        except FileExistsError:
            pass

        ds = load_dataset("abaryan/ham10000_bbox")
        data = ds['train']
        sample_data = data.shuffle(seed=42).select(range(100))

        for item in sample_data:
            image: Image.Image = item['image']
            image_id: str = item['image_id']
            filename = f"{image_id}.jpg"
            save_path = os.path.join(cls.OUTPUT_DIR+"/images", filename)
            image.save(save_path)

    @classmethod
    def collect_texts(cls): 
        try:
            os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
            os.makedirs(cls.OUTPUT_DIR + f"texts", exist_ok=True)
        except FileExistsError:
            pass

        topics = ["skin_cancer", "melanoma", "basal_cell_carcinoma", "squamous_cell_carcinoma", "actinic_keratosis"]
        cls.wikipedia_scrapper(topics)

    @classmethod
    def upload_data(cls, bucket_destination):
        minio_client = MinIOConnection()
        try:
            minio_client.create_bucket(Bucket=bucket_destination)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{bucket_destination}' already exists")

        for dataset in os.listdir(cls.OUTPUT_DIR):
            for root, _, files in os.walk(cls.OUTPUT_DIR + dataset):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        minio_client.upload_file(file_path, bucket_destination, file)
                    except Exception as e:
                        print(f"Failed to upload {file}: {e}")
            

