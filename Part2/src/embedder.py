import torch
from imagebind.models.imagebind_model import imagebind_huge, ModalityType
from imagebind import data
from pydub import AudioSegment
import os
from PIL import Image

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = imagebind_huge(pretrained=True)
model.eval()
model.to(device)

def embed_image(image: Image):
    try:
        image.save("/tmp/temp_image_file", format='PNG')

        inputs = {
            ModalityType.VISION: data.load_and_transform_vision_data(["/tmp/temp_image_file"], device)
        }
        with torch.no_grad():
            embeddings = model(inputs)

        image_vector = embeddings[ModalityType.VISION].squeeze(0)
        os.remove("/tmp/temp_image_file")
        return image_vector
    except Exception as e:
        print(f"Error processing image bytes: {e}")
        return None

def embed_text(text):
    try:
        inputs = {
            ModalityType.TEXT: data.load_and_transform_text([text], device),
        }

        with torch.no_grad():
            embeddings = model(inputs)

        text_vector = embeddings[ModalityType.TEXT]
        return text_vector
    except Exception as e:
        print(f"Error processing text: {e}")
        return None


def embed_audio(audio: AudioSegment):
    try:
        audio.export("/tmp/temp_audio_file", format="wav")

        inputs = {
            ModalityType.AUDIO: data.load_and_transform_audio_data(["/tmp/temp_audio_file"], device),
        }

        with torch.no_grad():
            embeddings = model(inputs)
        
        audio_vector = embeddings[ModalityType.AUDIO].squeeze(0)
        os.remove("/tmp/temp_audio_file")
        return audio_vector
    except Exception as e:
        print(f"Error processing audio bytes: {e}")
        return None