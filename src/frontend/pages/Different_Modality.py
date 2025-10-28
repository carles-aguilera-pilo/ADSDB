from src.frontend.helpers.transformObjects import display_chat_message, getTextFromText, getImageFromText, getAudioFromText, getImageFromImage, getTextFromImage, getAudioFromImage, getAudioFromAudio, getTextFromAudio, getImageFromAudio
from src.dataobj.TextObj import TextObj
from src.dataobj.ImageObj import ImageObj
from src.dataobj.AudioObj import AudioObj
from src.chroma_connection import ChromaConnection
from src.minio_connection import MinIOConnection
import streamlit as st
from audiorecorder import audiorecorder
import io
from PIL import Image

# --- Page Config ---
st.set_page_config(
    page_title="Multi-Modal Chatbot",  # Updated title
    page_icon="🤖",
    layout="wide"
)

st.title("Multi-Modal Chatbot 💬🖼️🎤")
st.caption("Interact across different modalities: Text, Image, and Audio.")

with st.sidebar:
    st.header("⚙️ Configuración")
    k_text = st.number_input("K para Texto", min_value=1, max_value=50, value=10, help="Número de respuestas para texto")
    k_image = st.number_input("K para Imágenes", min_value=1, max_value=20, value=1, help="Número de respuestas para imágenes")
    k_audio = st.number_input("K para Audio", min_value=1, max_value=20, value=1, help="Número de respuestas para audio")

# --- Session State Initialization ---
if "text_messages" not in st.session_state:
    st.session_state.text_messages = []
if "image_messages" not in st.session_state:
    st.session_state.image_messages = []
if "audio_messages" not in st.session_state:
    st.session_state.audio_messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# --- Helper Function to Display All Message Types ---
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
def getTextFromText(prompt, k=10):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=k)
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        # --- MODIFIED: Join K results into one string ---
        num_docs = min(k, len(docs[0]))
        result = " ".join(docs[0][i] for i in range(num_docs) if docs[0][i] is not None)
        return result
    return "I'm sorry, I don't have a text answer for that."

# 2. Text -> Image
def getImageFromText(prompt, k=10):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=k) # Query IMAGE collection
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find a matching image."
    
    # --- MODIFIED: Return list of K images ---
    keys = response["ids"][0]
    images = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        matched_image_data = obj["Body"].read()
        images.append(Image.open(io.BytesIO(matched_image_data)).convert('RGB'))
    return images

# 3. Text -> Audio
def getAudioFromText(prompt, k=10):
    o = TextObj("texts/dummy.txt", prompt.encode('utf-8'))
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=k) # Query AUDIO collection
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find matching audio."

    # --- MODIFIED: Return list of K audios ---
    keys = response["ids"][0]
    audios = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        audios.append(obj["Body"].read())
    return audios

# 4. Image -> Text
def getTextFromImage(image_bytes, k=10):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=k) # Query TEXT collection
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        # --- MODIFIED: Join K results into one string ---
        num_docs = min(k, len(docs[0]))
        result = " ".join(docs[0][i] for i in range(num_docs) if docs[0][i] is not None)
        return result
    return "I'm sorry, I don't have a description for that image."

# 5. Image -> Image
def getImageFromImage(image_bytes, k=10):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find a similar image."

    # --- MODIFIED: Return list of K images ---
    keys = response["ids"][0]
    images = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        matched_image_data = obj["Body"].read()
        images.append(Image.open(io.BytesIO(matched_image_data)).convert('RGB'))
    return images

# 6. Image -> Audio
def getAudioFromImage(image_bytes, k=10):
    o = ImageObj("images/dummy.png", image_bytes)
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=k) # Query AUDIO collection
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find matching audio for that image."

    # --- MODIFIED: Return list of K audios ---
    keys = response["ids"][0]
    audios = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        audios.append(obj["Body"].read())
    return audios

# 7. Audio -> Text
def getTextFromAudio(audio_bytes, k=10):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("text_multimodal_collection", o.embeddings, n_results=k) # Query TEXT collection
    docs = response.get("documents")
    if docs and len(docs) > 0 and len(docs[0]) > 0:
        # --- MODIFIED: Join K results into one string ---
        num_docs = min(k, len(docs[0]))
        result = " ".join(docs[0][i] for i in range(num_docs) if docs[0][i] is not None)
        return result
    return "I'm sorry, I don't have a description for that audio."

# 8. Audio -> Image
def getImageFromAudio(audio_bytes, k=10):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("image_multimodal_collection", o.embeddings, n_results=k) # Query IMAGE collection
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find a matching image for that audio."
    
    # --- MODIFIED: Return list of K images ---
    keys = response["ids"][0]
    images = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        matched_image_data = obj["Body"].read()
        images.append(Image.open(io.BytesIO(matched_image_data)).convert('RGB'))
    return images

