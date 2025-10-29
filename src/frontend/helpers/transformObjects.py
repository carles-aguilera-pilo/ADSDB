import streamlit as st
from src.chroma_connection import ChromaConnection
from src.minio_connection import MinIOConnection
from src.dataobj.TextObj import TextObj
from src.dataobj.ImageObj import ImageObj
from src.dataobj.AudioObj import AudioObj
import io
from PIL import Image

def display_chat_message(msg):
    with st.chat_message(msg["role"]):
        if "content" in msg:
            st.write(msg["content"])
        if "image" in msg:
            img_data = msg["image"]
            if isinstance(img_data, bytes):
                st.image(io.BytesIO(img_data), width=300)
            else:
                st.image(img_data, width=300)
        if "audio" in msg:
            st.audio(msg["audio"])

def getTextFromText(prompt, k=10):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=k)
    docs = response.get("documents")
    result = ""
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        num_docs = min(k, len(docs[0]))
        result = " ".join(docs[0][i] for i in range(num_docs) if docs[0][i] is not None)
    return result if docs else "I'm sorry, I don't have a text answer for that."

def getImageFromText(prompt, k=10):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=k)
    keys = response.get("ids")[0]
    print(keys)
    images = []
    for i in range(len(keys)):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        matched_image_data = obj["Body"].read()
        images.append(Image.open(io.BytesIO(matched_image_data)).convert('RGB'))
    return images

def getAudioFromText(prompt, k=10):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find matching audio."
    keys = response["ids"][0]
    audios = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        audios.append(obj["Body"].read())
    return audios

def getTextFromImage(image_bytes, k=10):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=k)
    print(response)
    docs = response.get("documents")
    print(docs)
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        num_docs = min(k, len(docs[0]))
        result = " ".join(docs[0][i] for i in range(num_docs) if docs[0][i] is not None)
        return result
    return "I'm sorry, I don't have a description for that image."

def getImageFromImage(image_bytes, k=10):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find a similar image."
    keys = response["ids"][0]
    images = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        matched_image_data = obj["Body"].read()
        images.append(Image.open(io.BytesIO(matched_image_data)).convert('RGB'))
    return images

def getAudioFromImage(image_bytes, k=10):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find matching audio for that image."
    keys = response["ids"][0]
    audios = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        audios.append(obj["Body"].read())
    return audios

def getTextFromAudio(audio_bytes, k=10):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=k)
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        num_docs = min(k, len(docs[0]))
        result = " ".join(docs[0][i] for i in range(num_docs) if docs[0][i] is not None)
        return result
    return "I'm sorry, I don't have a description for that audio."

def getImageFromAudio(audio_bytes, k=10):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find a matching image for that audio."
    keys = response["ids"][0]
    images = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        matched_image_data = obj["Body"].read()
        images.append(Image.open(io.BytesIO(matched_image_data)).convert('RGB'))
    return images

def getAudioFromAudio(audio_bytes, k=10):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find similar audio."
    keys = response["ids"][0]
    audios = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        audios.append(obj["Body"].read())
    return audios
