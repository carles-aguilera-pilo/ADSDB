import streamlit as st
from audiorecorder import audiorecorder
import io

# --- Page Config ---
st.set_page_config(
    page_title="Same Modality Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("Same Modality Chatbot")
st.caption("This is the page for same modality interactions.")

# --- Session State Initialization ---
if "text_messages" not in st.session_state:
    st.session_state.text_messages = []
if "image_messages" not in st.session_state:
    st.session_state.image_messages = []
if "audio_messages" not in st.session_state:
    st.session_state.audio_messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# --- Mock Response Function (FIXED) ---
def get_mock_response(prompt, mode, data=None):
    if mode == "text":
        return f"🤖 Echo: {prompt}"
    elif mode == "image":
        # FIXED: Handle cases where no text prompt is provided
        if prompt:
            return f"🤖 I see an image! You asked: '{prompt}'"
        else:
            return "🤖 I see an image!"
    elif mode == "audio":
        if prompt:
            return f"🤖 I received your audio. Your prompt was: '{prompt}'. (Mock transcription: '...hello world...')"
        else:
            return "🤖 I received your audio and am processing it. (Mock transcription: '...hello world...')"

tab1, tab2, tab3 = st.tabs(["💬 Text Mode", "🖼️ Image Mode", "🎤 Audio Mode"])

with tab1:
    st.header("Chat with Text")
    
    for msg in st.session_state.text_messages:
        st.chat_message(msg["role"]).write(msg["content"])

    with st.form(key="text_form", clear_on_submit=True):
        prompt = st.text_input("What's on your mind?", key="text_prompt")
        submitted = st.form_submit_button("Send")

    if submitted and prompt:
        st.session_state.text_messages.append({"role": "user", "content": prompt})
        
        response = get_mock_response(prompt, "text")
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
        uploaded_image = st.file_uploader("Upload an image (no prompt needed)", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Send")

    if submitted and uploaded_image is not None:
        image_bytes = uploaded_image.read()
        
        st.session_state.image_messages.append({
            "role": "user",
            "image": image_bytes
        })
        
        response = get_mock_response(prompt=None, mode="image", data=image_bytes)
        st.session_state.image_messages.append({"role": "assistant", "content": response})
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

        response = get_mock_response(prompt=None, mode="audio", data=buffer.getvalue())

        st.session_state.audio_messages.append({
            "role": "assistant", 
            "content": response
        })
        
        st.rerun()
        