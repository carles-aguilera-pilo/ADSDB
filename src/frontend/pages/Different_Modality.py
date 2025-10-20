import streamlit as st
from audiorecorder import audiorecorder
import time
import urllib.parse
import io
import wave
import struct

# --- Page Config ---
st.set_page_config(
    page_title="Multimodal Generative Studio",
    page_icon="🎨",
    layout="wide"
)

st.title("Multimodal Generative Studio")
st.caption("Generate content by converting between text, images, and audio.")

# --- Mock Generation Functions ---

def mock_text_to_image(prompt: str) -> str:
    """Generates a placeholder image URL based on the prompt."""
    time.sleep(2) # Simulate API call delay
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://placehold.co/512x512/2E2B22/FFFFFF?text=Generated+Image\\n---\\n{encoded_prompt}"
    return image_url

def mock_image_to_audio(image_bytes: bytes) -> bytes:
    """Generates a simple, mock 'sonification' WAV file in memory."""
    time.sleep(2)
    audio_buffer = io.BytesIO()
    
    # WAV parameters
    sample_rate = 22050
    duration_seconds = 3
    n_samples = int(sample_rate * duration_seconds)
    
    with wave.open(audio_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(sample_rate)
        
        # Generate a sound based on the size of the image
        image_size_kb = len(image_bytes) / 1024
        base_freq = 220 + (image_size_kb % 200) # Frequency changes with image size
        
        for i in range(n_samples):
            # A simple decaying sine wave
            t = float(i) / sample_rate
            value = int(32767.0 * 0.5 * (1 - t/duration_seconds) * pow(2, -t*3) * struct.unpack('h', struct.pack('h', int(base_freq * t * 2 * 3.14159)))[0])
            data = struct.pack('<h', value)
            wf.writeframesraw(data)
            
    return audio_buffer.getvalue()

def mock_audio_to_text(audio_bytes: bytes) -> str:
    """Generates a mock transcription of the audio."""
    time.sleep(2)
    audio_length_kb = len(audio_bytes) // 1024
    return f"Mock transcription complete! Received {audio_length_kb} KB of audio data. The transcribed text would appear here."

# --- UI Tabs ---
tab1, tab2, tab3 = st.tabs(["📝 Text-to-Image", "🖼️ Image-to-Audio", "🎤 Audio-to-Text"])

# ==============================================================================
# --- Tab 1: Text-to-Image ---
# ==============================================================================
with tab1:
    st.header("Generate an Image from a Text Prompt")
    with st.form("text_to_image_form", clear_on_submit=True):
        text_prompt = st.text_area("Enter your image prompt:", "A sunlit library with towering bookshelves, dust motes dancing in the air.")
        submitted = st.form_submit_button("Generate Image")

    if submitted and text_prompt:
        with st.spinner("Generating your image... please wait."):
            generated_image_url = mock_text_to_image(text_prompt)
        
        st.success("✨ Image Generated!")
        st.image(generated_image_url, caption=f"Prompt: {text_prompt}", use_column_width=True)

# ==============================================================================
# --- Tab 2: Image-to-Audio ---
# ==============================================================================
with tab2:
    st.header("Generate Audio from an Image")
    with st.form("image_to_audio_form", clear_on_submit=True):
        uploaded_image = st.file_uploader("Upload an image to create a soundscape for it", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Generate Audio")

    if submitted and uploaded_image is not None:
        image_bytes = uploaded_image.read()
        st.image(image_bytes, caption="Image being processed...", width=300)
        with st.spinner("Analyzing image and synthesizing audio..."):
            generated_audio_bytes = mock_image_to_audio(image_bytes)
        
        st.success("🎧 Audio Generated!")
        st.audio(generated_audio_bytes)

# ==============================================================================
# --- Tab 3: Audio-to-Text ---
# ==============================================================================
with tab3:
    st.header("Transcribe Audio to Text")
    st.info("Record a short message, and we'll convert it to text.")

    recorded_audio_bytes = audiorecorder(show_visualizer=True, key="audio_to_text_recorder")

    if len(recorded_audio_bytes) > 500: # Check if there's substantial audio data
        st.audio(recorded_audio_bytes, format="audio/wav")
        
        with st.spinner("Transcribing your audio... please wait."):
            transcribed_text = mock_audio_to_text(recorded_audio_bytes)

        st.success("✍️ Transcription Complete!")
        st.markdown(f"> {transcribed_text}")
