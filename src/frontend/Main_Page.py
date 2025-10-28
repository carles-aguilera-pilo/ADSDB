import streamlit as st

# --- Page Config ---
# The page config must be the first Streamlit command used, and must only be set once
st.set_page_config(
    page_title="AI Creations Hub",
    page_icon="💌",
    layout="centered"
)

# --- Main Page Content ---
st.title("💌 Welcome to the AI Creations Hub!")
st.sidebar.success("Select a studio from the menu above.")

st.markdown(
    """
    This is a hub for multimodal AI applications built with Streamlit.

    **👈 Select a studio from the sidebar** to get started.

    ### What's available?
    - **🤖 Multimodal Chatbot**: Engage in a conversation using text, images, or your voice.
    - **🤖 Same Modality Chatbot**: Engage in a conversation using text, images, or your voice.
    - **🤖 Generative Chatbot**: Engage in a conversation using text, images, or your voice enhanced with specific data.

    This application demonstrates how to structure a multi-page Streamlit app
    and integrate various I/O components.
    """
)
