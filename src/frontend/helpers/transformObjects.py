import streamlit as st
from src.chroma_connection import ChromaConnection
from src.minio_connection import MinIOConnection
from src.dataobj.TextObj import TextObj
from src.dataobj.ImageObj import ImageObj
from src.dataobj.AudioObj import AudioObj
import io
from PIL import Image

def display_chat_message(msg):
    """Generic function to display a message, handling any data type."""
    with st.chat_message(msg["role"]):
        if "content" in msg:  # Text content
            st.write(msg["content"])
        if "image" in msg:  # Image content
            # Handle both PIL Image objects and raw bytes
            img_data = msg["image"]
            if isinstance(img_data, bytes):
                st.image(io.BytesIO(img_data), width=300)
            else:
                st.image(img_data, width=300)
        if "audio" in msg:  # Audio content
            st.audio(msg["audio"])

# --- Response Functions (9 Combinations) ---

# 1. Text -> Text
def getTextFromText(prompt):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=1)
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        return docs[0][0]
    return "I'm sorry, I don't have a text answer for that."

# 2. Text -> Image
def getImageFromText(prompt):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=1) # Query IMAGE collection
    if not response["ids"][0]:
        return "Sorry, I couldn't find a matching image."
    key = response["ids"][0][0]
    obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=key)
    matched_image_data = obj["Body"].read()
    return Image.open(io.BytesIO(matched_image_data)).convert('RGB')

# 3. Text -> Audio
def getAudioFromText(prompt):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=1) # Query AUDIO collection
    if not response["ids"][0]:
        return "Sorry, I couldn't find matching audio."
    key = response["ids"][0][0]
    obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=key)
    return obj["Body"].read()

# 4. Image -> Text
def getTextFromImage(image_bytes):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=1) # Query TEXT collection
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        return docs[0][0]
    return "I'm sorry, I don't have a description for that image."

# 5. Image -> Image
def getImageFromImage(image_bytes):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=1)
    if not response["ids"][0]:
        return "Sorry, I couldn't find a similar image."
    key = response["ids"][0][0]
    obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=key)
    matched_image_data = obj["Body"].read()
    return Image.open(io.BytesIO(matched_image_data)).convert('RGB')

# 6. Image -> Audio
def getAudioFromImage(image_bytes):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=1) # Query AUDIO collection
    if not response["ids"][0]:
        return "Sorry, I couldn't find matching audio for that image."
    key = response["ids"][0][0]
    obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=key)
    return obj["Body"].read()

# 7. Audio -> Text
def getTextFromAudio(audio_bytes):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=1) # Query TEXT collection
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        return docs[0][0]
    return "I'm sorry, I don't have a description for that audio."

# 8. Audio -> Image
def getImageFromAudio(audio_bytes):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=1) # Query IMAGE collection
    if not response["ids"][0]:
        return "Sorry, I couldn't find a matching image for that audio."
    key = response["ids"][0][0]
    obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=key)
    matched_image_data = obj["Body"].read()
    return Image.open(io.BytesIO(matched_image_data)).convert('RGB')

# 9. Audio -> Audio
def getAudioFromAudio(audio_bytes):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.save("exploitation-zone")
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=1)
    if not response["ids"][0]:
        return "Sorry, I couldn't find similar audio."
    key = response["ids"][0][0]
    obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=key)
    return obj["Body"].read()

