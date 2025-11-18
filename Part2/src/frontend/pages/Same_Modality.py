import streamlit as st
from audiorecorder import audiorecorder
import io
from src.frontend.helpers.transformObjects import (
    getTextFromText,
    getImageFromImage,
    getAudioFromAudio
)

st.set_page_config(
    page_title="Same Modality Chatbot",
    layout="wide"
)

st.title("Same Modality Chatbot")
st.caption("This is the page for same modality interactions.")

with st.sidebar:
    st.header("Configuración")
    k_text = st.number_input("K para Texto", min_value=1, max_value=50, value=10, help="Número de respuestas para texto")
    k_image = st.number_input("K para Imágenes", min_value=1, max_value=20, value=1, help="Número de respuestas para imágenes")
    k_audio = st.number_input("K para Audio", min_value=1, max_value=20, value=1, help="Número de respuestas para audio")

if "text_messages" not in st.session_state:
    st.session_state.text_messages = []
if "image_messages" not in st.session_state:
    st.session_state.image_messages = []
if "audio_messages" not in st.session_state:
    st.session_state.audio_messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None


tab1, tab2, tab3 = st.tabs(["Text", "Image", "Audio"])

with tab1:
    st.header("Chat with Text")
    
    for msg in st.session_state.text_messages:
        st.chat_message(msg["role"]).write(msg["content"])

    with st.form(key="text_form", clear_on_submit=True):
        prompt = st.text_input("Type something...", key="text_prompt")
        submitted = st.form_submit_button("Send")

    if submitted and prompt:
        st.session_state.text_messages.append({"role": "user", "content": prompt})

        response = getTextFromText(prompt, k=k_text)
        st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        st.rerun()

with tab2:
    st.header("Chat with Images")

    for msg in st.session_state.image_messages:
        with st.chat_message(msg["role"]):
            if "content" in msg and msg["content"] is not None:
                st.write(msg["content"])
            if "image" in msg:
                st.image(msg["image"], width=300)

    with st.form(key="image_form", clear_on_submit=True):
        uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Send")

    if submitted and uploaded_image is not None:
        image_bytes = uploaded_image.read()
        
        st.session_state.image_messages.append({
            "role": "user",
            "image": image_bytes
        })

        response = getImageFromImage(image_bytes, k=k_image)
        for img in response:
            st.session_state.image_messages.append({"role": "assistant", "image": img})
        st.rerun()

with tab3:
    st.header("Chat with Audio")
    st.info("Click the recorder. When you stop, your audio will be sent automatically. (Check browser permissions 🔒)")

    for msg in st.session_state.audio_messages:
        with st.chat_message(msg["role"]):
            if "content" in msg and msg["content"] is not None:
                st.write(msg["content"])
            if "audio" in msg:
                st.audio(msg["audio"])

    audio_segment = audiorecorder(
        show_visualizer=True,
        key="audiorecorder"
    )

    buffer = io.BytesIO()
    audio_segment.export(buffer, format="wav")

    if (
        isinstance(buffer.getvalue(), bytes)
        and len(buffer.getvalue()) > 100
        and buffer.getvalue() != st.session_state.last_processed_audio
    ):
        st.session_state.last_processed_audio = buffer.getvalue()
        
        st.session_state.audio_messages.append({
            "role": "user", 
            "audio": buffer.getvalue()
        })

        response = getAudioFromAudio(buffer.getvalue(), k=k_audio)

        for audio_data in response:
            st.session_state.audio_messages.append({
                "role": "assistant", 
                "audio": audio_data
            })
        
        st.rerun()
        