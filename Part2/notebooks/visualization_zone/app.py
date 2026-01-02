import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY_ID")
SECRET_KEY = os.getenv("SECRET_ACCESS_KEY")
MINIO_URL = "http://" + os.getenv("S3_API_ENDPOINT")
BUCKET_NAME = "visualization-zone"

s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    endpoint_url=MINIO_URL
)

st.set_page_config(page_title="CLIP Skin Cancer Dashboard", layout="wide")
st.title("Skin Cancer Experiment Comparison")
st.markdown("---")

# --- HELPER FUNCTIONS ---

def list_experiment_folders():
    """Lists top-level folders in the bucket which represent EXPERIMENT_NAME."""
    paginator = s3.get_paginator('list_objects_v2')
    folders = set()
    for result in paginator.paginate(Bucket=BUCKET_NAME, Delimiter='/'):
        for prefix in result.get('CommonPrefixes', []):
            # Extract folder name from 'Folder/'
            folders.add(prefix.get('Prefix').rstrip('/'))
    return sorted(list(folders))

def load_experiment_assets(folder_name):
    """Finds the .json and .png files within the specific experiment folder."""
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=f"{folder_name}/")
    
    metrics_data = None
    loss_image = None
    
    for obj in objects.get('Contents', []):
        key = obj['Key']
        if key.endswith('.json'):
            json_obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            metrics_data = json.loads(json_obj['Body'].read().decode('utf-8'))
        elif key.endswith('.png'):
            img_obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            loss_image = Image.open(io.BytesIO(img_obj['Body'].read()))
            
    return metrics_data, loss_image

# --- SIDEBAR ---
st.sidebar.header("Experiment Filter")
all_folders = list_experiment_folders()
selected_folders = st.sidebar.multiselect("Select experiments:", all_folders)

if not selected_folders:
    st.info("Please select one or more experiments from the sidebar to begin comparison.")
else:
    all_metrics = []
    all_images = {}

    for folder in selected_folders:
        m, img = load_experiment_assets(folder)
        if m and img:
            # Flattens the nested 'metrics' dict you defined earlier
            # Adds the Experiment name as a column for comparison
            flat_row = {"Experiment": folder, **m.get('metrics', {})}
            all_metrics.append(flat_row)
            all_images[folder] = img

    df = pd.DataFrame(all_metrics)

    # --- VISUALIZATION TABS ---
    tab1, tab2, tab3 = st.tabs(["Diagnostic Performance", "Semantic Meaning", "Efficiency"])

    with tab1:
        st.subheader("Perspective 1 & 2: Alignment and Safety")
        c1, c2 = st.columns(2)
        with c1:
            # Retrieval Metrics
            ret_df = df.melt(id_vars="Experiment", value_vars=["Recall@1", "Recall@5", "Recall@10"])
            fig_ret = px.bar(ret_df, x="variable", y="value", color="Experiment", barmode="group", title="Retrieval Recall")
            st.plotly_chart(fig_ret, use_container_width=True)
        with c2:
            # Clinical Safety Metrics
            safe_df = df.melt(id_vars="Experiment", value_vars=["Sensitivity", "Specificity", "F1 Score"])
            fig_safe = px.bar(safe_df, x="variable", y="value", color="Experiment", barmode="group", title="Clinical Metrics")
            st.plotly_chart(fig_safe, use_container_width=True)

    with tab2:
        st.subheader("Perspective 3: BERTScore Alignment")
        bert_vars = [c for c in df.columns if "BertScore" in c or "BERTScore" in c]
        if bert_vars:
            bert_df = df.melt(id_vars="Experiment", value_vars=bert_vars)
            fig_bert = px.bar(bert_df, x="Experiment", y="value", color="variable", barmode="group")
            st.plotly_chart(fig_bert, use_container_width=True)
        else:
            st.warning("No BERTScore metrics found in selected JSON files.")

    with tab3:
        st.subheader("Perspective 4: System Specifications")
        col_eff1, col_eff2 = st.columns(2)
        with col_eff1:
            fig_vram = px.bar(df, x="Experiment", y="Peak VRAM Usage (GB)", title="GPU Memory Usage")
            st.plotly_chart(fig_vram, use_container_width=True)
        with col_eff2:
            fig_lat = px.bar(df, x="Experiment", y="Inference Latency (ms)", title="Inference Latency")
            st.plotly_chart(fig_lat, use_container_width=True)

    # --- LOSS CURVES SECTION ---
    st.markdown("---")
    st.subheader("Training History (Loss Curves)")
    img_cols = st.columns(len(selected_folders))
    for i, folder in enumerate(selected_folders):
        with img_cols[i]:
            st.image(all_images[folder], caption=f"Loss: {folder}")

    # --- RAW DATA ---
    st.markdown("---")
    st.subheader("Detailed Metrics Table")
    st.dataframe(df.set_index("Experiment"))