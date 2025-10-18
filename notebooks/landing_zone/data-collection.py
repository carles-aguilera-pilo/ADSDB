
import os
from os import mkdir
from datasets import load_dataset
from PIL import Image
import requests
from bs4 import BeautifulSoup
import pandas as pd
import wave
from piper import PiperVoice


class DataCollection(StrategyLandingZone)
    
    def executar(self):
        # Get the path to the folder named ADSDB
        BASE_DIR = os.getcwd().split("ADSDB")[0] + "ADSDB/"
        OUTPUT_DIR = os.path.join(BASE_DIR, "output/")
        datasets = 3
        for i in range(1, datasets + 1):
            try:
                #TODO output dir not good.
                mkdir(OUTPUT_DIR)
                mkdir(OUTPUT_DIR + f"dataset{i}/")
            except FileExistsError:
                pass
        ds = load_dataset("abaryan/ham10000_bbox")
        data = ds['train']
        sample_data = data.shuffle(seed=42).select(range(100))

        for item in sample_data:
            image: Image.Image = item['image']
            image_id: str = item['image_id']
            filename = f"{image_id}.jpg"
            save_path = os.path.join(OUTPUT_DIR+"/dataset1", filename)
            image.save(save_path)
        topics = ["skin_cancer", "melanoma", "basal_cell_carcinoma", "squamous_cell_carcinoma", "actinic_keratosis"]
        wikipedia_scrapper(topics)
        df = pd.read_json("hf://datasets/Moaaz55/skin_cancer_questions_answers/dataset.json", lines=True)
        df = df.sample(n=100, random_state=42)
        df = df.apply(lambda row: f"A: {row['Answer']}\n", axis=1)
        voice = PiperVoice.load(os.path.join(BASE_DIR, "en_US-lessac-medium.onnx"))
        for i, text in enumerate(df):
            text = text.replace("A: ", "").strip()
            with wave.open(os.path.join(OUTPUT_DIR, f"dataset3/answer_{i}.wav"), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
                

    def wikipedia_scrapper(self,topics):
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