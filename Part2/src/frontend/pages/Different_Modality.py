from src.frontend.helpers.transformObjects import display_chat_message, getTextFromText, getImageFromText, getAudioFromText, getImageFromImage, getTextFromImage, getAudioFromImage, getAudioFromAudio, getTextFromAudio, getImageFromAudio
import streamlit as st
from audiorecorder import audiorecorder
import io

st.set_page_config(
    page_title="Multi-Modal Chatbot",
    layout="wide"
)

st.title("Multi-Modal Chatbot")
st.caption("Interact across different modalities: Text, Image, and Audio.")

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

tab1, tab2, tab3 = st.tabs(["Text Input", "Image Input", "Audio Input"])

with tab1:
    st.header("Chat with Text")
    for msg in st.session_state.text_messages:
        display_chat_message(msg)

    output_mode_text = st.radio(
        "What do you want to get back?",
        ("Text", "Image", "Audio"),
        key="text_output_mode",
        horizontal=True
    )

    with st.form(key="text_form", clear_on_submit=True):
        prompt = st.text_input("What's on your mind?", key="rag_text_prompt")
        submitted = st.form_submit_button("Send")

    if submitted and prompt:
        st.session_state.text_messages.append({"role": "user", "content": prompt})

        if output_mode_text == "Text":
            response = getTextFromText(prompt, k=k_text)
            st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_text == "Image":
            response = getImageFromText(prompt, k=k_image)
            if isinstance(response, list):
                for img in response:
                    st.session_state.text_messages.append({"role": "assistant", "image": img})
            else:
                st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_text == "Audio":
            response = getAudioFromText(prompt, k=k_audio)
            if isinstance(response, list):
                for audio_data in response:
                    st.session_state.text_messages.append({"role": "assistant", "audio": audio_data})
            else:
                st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        st.rerun()

with tab2:
    st.header("Chat with Images")
    for msg in st.session_state.image_messages:
        display_chat_message(msg)
    output_mode_image = st.radio(
        "What do you want to get back?",
        ("Image", "Text", "Audio"),
        key="image_output_mode",
        horizontal=True
    )

    with st.form(key="image_form", clear_on_submit=True):
        uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Send")

    if submitted and uploaded_image is not None:
        image_bytes = uploaded_image.read()
        st.session_state.image_messages.append({
            "role": "user",
            "image": image_bytes
        })
        if output_mode_image == "Image":
            response = getImageFromImage(image_bytes, k=k_image)
            if isinstance(response, list):
                for img in response:
                    st.session_state.image_messages.append({"role": "assistant", "image": img})
            else:
                st.session_state.image_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_image == "Text":
            response = getTextFromImage(image_bytes, k=k_text)
            st.session_state.image_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_image == "Audio":
            response = getAudioFromImage(image_bytes, k=k_audio)
            if isinstance(response, list):
                for audio_data in response:
                    st.session_state.image_messages.append({"role": "assistant", "audio": audio_data})
            else:
                st.session_state.image_messages.append({"role": "assistant", "content": response})
        
        st.rerun()

with tab3:
    st.header("Chat with Audio")
    st.info("Select your desired output, then click to record. Stop to send. (Check browser permissions 🔒)")
    for msg in st.session_state.audio_messages:
        display_chat_message(msg)
    output_mode_audio = st.radio(
        "What do you want to get back?",
        ("Audio", "Text", "Image"),
        key="audio_output_mode",
        horizontal=True
    )

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
        st.session_state.audio_messages.append({
            "role": "user", 
            "audio": buffer.getvalue()
        })
        if output_mode_audio == "Audio":
            response = getAudioFromAudio(buffer.getvalue(), k=k_audio)
            if isinstance(response, list):
                for audio_data in response:
                    st.session_state.audio_messages.append({"role": "assistant", "audio": audio_data})
            else:
                st.session_state.audio_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_audio == "Text":
            response = getTextFromAudio(buffer.getvalue(), k=k_text)
            st.session_state.audio_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_audio == "Image":
            response = getImageFromAudio(buffer.getvalue(), k=k_image)
            if isinstance(response, list):
                for img in response:
                    st.session_state.audio_messages.append({"role": "assistant", "image": img})
            else:
                st.session_state.audio_messages.append({"role": "assistant", "content": response})
        
        st.rerun()