# 9. Audio -> Audio
def getAudioFromAudio(audio_bytes, k=10):
    o = AudioObj("audios/dummy.wav", audio_bytes)
    o.clean()
    o.format()
    o.embed()
    response = ChromaConnection().query("audio_multimodal_collection", o.embeddings, n_results=k)
    if not response["ids"] or not response["ids"][0]:
        return "Sorry, I couldn't find similar audio."

    # --- MODIFIED: Return list of K audios ---
    keys = response["ids"][0]
    audios = []
    num_results = min(k, len(keys))
    for i in range(num_results):
        obj = MinIOConnection().get_object(Bucket="exploitation-zone", Key=keys[i])
        audios.append(obj["Body"].read())
    return audios


# --- Streamlit Tabs ---

tab1, tab2, tab3 = st.tabs(["💬 Text Input", "🖼️ Image Input", "🎤 Audio Input"])

with tab1:
    st.header("Chat with Text")
    
    # Display chat history
    for msg in st.session_state.text_messages:
        display_chat_message(msg)  # Use the new helper

    # Output selection
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
        # Add user message
        st.session_state.text_messages.append({"role": "user", "content": prompt})

        # Get response based on selected mode
        if output_mode_text == "Text":
            response = getTextFromText(prompt, k=k_text)
            st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_text == "Image":
            response = getImageFromText(prompt, k=k_image)
            # --- MODIFIED: Handle list of images ---
            if isinstance(response, list):
                for img in response:
                    st.session_state.text_messages.append({"role": "assistant", "image": img})
            else: # Handle error string
                st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_text == "Audio":
            response = getAudioFromText(prompt, k=k_audio)
            # --- MODIFIED: Handle list of audios ---
            if isinstance(response, list):
                for audio_data in response:
                    st.session_state.text_messages.append({"role": "assistant", "audio": audio_data})
            else: # Handle error string
                st.session_state.text_messages.append({"role": "assistant", "content": response})
        
        st.rerun()

with tab2:
    st.header("Chat with Images")

    # Display chat history
    for msg in st.session_state.image_messages:
        display_chat_message(msg)  # Use the new helper

    # Output selection
    output_mode_image = st.radio(
        "What do you want to get back?",
        ("Image", "Text", "Audio"), # Reordered to make same-modality first
        key="image_output_mode",
        horizontal=True
    )

    with st.form(key="image_form", clear_on_submit=True):
        uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Send")

    if submitted and uploaded_image is not None:
        image_bytes = uploaded_image.read()
        
        # Add user message
        st.session_state.image_messages.append({
            "role": "user",
            "image": image_bytes # Display the uploaded image
        })

        # Get response based on selected mode
        if output_mode_image == "Image":
            response = getImageFromImage(image_bytes, k=k_image)
            # --- MODIFIED: Handle list of images ---
            if isinstance(response, list):
                for img in response:
                    st.session_state.image_messages.append({"role": "assistant", "image": img})
            else:
                st.session_state.image_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_image == "Text":
            response = getTextFromImage(image_bytes, k=k_text) # --- MODIFIED: Use k_text ---
            st.session_state.image_messages.append({"role": "assistant", "content": response})
        
        elif output_mode_image == "Audio":
            response = getAudioFromImage(image_bytes, k=k_audio) # --- MODIFIED: Use k_audio ---
            # --- MODIFIED: Handle list of audios ---
            if isinstance(response, list):
                for audio_data in response:
                    st.session_state.image_messages.append({"role": "assistant", "audio": audio_data})
            else:
                st.session_state.image_messages.append({"role": "assistant", "content": response})
        
        st.rerun()

with tab3:
    st.header("Chat with Audio")
    st.info("Select your desired output, then click to record. Stop to send. (Check browser permissions 🔒)")

    # Display chat history
    for msg in st.session_state.audio_messages:
        display_chat_message(msg)  # Use the new helper
    
    # Output selection
    output_mode_audio = st.radio(
        "What do you want to get back?",
        ("Audio", "Text", "Image"), # Reordered
        key="audio_output_mode",
        horizontal=True
    )

    audio_segment = audiorecorder(
        show_visualizer=True,
        key="audiorecorder"
    )

    buffer = io.BytesIO()
    if audio_segment.duration_seconds > 0: # Check if there is audio
        audio_segment.export(buffer, format="wav")

    if (
        isinstance(buffer.getvalue(), bytes)
        and len(buffer.getvalue()) > 100 # Ensure it's not just an empty header
        and buffer.getvalue() != st.session_state.last_processed_audio
    ):
        st.session_state.last_processed_audio = buffer.getvalue()
        
        # Add user message
        st.session_state.audio_messages.append({
            "role": "user", 
            "audio": buffer.getvalue()
        })

        # Get response based on mode selected at time of recording
        if output_mode_audio == "Audio":
            response = getAudioFromAudio(buffer.getvalue(), k=k_audio)
            # --- MODIFIED: Handle list of audios ---
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
            # --- MODIFIED: Handle list of images ---
            if isinstance(response, list):
                for img in response:
                    st.session_state.audio_messages.append({"role": "assistant", "image": img})
            else:
                st.session_state.audio_messages.append({"role": "assistant", "content": response})
        
        st.rerun()