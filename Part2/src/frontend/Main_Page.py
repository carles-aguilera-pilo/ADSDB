import streamlit as st

st.set_page_config(
    page_title="Projecte ADSDB",
    layout="centered"
)

st.title("Projecte ADSDB")

st.markdown(
    """
    ## Demonstration of the ADSDB Project: Deliverable 1

    This application shows various functionalities developed during the ADSDB project. 
    You can navigate through the different pages using the sidebar.

    ### What is available?
    - **Same Modality Chatbot**: Chatbot that allows you to ask questions and receive answers in the same format (text, image, or voice).
    - **Multi Modality Chatbot**: Chatbot that allows you to ask questions and receive answers in different formats (text, image, or voice).
    - **Generative Chatbot**: Chatbot that allows you to ask questions and receive generative answers in different formats (text, image, or voice) enhanced with specific data.
    - **Quality Report**: We have also added a page to display the data quality report. This report includes various metrics and visualizations to help you understand the quality of the data used in our chatbots.
    """
)
