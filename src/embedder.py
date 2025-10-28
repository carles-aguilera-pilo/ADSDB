import torch
from imagebind.models.imagebind_model import imagebind_huge, ModalityType
from imagebind import data
from src.minio_connection import MinIOConnection
import os

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = imagebind_huge(pretrained=True)
model.eval()
model.to(device)

def embed_image(minio_key):
    try:
        response = MinIOConnection().get_object(Bucket="exploitation-zone", Key=minio_key)
        image_data = response["Body"].read()
        with open("/tmp/temp_image_file", "wb") as f:
            f.write(image_data)

        inputs = {
            ModalityType.VISION: data.load_and_transform_vision_data(["/tmp/temp_image_file"], device)
        }
        with torch.no_grad():
            embeddings = model(inputs)

        image_vector = embeddings[ModalityType.VISION].squeeze(0)
        print(f"image_vector: {type(image_vector)} {image_vector.shape} {image_vector}")
        os.remove("/tmp/temp_image_file")
        return image_vector
    except Exception as e:
        print(f"Error processing image bytes: {e}")
        return None

def embed_text(text):
    try:
        print(f"Embedding text: {text}")
        inputs = {
            ModalityType.TEXT: data.load_and_transform_text([text], device),
        }
        print(f"inputs: {inputs}")

        with torch.no_grad():
            embeddings = model(inputs)

        print(f"embeddings: {embeddings}")

        text_vector = embeddings[ModalityType.TEXT]
        print(f"text_vector: {type(text_vector)} {text_vector.shape} {text_vector}")
        return text_vector
    except Exception as e:
        print(f"Error processing text: {e}")
        return None


def embed_audio(minio_key):
    print(minio_key)
    try:
        response = MinIOConnection().get_object(Bucket="exploitation-zone", Key=minio_key)
        audio_data = response["Body"].read()
        print(audio_data)
        with open("/tmp/temp_audio_file", "wb") as f:
            f.write(audio_data)

        inputs = {
            ModalityType.AUDIO: data.load_and_transform_audio_data(["/tmp/temp_audio_file"], device),
        }

        with torch.no_grad():
            embeddings = model(inputs)
        
        audio_vector = embeddings[ModalityType.AUDIO].squeeze(0)
        print(f"audio_vector: {type(audio_vector)} {audio_vector.shape} {audio_vector}")
        os.remove("/tmp/temp_audio_file")
        return audio_vector
    except Exception as e:
        print(f"Error processing audio bytes: {e}")
        return None