# %% [markdown]
# # Obtaining the data from datasources
# 
# This project focuses on the design and execution of a data processing pipeline that transforms raw data from multiple sources into a structued format suitable for machine learning applications.
# 
# In a real scenario, such data sources would come from different repositories or systems, for example, different databases or APIs, each containing only a subset of the required information. However, these idealized and openly accessible data sources do not always exist in practice, especially when the project involves combining multiple types of information. To overcome this limitation and for academic purposes, we have created our own data sources by extracting, restructuring, and combining data from existing public datasets.
# 
# This notebook therefore begins by introducing the different simulated data sources we created, explaining their purpose and structure. After that, in the [temporal landing zone](./temporal_zone.ipynb) we demonstrate how the pipeline ingests theses sources, and futher applies transformations to produce a final dataset ready for use in ML models.
# 
# The different datasources we used or created are the following:
# 1. [huggingface dataset](https://huggingface.co/datasets/Moaaz55/skin_cancer_questions_answers). This dataset is used for ...
# 2. Self made audio dataset. This dataset is used for ...
# 3. Wikipedia web scrapping information. This dataset is used for...
# 
# In the next sections, we will discuss how the data is obtained to further insert them into the first zone of the pipeline.

# %%
import os
from os import mkdir
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



# %% [markdown]
# ## HAM10000
# 
# The primary image dataset for our project is the **HAM10000** (Human Against Machine with 10,000 Training images) dataset, which we acquired directly from the **Hugging Face Hub**. This is a large, publicly available collection of dermatoscopic images specifically for the dermatological research. It contains thousands of images representing common pigmented skin lesions, including various types of moles and skin cancers. Each image is associated with a specific diagnostic category, making it a very good resource for tasks related to image classification of skin conditions.
# 
# 

# %%
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

# %% [markdown]
# ## Wikipedia web scrapping
# 
# For the textual resource, we generated a corpus by performing **web scrapping** of Wikipedia. We targeted a specific set of articles centered on the topic of skin cancer, including pages detailing its various forms, risk factors, prevention methods... This process involved extracting the full text from these pages. We achieved this by obtaining the HTML and then, we saw that the data is contained in all the <p> HTML tags. Therefore, we iterated each of this components and we extracted all the rellevant information and saved into a file to introduce the dataset into the pipeline in the next process. The result is a cusotm-made text dataset centered on skin cancer information, designed for different type of data science applications.

# %%
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

# %% [markdown]
# ## Self made audio dataset
# For our third datset, we created a set of spoken answers. We started by getting a datset of skin cancer Q&A in text format from the **Hugging Face Hub**. Our goal was to turn the written answers into audio files. To do this, we used a Text-to-Speech (TTS) tool called Piper. We fed a sample of 100 text answers from the dataset into Piper, and it generated a spoken audio clip for each one. The final result is a collection of .wav files containing all the answers.

# %%
import pandas as pd

df = pd.read_json("hf://datasets/Moaaz55/skin_cancer_questions_answers/dataset.json", lines=True)

df = df.sample(n=100, random_state=42)
df = df.apply(lambda row: f"A: {row['Answer']}\n", axis=1)

# %% [markdown]
# ## Model instal·lation
# 
# To install the model, you must execute this command:
# ```sh
# python3 -m piper.download_voices en_US-lessac-medium
# ```
# 

# %%
import wave
from piper import PiperVoice
import os

voice = PiperVoice.load(os.path.join(BASE_DIR, "en_US-lessac-medium.onnx"))

for i, text in enumerate(df):
    text = text.replace("A: ", "").strip()
    with wave.open(os.path.join(OUTPUT_DIR, f"dataset3/answer_{i}.wav"), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)


