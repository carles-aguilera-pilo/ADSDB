import os
from dotenv import load_dotenv
from src.llm.GeminiModel import GeminiModel
from src.frontend.helpers.transformObjects import (
    display_chat_message, 
    getTextFromText, 
    getImageFromText, 
    getImageFromImage, 
    getTextFromImage, 
    getTextFromAudio
)

import streamlit as st
from audiorecorder import audiorecorder
import io
from PIL import Image

st.set_page_config(
    page_title="Rag Chatbot",
    layout="wide"
)

st.title("Rag Chatbot")
st.caption("Our rag implementation of the project. You can send text, an image, or both!")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

def rag(user_text, user_image):
    if not user_text:
        user_text = "Describe this image"

    retrieved_texts = getTextFromText(user_text, k = 1)
    retrieved_images = [getImageFromText(user_text, k = 1)]

    images_prompt = ""
    retrieved_images_paths = []

    if user_image:
        retrieved_texts += getTextFromImage(user_image)
        images_prompt = f"The user also provided an image, which corresponds to the last of the following sequence" 
        retrieved_images += [getImageFromImage(user_image)]
        retrieved_images.append(Image.open(io.BytesIO(user_image)))
        
    for i, image in enumerate(retrieved_images):
        if isinstance(image, Image.Image):
            path = f"/tmp/image_{i}.png"
            image.save(path)
            retrieved_images_paths.append(path)
        
    final_prompt = f"You are a medical expert on skin cancers. A user asked the following question: {user_text}.{images_prompt}. Here is some useful information about it:{retrieved_texts}" 
    print(final_prompt)
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    gm = GeminiModel(api_key, "gemini-2.5-flash")
    return gm.query(final_prompt, retrieved_images_paths)

for msg in st.session_state.messages:
    display_chat_message(msg)

st.header("Speak to Chat")
st.info("Click to record, stop to send. Your audio will be transcribed and used as a prompt.")

audio_segment = audiorecorder(
    show_visualizer=True,
    key="audiorecorder"
)

buffer = io.BytesIO()
if audio_segment.duration_seconds > 0:
    audio_segment.export(buffer, format="wav")

if (
    isinstance(buffer.getvalue(), bytes)
    and len(buffer.getvalue()) > 100
    and buffer.getvalue() != st.session_state.last_processed_audio
):
    st.session_state.last_processed_audio = buffer.getvalue()
    audio_bytes = buffer.getvalue()
    st.session_state.messages.append({
        "role": "user", 
        "audio": audio_bytes
    })
    with st.spinner("Transcribing audio and thinking..."):
        transcribed_text = getTextFromAudio(audio_bytes)
        st.session_state.messages.append({
            "role": "user", 
            "content": f"*(Audio transcribed: {transcribed_text})*"
        })
        response = rag(user_text=transcribed_text, user_image="")
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

st.header("Type and/or Upload")

with st.form(key="main_chat_form", clear_on_submit=True):
    prompt = st.text_input("What's on your mind?", key="text_prompt")
    uploaded_image = st.file_uploader(
        "Upload an image (optional)", 
        type=["png", "jpg", "jpeg"]
    )
    submitted = st.form_submit_button("Send")

if submitted:
    if not prompt and not uploaded_image:
        st.warning("Please enter a prompt or upload an image.")
    else:
        user_image_bytes = None
        user_message = {"role": "user"}
        
        if prompt:
            user_message["content"] = prompt
            
        if uploaded_image:
            user_image_bytes = uploaded_image.read()
            user_message["image"] = user_image_bytes
        st.session_state.messages.append(user_message)
        
        with st.spinner("Thinking..."):
            response = rag(user_text=prompt, user_image=user_image_bytes)
            
            try:
                useful_content = "".join(part.text for part in response.candidates[0].content.parts)
            except (AttributeError, IndexError, TypeError):
                useful_content = "Error: Could not parse the response."

            st.session_state.messages.append({"role": "assistant", "content": useful_content})
            st.rerun()