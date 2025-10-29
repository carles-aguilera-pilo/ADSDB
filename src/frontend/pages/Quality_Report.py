import streamlit as st
import boto3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from PIL import Image
import cv2
import librosa
import librosa.display
from pydub import AudioSegment
from pydub.silence import detect_silence
import math
import re
import unicodedata
from dotenv import load_dotenv
from tqdm import tqdm # tqdm will be used by librosa, but we'll use st.spinner for UI

# -------------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Data Quality Report",
    page_icon="📊",
    layout="wide"
)

# -------------------------------------------------------------------
# MINIO S3 CLIENT (CACHED)
# -------------------------------------------------------------------

# Load environment variables
load_dotenv()

@st.cache_resource
def get_minio_client():
    """Initializes and returns a cached MinIO client."""
    try:
        access_key_id = os.getenv("ACCESS_KEY_ID")
        secret_access_key = os.getenv("SECRET_ACCESS_KEY")
        minio_url = "http://" + os.getenv("S3_API_ENDPOINT")

        if not all([access_key_id, secret_access_key, minio_url]):
            st.error("Missing MinIO credentials in .env file. Please check ACCESS_KEY_ID, SECRET_ACCESS_KEY, and S3_API_ENDPOINT.")
            return None

        minio_client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=minio_url
        )
        return minio_client
    except Exception as e:
        st.error(f"Failed to initialize MinIO client: {e}")
        return None

# -------------------------------------------------------------------
# ANALYSIS FUNCTIONS (from notebooks)
# -------------------------------------------------------------------

# --- Text Analysis ---
def analisi_text(text):
    problemas = {}

    control_chars = [c for c in text if unicodedata.category(c)[0] == 'C' and c not in '\n\t']
    problemas["caracteres_control"] = len(control_chars)

    lineas_con_espacios = [line for line in text.splitlines() if line.startswith(" ") or line.endswith(" ")]
    problemas["lineas_con_espacios"] = len(lineas_con_espacios)

    saltos_multiples = bool(re.search(r"\n\s*\n\s*\n+", text))
    problemas["saltos_multiples"] = saltos_multiples

    lineas_vacias = [line for line in text.splitlines() if not line.strip()]
    problemas["lineas_vacias"] = len(lineas_vacias)

    caracteres_invalidos = re.findall(r"[^\w\s\.,;:\!\?\(\)\[\]\"\'\-\+=\%&\$\/\@\#\*]", text)
    problemas["caracteres_especiales"] = len(caracteres_invalidos)

    comillas_tipograficas = re.findall(r"[“”«»]", text)
    apostrofes_tipograficos = re.findall(r"[‘’]", text)
    problemas["comillas_tipograficas"] = len(comillas_tipograficas)
    problemas["apostrofes_tipograficos"] = len(apostrofes_tipograficos)

    guiones_multiples = bool(re.search(r"-{2,}", text))
    problemas["guiones_multiples"] = guiones_multiples

    texto_vacio = not text.strip()
    problemas["texto_vacio"] = texto_vacio

    return {
        "problems_control_caracters": problemas["caracteres_control"],
        "problems_lineas_con_espacios": problemas["lineas_con_espacios"],
        "problems_saltos_multiples": problemas["saltos_multiples"],
        "problems_lineas_vacias": problemas["lineas_vacias"],
        "problems_caracteres_especiales": problemas["caracteres_especiales"],
        "problems_comillas_tipograficas": problemas["comillas_tipograficas"],
        "problems_apostrofes_tipograficos": problemas["apostrofes_tipograficos"],
        "problems_guiones_multiples": problemas["guiones_multiples"],
        "problems_texto_vacio": problemas["texto_vacio"]
    }

# --- Image Analysis ---
def analisi_imagen(img_bytes):
    try:
        img = Image.open(BytesIO(img_bytes))
        modo = img.mode
        width, height = img.size

        if modo not in ['RGB', 'RGBA', 'L']:
            img = img.convert('RGB')
            modo = img.mode
        
        image_np = np.array(img)

        # Ensure image is 3-channel for functions expecting color
        if modo == 'L':
             gray_np = image_np
             color_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif modo == 'RGBA':
             gray_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2GRAY)
             color_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        else: # RGB
             gray_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
             color_np = image_np


        #---- CHECK DIMENSIONS & ASPECT RATIO ----
        aspect_ratio = width / height if height > 0 else 0
        total_pixels = width * height
        is_square = abs(aspect_ratio - 1.0) < 0.05
        is_portrait = aspect_ratio < 0.8
        is_landscape = aspect_ratio > 1.2
        
        #---- CHECK BRIGHTNESS AND CONTRAST ----
        brillo = np.mean(gray_np)
        contraste = np.std(gray_np)
        
        fosca = brillo < 80
        brillant = brillo > 200
        contrast = contraste < 10
        
        #---- CHECK COLOR SATURATION ----
        has_color = (modo == 'RGB' or modo == 'RGBA')
        if has_color:
            saturation = np.std(cv2.cvtColor(color_np, cv2.COLOR_RGB2HSV)[:, :, 1])
            low_saturation = saturation < 30
            high_saturation = saturation > 100
        else:
            saturation = 0
            low_saturation = True
            high_saturation = False
            
        #---- CHECK SHARPNESS / BLUR ----
        variance = cv2.Laplacian(gray_np, cv2.CV_64F).var()
        necessita_nitidez = variance < 50
        blur_score = variance
        blur_detected = variance < 50
        
        #---- CHECK NOISE ----
        blur_cv = cv2.GaussianBlur(gray_np, (3,3), 0)
        diff = cv2.absdiff(gray_np, blur_cv)
        local_variance = np.var(diff)
        
        if local_variance < 50:
            noise = 'Low'
        elif local_variance < 150:
            noise = 'Medium'
        else:
            noise = 'High'
        
        #---- CHECK COLOR CHANNELS ----
        num_channels = len(modo)
        
        #---- COMPRESSION ARTIFACTS DETECTION ----
        compression_score = variance # Using Laplacian variance as a proxy
        compression_artifacts = compression_score < 20
        
        #---- QUALITY SCORE (Composite) ----
        quality_score = 100
        if fosca or brillant: quality_score -= 20
        if contrast: quality_score -= 15
        if necessita_nitidez: quality_score -= 15
        if noise == 'High': quality_score -= 10
        if total_pixels < 10000: quality_score -= 20
        
        return {
            'width': width, 'height': height, 'aspect_ratio': aspect_ratio, 'total_pixels': total_pixels,
            'is_square': is_square, 'is_portrait': is_portrait, 'is_landscape': is_landscape,
            'brillo': brillo, 'contraste': contraste, 'saturation': saturation,
            'low_saturation': low_saturation, 'high_saturation': high_saturation,
            'fosc': fosca, 'brillant': brillant, 'contrast': contrast,
            'nitidez': necessita_nitidez, 'blur_score': blur_score, 'blur_detected': blur_detected,
            'noise': noise, 'has_color': has_color, 'num_channels': num_channels,
            'compression_artifacts': compression_artifacts, 'quality_score': quality_score
        }
    except Exception as e:
        st.warning(f"Could not process an image. Error: {e}")
        return None # Return None for failed analysis

# --- Audio Analysis ---
def detectar_filtro(centroid, rolloff, ratio):
    if centroid < 1500 and rolloff < 3000 and ratio < 0.5:
        return "Low-pass filter"
    elif centroid > 4000 and rolloff > 6000 and ratio > 1.5:
        return "High-pass filter"
    elif 1500 <= centroid <= 4000 and 3000 <= rolloff <= 6000 and 0.5 <= ratio <= 1.5:
        return "Band-pass filter"
    else:
        return "No filter"

def analyze_audio_file(audio_bytes):
    try:
        audio = AudioSegment.from_file(BytesIO(audio_bytes))
        
        duration = len(audio) / 1000
        frame_rate = audio.frame_rate
        channels = audio.channels
        sample_width = audio.sample_width
        
        rms = audio.rms
        audio_level = 20 * math.log10(rms) if rms > 0 else -float('inf')
        peak = audio.max
        noise_floor = audio.dBFS
        
        silence_ranges = detect_silence(audio, min_silence_len=500, silence_thresh=-50)
        total_silence_duration = sum(end - start for start, end in silence_ranges) / 1000
        silence_percent = (total_silence_duration / duration) * 100 if duration > 0 else 0
        
        dynamic_range = peak - rms
        
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        if channels == 2:
            samples = samples.reshape((-1, 2))
            samples = np.mean(samples, axis=1)
        
        if audio.sample_width == 1: # 8-bit
             samples /= 128.0 
        elif audio.sample_width == 2: # 16-bit
             samples /= 32768.0
        elif audio.sample_width == 4: # 32-bit
             samples /= 2147483648.0
            
        sr = audio.frame_rate
        
        if len(samples) == 0:
            return None # Skip empty audio file

        centroid = librosa.feature.spectral_centroid(y=samples, sr=sr)
        bandwidth = librosa.feature.spectral_bandwidth(y=samples, sr=sr)
        rolloff = librosa.feature.spectral_rolloff(y=samples, sr=sr, roll_percent=0.95)

        S = np.abs(librosa.stft(samples))
        freqs = librosa.fft_frequencies(sr=sr)

        low_energy = np.sum(S[(freqs > 0) & (freqs < 1000)])
        high_energy = np.sum(S[freqs > 5000])
        ratio = high_energy / (low_energy + 1e-9)

        centroid_mean = np.mean(centroid)
        bandwidth_mean = np.mean(bandwidth)
        rolloff_mean = np.mean(rolloff)
        
        filter_type = detectar_filtro(centroid_mean, rolloff_mean, ratio)
        
        return {
            "duration": duration, "frame_rate": frame_rate, "channels": channels,
            "sample_width": sample_width, "audio_level": audio_level, "peak": peak,
            "noise_floor": noise_floor, "silence_ranges": silence_ranges,
            "total_silence_duration": total_silence_duration, "silence_percent": silence_percent,
            "dynamic_range": dynamic_range, "filter_type": filter_type
        }
    except Exception as e:
        st.warning(f"Could not process an audio file. Error: {e}")
        return None # Return None for failed analysis

# -------------------------------------------------------------------
# DATA LOADING FUNCTIONS (CACHED)
# -------------------------------------------------------------------

def load_data(bucket, prefix, analysis_func, file_type):
    """Generic data loading and analysis function."""
    minio_client = get_minio_client()
    if minio_client is None:
        return pd.DataFrame()

    analysis_list = []
    paginator = minio_client.get_paginator("list_objects_v2")
    
    with st.spinner(f"Loading and analyzing {file_type} files..."):
        try:
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith('/'): continue # Skip directories

                    response = minio_client.get_object(Bucket=bucket, Key=key)
                    data_bytes = response["Body"].read()
                    
                    if file_type == 'text':
                        data_to_analyze = data_bytes.decode("utf-8", errors="ignore")
                        result = analysis_func(data_to_analyze)
                    else:
                        result = analysis_func(data_bytes)

                    if result:
                        analysis_list.append(result)
        except Exception as e:
            st.error(f"Error loading data from MinIO: {e}")
            return pd.DataFrame()

    if not analysis_list:
        st.warning(f"No {file_type} files found in 'formatted-zone' with prefix '{prefix}'.")
        return pd.DataFrame()
        
    return pd.DataFrame(analysis_list)

# -------------------------------------------------------------------
# STATISTICAL SUMMARY FUNCTIONS
# -------------------------------------------------------------------

def show_text_stats(df):
    summary_text = f"""
================================================================================
Text Quality Analysis - Summary Statistics
================================================================================

Total files analyzed: {len(df)}

CONTROL CHARACTERS:
   Files with control characters: {df[df['problems_control_caracters'] > 0].shape[0]} ({(df[df['problems_control_caracters'] > 0].shape[0]/len(df)*100):.1f}%)

TRAILING/LEADING SPACES:
   Average lines with spaces per file: {df['problems_lineas_con_espacios'].mean():.1f}
   Max lines with spaces in a single file: {df['problems_lineas_con_espacios'].max()}

LINE BREAKS:
   Files with multiple line breaks: {df['problems_saltos_multiples'].sum()} ({(df['problems_saltos_multiples'].sum()/len(df)*100):.1f}%)

EMPTY LINES:
   Average empty lines per file: {df['problems_lineas_vacias'].mean():.1f}
   Max empty lines in a single file: {df['problems_lineas_vacias'].max()}

SPECIAL CHARACTERS:
   Average special characters per file: {df['problems_caracteres_especiales'].mean():.1f}
   Files with >20 special characters: {(df['problems_caracteres_especiales'] > 20).sum()}

TYPOGRAPHIC CHARACTERS:
   Files with typographic quotes: {(df['problems_comillas_tipograficas'] > 0).sum()}
   Files with typographic apostrophes: {(df['problems_apostrofes_tipograficos'] > 0).sum()}

MULTIPLE HYPHENS:
   Files with multiple hyphens: {df['problems_guiones_multiples'].sum()} ({(df['problems_guiones_multiples'].sum()/len(df)*100):.1f}%)

EMPTY FILES:
   Empty text files: {df['problems_texto_vacio'].sum()} ({(df['problems_texto_vacio'].sum()/len(df)*100):.1f}%)

================================================================================
    """
    st.code(summary_text, language="text")

def show_image_stats(df):
    quality_levels = pd.cut(df['quality_score'], bins=[0, 50, 70, 85, 100], labels=['Poor', 'Fair', 'Good', 'Excellent'])
    
    summary_text = f"""
================================================================================
Complete Statistical Summary - Images
================================================================================

DIMENSIONS:
   Average dimensions: {df['width'].mean():.0f}x{df['height'].mean():.0f} pixels
   Minimum dimensions: {df['width'].min():.0f}x{df['height'].min():.0f} pixels
   Maximum dimensions: {df['width'].max():.0f}x{df['height'].max():.0f} pixels
   Average total pixels: {df['total_pixels'].mean():,.0f}

ORIENTATION:
   Squares: {df['is_square'].sum()} ({(df['is_square'].sum()/len(df)*100):.1f}%)
   Portraits: {df['is_portrait'].sum()} ({(df['is_portrait'].sum()/len(df)*100):.1f}%)
   Horizontals: {df['is_landscape'].sum()} ({(df['is_landscape'].sum()/len(df)*100):.1f}%)

COLOR SATURATION:
   Low saturation: {df['low_saturation'].sum()} ({(df['low_saturation'].sum()/len(df)*100):.1f}%)
   High saturation: {df['high_saturation'].sum()} ({(df['high_saturation'].sum()/len(df)*100):.1f}%)
   Average saturation: {df['saturation'].mean():.1f}

BLUR DETECTION:
   Images with blur: {df['blur_detected'].sum()} ({(df['blur_detected'].sum()/len(df)*100):.1f}%)
   Average blur score: {df['blur_score'].mean():.1f}

COMPRESSION ARTIFACTS:
   With artifacts: {df['compression_artifacts'].sum()} ({(df['compression_artifacts'].sum()/len(df)*100):.1f}%)

QUALITY SCORE:
   Average score: {df['quality_score'].mean():.1f}/100
   Minimum score: {df['quality_score'].min():.1f}/100
   Maximum score: {df['quality_score'].max():.1f}/100
   Poor: {(quality_levels == 'Poor').sum()} imágenes ({( (quality_levels == 'Poor').sum()/len(df)*100):.1f}%)
   Fair: {(quality_levels == 'Fair').sum()} imágenes ({( (quality_levels == 'Fair').sum()/len(df)*100):.1f}%)
   Good: {(quality_levels == 'Good').sum()} imágenes ({( (quality_levels == 'Good').sum()/len(df)*100):.1f}%)
   Excellent: {(quality_levels == 'Excellent').sum()} imágenes ({( (quality_levels == 'Excellent').sum()/len(df)*100):.1f}%)

================================================================================
    """
    st.code(summary_text, language="text")

def show_audio_stats(df):
    summary_text = f"""
================================================================================
Audio Quality Analysis - Summary Statistics
================================================================================

Total audio files analyzed: {len(df)}

DURATION:
   Average duration: {df['duration'].mean():.2f} seconds
   Minimum duration: {df['duration'].min():.2f} seconds
   Maximum duration: {df['duration'].max():.2f} seconds

SAMPLE RATE:
   Average sample rate: {df['frame_rate'].mean():.0f} Hz
   Most common sample rate: {df['frame_rate'].mode()[0]:.0f} Hz

CHANNELS:
"""
    for channel in sorted(df['channels'].unique()):
        count = (df['channels'] == channel).sum()
        summary_text += f"   {channel} channel(s): {count} files ({(count/len(df)*100):.1f}%)\n"

    summary_text += f"""
AUDIO LEVEL (RMS):
   Average level: {df['audio_level'].mean():.1f} dB
   Minimum level: {df['audio_level'].min():.1f} dB
   Maximum level: {df['audio_level'].max():.1f} dB

DYNAMIC RANGE:
   Average dynamic range: {df['dynamic_range'].mean():.1f}
   Files with low dynamic range (<1000): {(df['dynamic_range'] < 1000).sum()}

SILENCE:
   Average silence: {df['silence_percent'].mean():.1f}%
   Files with high silence (>30%): {(df['silence_percent'] > 30).sum()}

NOISE FLOOR:
   Average noise floor: {df['noise_floor'].mean():.1f} dBFS
   Files with high noise floor (>-50 dBFS): {(df['noise_floor'] > -50).sum()}

FILTER TYPES:
"""
    for filter_type in sorted(df['filter_type'].unique()):
        count = (df['filter_type'] == filter_type).sum()
        summary_text += f"   {filter_type}: {count} files ({(count/len(df)*100):.1f}%)\n"
    
    summary_text += "================================================================================\n"
    st.code(summary_text, language="text")


# -------------------------------------------------------------------
# PLOTTING FUNCTIONS
# -------------------------------------------------------------------

# --- Text Plots ---
def plot_text_summary(df):
    fig, axes = plt.subplots(3, 3, figsize=(20, 15))
    fig.suptitle('Text Quality - Overall Summary', fontsize=20, y=1.03)

    # 1. Control characters
    axes[0, 0].bar(['Files with', 'Files without'], 
                   [df[df['problems_control_caracters'] > 0].shape[0],
                    df[df['problems_control_caracters'] == 0].shape[0]],
                   color=['red', 'green'])
    axes[0, 0].set_title('Control Characters Detection')
    axes[0, 0].set_ylabel('Number of Files')

    # 2. Lines with spaces
    sns.histplot(df['problems_lineas_con_espacios'], bins=20, color='orange', ax=axes[0, 1], kde=True)
    axes[0, 1].set_title('Distribution: Lines with Trailing/Leading Spaces')
    axes[0, 1].set_xlabel('Count')
    axes[0, 1].set_ylabel('Frequency')

    # 3. Multiple line breaks
    axes[0, 2].bar(['Yes', 'No'], 
                   [df['problems_saltos_multiples'].sum(),
                    len(df) - df['problems_saltos_multiples'].sum()],
                   color=['red', 'green'])
    axes[0, 2].set_title('Multiple Line Breaks')
    axes[0, 2].set_ylabel('Number of Files')

    # 4. Empty lines
    sns.histplot(df['problems_lineas_vacias'], bins=20, color='purple', ax=axes[1, 0], kde=True)
    axes[1, 0].set_title('Distribution: Empty Lines')
    axes[1, 0].set_xlabel('Count')
    axes[1, 0].set_ylabel('Frequency')

    # 5. Special characters
    sns.histplot(df['problems_caracteres_especiales'], bins=20, color='cyan', ax=axes[1, 1], kde=True)
    axes[1, 1].set_title('Distribution: Special Characters')
    axes[1, 1].set_xlabel('Count')
    axes[1, 1].set_ylabel('Frequency')

    # 6. Typographic quotes
    sns.histplot(df['problems_comillas_tipograficas'], bins=10, color='pink', ax=axes[1, 2], kde=True)
    axes[1, 2].set_title('Distribution: Typographic Quotes')
    axes[1, 2].set_xlabel('Count')
    axes[1, 2].set_ylabel('Frequency')

    # 7. Typographic apostrophes
    sns.histplot(df['problems_apostrofes_tipograficos'], bins=10, color='brown', ax=axes[2, 0], kde=True)
    axes[2, 0].set_title('Distribution: Typographic Apostrophes')
    axes[2, 0].set_xlabel('Count')
    axes[2, 0].set_ylabel('Frequency')

    # 8. Multiple hyphens
    axes[2, 1].bar(['Yes', 'No'], [df['problems_guiones_multiples'].sum(),
                    len(df) - df['problems_guiones_multiples'].sum()],color=['red', 'green'])
    axes[2, 1].set_title('Multiple Hyphens Detection')
    axes[2, 1].set_ylabel('Number of Files')

    # 9. Empty text
    axes[2, 2].bar(['No', 'Yes'], 
        [len(df) - df['problems_texto_vacio'].sum(),
                    df['problems_texto_vacio'].sum()],
                   color=['green', 'red'])
    axes[2, 2].set_title('Empty Text Files')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    return fig

def plot_text_correlation(df):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    correlation_metrics = ['problems_control_caracters', 'problems_lineas_con_espacios','problems_lineas_vacias', 'problems_caracteres_especiales','problems_comillas_tipograficas', 'problems_apostrofes_tipograficos']
    corr_matrix = df[correlation_metrics].corr()

    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, ax=axes[0])
    axes[0].set_title('Correlation Matrix of Text Quality Metrics')

    axes[1].scatter(df['problems_lineas_vacias'], df['problems_caracteres_especiales'], alpha=0.6, s=100)
    axes[1].set_title('Empty Lines vs Special Characters')
    axes[1].set_xlabel('Empty Lines')
    axes[1].set_ylabel('Special Characters')

    plt.tight_layout()
    return fig

# --- Image Plots ---
def plot_image_brightness_contrast(df):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Image Brightness & Contrast Analysis', fontsize=16, y=1.03)

    # Line plot for brightness and contrast
    axes[0].plot(df['brillo'], label='Brightness')
    axes[0].plot(df['contraste'], label='Contrast')
    axes[0].set_title('Brightness and Contrast per Image')
    axes[0].set_xlabel('Image Index')
    axes[0].set_ylabel('Value')
    axes[0].legend()

    # Count plot for 'fosc' (dark)
    df_temp_fosc = df.copy()
    df_temp_fosc['fosc'] = df_temp_fosc['fosc'].astype(str)
    sns.countplot(data=df_temp_fosc, x='fosc', ax=axes[1])
    axes[1].set_title('Distribution: Dark Images (True/False)')
    axes[1].set_xlabel('')

    # Count plot for 'brillant' (bright)
    df_temp_brillant = df.copy()
    df_temp_brillant['brillant'] = df_temp_brillant['brillant'].astype(str)
    sns.countplot(data=df_temp_brillant, x='brillant', ax=axes[2])
    axes[2].set_title('Distribution: Bright Images (True/False)')
    axes[2].set_xlabel('')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def plot_image_dims(df):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Image Dimension & Aspect Ratio Analysis', fontsize=16, y=1.03)

    # Width and height distribution
    sns.histplot(df['width'], bins=20, alpha=0.5, label='Width', color='blue', ax=axes[0, 0], kde=True)
    sns.histplot(df['height'], bins=20, alpha=0.5, label='Height', color='red', ax=axes[0, 0], kde=True)
    axes[0, 0].set_title('Distribution of Width and Height')
    axes[0, 0].set_xlabel('Pixels')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].legend()

    # Aspect Ratio
    sns.histplot(df['aspect_ratio'], bins=30, color='green', ax=axes[0, 1], kde=True)
    axes[0, 1].set_title('Distribution of Aspect Ratio')
    axes[0, 1].set_xlabel('Ratio (Width/Height)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].axvline(x=1.0, color='red', linestyle='--', label='Square (1:1)')
    axes[0, 1].legend()

    # Image orientation
    orientation_counts = pd.DataFrame({
        'Type': ['Square', 'Portrait', 'Landscape'],
        'Count': [df['is_square'].sum(), df['is_portrait'].sum(), df['is_landscape'].sum()]
    })
    sns.barplot(data=orientation_counts, x='Type', y='Count', ax=axes[1, 0], palette=['orange', 'purple', 'cyan'])
    axes[1, 0].set_title('Image Orientation')
    axes[1, 0].set_ylabel('Count')

    # Total pixels
    sns.histplot(df['total_pixels'], bins=30, color='brown', ax=axes[1, 1], kde=True)
    axes[1, 1].set_title('Distribution of Total Pixels')
    axes[1, 1].set_xlabel('Total Pixels')
    axes[1, 1].set_ylabel('Frequency')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def plot_image_color(df):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Image Color & Saturation Analysis', fontsize=16, y=1.03)

    # Saturation histogram
    sns.histplot(df['saturation'], bins=30, color='pink', ax=axes[0], kde=True)
    axes[0].axvline(x=30, color='red', linestyle='--', label='Low Threshold')
    axes[0].axvline(x=100, color='blue', linestyle='--', label='High Threshold')
    axes[0].set_title('Distribution of Color Saturation')
    axes[0].set_xlabel('Saturation')
    axes[0].set_ylabel('Frequency')
    axes[0].legend()

    # Low/high saturation distribution
    saturation_counts = pd.DataFrame({
        'Type': ['Normal', 'Low Saturation', 'High Saturation'],
        'Count': [
            ((df['low_saturation'] == False) & (df['high_saturation'] == False)).sum(),
            df['low_saturation'].sum(),
            df['high_saturation'].sum()
        ]
    })
    sns.barplot(data=saturation_counts, x='Type', y='Count', ax=axes[1], palette=['green', 'orange', 'purple'])
    axes[1].set_title('Color Saturation (Classification)')
    axes[1].set_ylabel('Count')

    # Color channels
    channel_counts = df['num_channels'].value_counts().sort_index()
    sns.barplot(x=channel_counts.index.astype(str), y=channel_counts.values, ax=axes[2], color='teal')
    axes[2].set_title('Number of Color Channels')
    axes[2].set_xlabel('Channels (1=Gray, 3=RGB, 4=RGBA)')
    axes[2].set_ylabel('Count')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def plot_image_quality_score(df):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Overall Image Quality Score Analysis', fontsize=16, y=1.03)

    # Quality Score distribution
    sns.histplot(df['quality_score'], bins=20, color='darkgreen', edgecolor='black', ax=axes[0, 0], kde=True)
    axes[0, 0].axvline(x=70, color='red', linestyle='--', label='Threshold (70)')
    axes[0, 0].set_title('Distribution of Quality Score')
    axes[0, 0].set_xlabel('Quality Score (0-100)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].legend()

    # Quality classification
    quality_levels = pd.cut(df['quality_score'], bins=[0, 50, 70, 85, 100], labels=['Poor', 'Fair', 'Good', 'Excellent'])
    quality_counts = quality_levels.value_counts().sort_index()
    sns.barplot(x=quality_counts.index.astype(str), y=quality_counts.values, ax=axes[0, 1], palette=['red', 'orange', 'yellow', 'green'])
    axes[0, 1].set_title('Quality Classification')
    axes[0, 1].set_ylabel('Number of Images')
    axes[0, 1].tick_params(axis='x', rotation=45)

    # Blur Score vs Quality Score
    axes[1, 0].scatter(df['blur_score'], df['quality_score'], alpha=0.5, s=50)
    axes[1, 0].set_title('Relationship: Blur Score vs Quality Score')
    axes[1, 0].set_xlabel('Blur Score (Higher is Sharper)')
    axes[1, 0].set_ylabel('Quality Score')

    # Correlation matrix
    quality_metrics = ['brillo', 'contraste', 'saturation', 'blur_score', 'quality_score']
    correlation_matrix = df[quality_metrics].corr()
    sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, ax=axes[1, 1])
    axes[1, 1].set_title('Correlation Matrix of Metrics')
    axes[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

# --- Audio Plots ---
def plot_audio_summary(df):
    fig, axes = plt.subplots(3, 3, figsize=(20, 15))
    fig.suptitle('Audio Quality - Overall Summary', fontsize=20, y=1.03)

    # 1. Duration distribution
    sns.histplot(df['duration'], bins=20, color='blue', edgecolor='black', ax=axes[0, 0], kde=True)
    axes[0, 0].set_title('Duration Distribution (seconds)')
    axes[0, 0].set_xlabel('Duration (seconds)')
    axes[0, 0].set_ylabel('Frequency')

    # 2. Frame rate (sample rate) distribution
    sns.histplot(df['frame_rate'], bins=15, color='green', edgecolor='black', ax=axes[0, 1], kde=True)
    axes[0, 1].set_title('Sample Rate Distribution')
    axes[0, 1].set_xlabel('Sample Rate (Hz)')
    axes[0, 1].set_ylabel('Frequency')

    # 3. Channels (mono vs stereo)
    channels_counts = df['channels'].value_counts()
    sns.barplot(x=channels_counts.index.astype(str), y=channels_counts.values, ax=axes[0, 2], palette=['red', 'blue'])
    axes[0, 2].set_title('Audio Channels Distribution')
    axes[0, 2].set_xlabel('Channels')
    axes[0, 2].set_ylabel('Count')

    # 4. Audio level (RMS in dB)
    sns.histplot(df['audio_level'], bins=20, color='orange', edgecolor='black', ax=axes[1, 0], kde=True)
    axes[1, 0].set_title('Audio Level Distribution (dB)')
    axes[1, 0].set_xlabel('RMS Level (dB)')
    axes[1, 0].set_ylabel('Frequency')

    # 5. Dynamic range
    sns.histplot(df['dynamic_range'], bins=20, color='purple', edgecolor='black', ax=axes[1, 1], kde=True)
    axes[1, 1].set_title('Dynamic Range Distribution')
    axes[1, 1].set_xlabel('Dynamic Range')
    axes[1, 1].set_ylabel('Frequency')

    # 6. Silence percentage
    sns.histplot(df['silence_percent'], bins=20, color='cyan', edgecolor='black', ax=axes[1, 2], kde=True)
    axes[1, 2].set_title('Silence Percentage Distribution')
    axes[1, 2].set_xlabel('Silence (%)')
    axes[1, 2].set_ylabel('Frequency')

    # 7. Noise floor (dBFS)
    sns.histplot(df['noise_floor'], bins=20, color='pink', edgecolor='black', ax=axes[2, 0], kde=True)
    axes[2, 0].set_title('Noise Floor Distribution (dBFS)')
    axes[2, 0].set_xlabel('Noise Floor (dBFS)')
    axes[2, 0].set_ylabel('Frequency')

    # 8. Filter type distribution
    filter_counts = df['filter_type'].value_counts()
    sns.barplot(x=filter_counts.index, y=filter_counts.values, ax=axes[2, 1], palette=['brown', 'gray', 'gold', 'coral'])
    axes[2, 1].set_title('Filter Type Distribution')
    axes[2, 1].set_xticklabels(filter_counts.index, rotation=45, ha='right')
    axes[2, 1].set_ylabel('Count')

    # 9. Sample width distribution
    sample_width_counts = df['sample_width'].value_counts()
    sns.barplot(x=sample_width_counts.index.astype(str), y=sample_width_counts.values, ax=axes[2, 2], color='teal')
    axes[2, 2].set_title('Sample Width Distribution (bytes)')
    axes[2, 2].set_xlabel('Sample Width (bytes)')
    axes[2, 2].set_ylabel('Count')

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    return fig

def plot_audio_correlation(df):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Correlation matrix
    correlation_metrics = ['duration', 'audio_level', 'noise_floor', 'silence_percent', 'dynamic_range']
    corr_matrix = df[correlation_metrics].corr()

    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, ax=axes[0])
    axes[0].set_title('Correlation Matrix of Audio Metrics')

    # Audio level vs Dynamic range
    axes[1].scatter(df['audio_level'], df['dynamic_range'], alpha=0.6, s=50)
    axes[1].set_title('Audio Level vs Dynamic Range')
    axes[1].set_xlabel('Audio Level (dB)')
    axes[1].set_ylabel('Dynamic Range')

    plt.tight_layout()
    return fig

# -------------------------------------------------------------------
# MAIN STREAMLIT APP
# -------------------------------------------------------------------

st.title("📊 Data Quality Assurance Report")

st.markdown("""
This dashboard provides a comprehensive analysis of the data quality for text, image, and audio files 
retrieved from the **'formatted-zone'** bucket. The analysis identifies potential issues such as formatting errors, 
encoding problems, low-quality media, and inconsistencies that could affect downstream processing and model performance.
""")

if get_minio_client() is None:
    st.stop()

# --- Load Data ---
# We load all data at the start, and caching will ensure it only runs once.
df_text = load_data(bucket="formatted-zone", prefix="text/", analysis_func=analisi_text, file_type="text")
df_image = load_data(bucket="formatted-zone", prefix="images/", analysis_func=analisi_imagen, file_type="image")
df_audio = load_data(bucket="formatted-zone", prefix="audio/", analysis_func=analyze_audio_file, file_type="audio")


# --- Create Tabs ---
tab_text, tab_image, tab_audio = st.tabs(["Text Quality", "Image Quality", "Audio Quality"])

# -------------------------
# TEXT TAB
# -------------------------
with tab_text:
    st.header("Text Quality Analysis")
    if df_text.empty:
        st.warning("No text data found to display.")
    else:
        st.markdown("Analyzes text files for control characters, whitespace issues, special characters, and other formatting problems.")
        
        # Statistical Summary
        with st.expander("Show Statistical Summary", expanded=False):
            show_text_stats(df_text)
        
        # Main Visualizations
        st.subheader("Overall Quality Summary")
        st.pyplot(plot_text_summary(df_text))
        with st.expander("Interpretation of Text Visualizations"):
            st.markdown("""
            1.  **Control Characters**: Green means clean files, red indicates potential encoding issues. These invisible characters can cause problems in text processing.
            2.  **Lines with Spaces**: Distribution shows formatting consistency; peaks near 0 are ideal. Leading/trailing spaces on lines indicate formatting problems.
            3.  **Multiple Line Breaks**: Yes/No comparison reveals excessive whitespace issues. Multiple consecutive line breaks create inconsistent spacing.
            4.  **Empty Lines**: Normal distribution indicates proper paragraph structure. Too many empty lines (>100 per file) may indicate formatting issues.
            5.  **Special Characters**: Low counts (<20) are acceptable for most text processing tasks. High counts may indicate encoding issues or unusual characters.
            6.  **Typographic Quotes**: Should ideally be 0; these need ASCII replacement. Fancy quotes (like “ ”) can cause processing issues.
            7.  **Typographic Apostrophes**: Same as quotes, ideally 0 for clean text. Fancy apostrophes (like ‘ ’) need to be replaced with standard ones.
            8.  **Multiple Hyphens**: Yes indicates potential formatting artifacts. Multiple hyphens (--) may need to be replaced with em-dashes.
            9.  **Empty Text**: Critical issue if any files have this problem. Completely empty files indicate data quality problems.
            """)

        # Correlation
        st.subheader("Correlation Analysis")
        st.pyplot(plot_text_correlation(df_text))
        with st.expander("Interpretation of Correlation Analysis"):
            st.markdown("""
            **Correlation Matrix**: This heatmap identifies relationships between different text quality metrics:
            * **Positive correlations (red)**: Two metrics increase or decrease together. For example, if empty lines and special characters are positively correlated, files with more empty lines tend to have more special characters.
            * **Negative correlations (blue)**: One metric increases while the other decreases.
            * **Near-zero correlations**: Metrics are independent. This helps identify which quality aspects are unrelated.

            **Empty Lines vs Special Characters Scatter Plot**: This visualization reveals patterns between formatting issues and character problems:
            * **Cloud pattern**: Shows natural variation in the dataset.
            * **Positive trend**: Increasing empty lines associated with increasing special characters may indicate files with multiple formatting and encoding issues.
            * **Outliers**: Points far from the main cloud may represent problematic files that need attention.
            """)

        # Raw Data
        with st.expander("Show Raw Text Data"):
            st.dataframe(df_text)

# -------------------------
# IMAGE TAB
# -------------------------
with tab_image:
    st.header("Image Quality Analysis")
    if df_image.empty:
        st.warning("No image data found to display.")
    else:
        st.markdown("Analyzes images for dimensions, aspect ratio, brightness, contrast, saturation, sharpness, and overall quality.")

        with st.expander("Image Metrics Description", expanded=False):
            st.markdown("""
            - **`width` & `height`**: Image size in pixels.
            - **`total_pixels`**: Total resolution (width × height).
            - **`aspect_ratio`**: Ratio between width and height.
            - **`brillo` (Brightness)**: Average pixel intensity (0-255). `< 80` is dark, `> 200` is bright.
            - **`contraste` (Contrast)**: Standard deviation of pixels. `< 10` is very low contrast.
            - **`saturation`**: Color intensity. `< 30` is low saturation (muted/grayscale).
            - **`blur_score`**: Laplacian variance. High values = sharp image. `< 50` suggests blur.
            - **`noise`**: Detects "grainy" visual noise.
            - **`compression_artifacts`**: Detects degradation from excessive compression.
            - **`quality_score`**: Composite score (0-100) penalizing issues like blur, low contrast, and noise.
            """)
        
        # Statistical Summary
        with st.expander("Show Statistical Summary", expanded=False):
            show_image_stats(df_image)

        # Visualizations
        st.subheader("Brightness & Contrast Analysis")
        st.pyplot(plot_image_brightness_contrast(df_image))
        with st.expander("Interpretation"):
             st.markdown("The analysis shows that most images exhibit adequate clarity, as they are not excessively dark. Nevertheless, the overall brightness levels remain below the desired range. While avoiding dark imagery is beneficial, insufficient brightness can also impact visual quality.")

        st.subheader("Dimension & Aspect Ratio Analysis")
        st.pyplot(plot_image_dims(df_image))
        with st.expander("Interpretation"):
            st.markdown("""
            This analysis evaluates the **geometric consistency** of our image collection:
            1.  **Width/Height Distribution**: Shows if images have consistent dimensions. Overlapping bars are good.
            2.  **Aspect Ratio Distribution**: Reveals geometric proportions. A concentration around 1.0 means most images are square.
            3.  **Orientation Bar Chart**: Shows the dominant orientation (Square, Portrait, Landscape).
            4.  **Total Pixels Distribution**: Detects image resolution. Low pixel counts (<50,000) may be too small for embedding.
            """)

        st.subheader("Color & Saturation Analysis")
        st.pyplot(plot_image_color(df_image))
        with st.expander("Interpretation"):
            st.markdown("""
            This analysis evaluates **color quality**:
            1.  **Saturation Distribution**: Shows color intensity. Values below 30 (red line) are washed out. A curve centered around 50-70 is natural.
            2.  **Saturation Classification**: Categorizes images. Ideally, most should be "Normal".
            3.  **Color Channels**: Reveals color mode. A single bar at 3 (RGB) is ideal for consistency.
            """)

        st.subheader("Overall Image Quality Score Analysis")
        st.pyplot(plot_image_quality_score(df_image))
        with st.expander("Interpretation"):
            st.markdown("""
            This provides a **comprehensive quality assessment**:
            1.  **Quality Score Distribution**: Shows overall image quality (0-100). We want most images to be > 70 (red line).
            2.  **Quality Classification**: Categorizes images as Poor/Fair/Good/Excellent.
            3.  **Blur vs Quality Relationship**: Scatter plot checks if blurriness (low blur score) correlates with a low quality score.
            4.  **Correlation Matrix**: Heatmap identifies which metrics are related (e.g., contrast and quality).
            """)

        # Raw Data
        with st.expander("Show Raw Image Data"):
            st.dataframe(df_image)

# -------------------------
# AUDIO TAB
# -------------------------
with tab_audio:
    st.header("Audio Quality Analysis")
    if df_audio.empty:
        st.warning("No audio data found to display.")
    else:
        st.markdown("Analyzes audio files for duration, sample rate, volume, silence, and other technical quality metrics.")
        
        with st.expander("Audio Metrics Description", expanded=False):
            st.markdown("""
            - **`duration`**: Length of audio in seconds.
            - **`frame_rate`**: Sampling frequency (Hz). Higher rates (>44.1 kHz) provide better quality.
            - **`channels`**: Number of audio channels (1=mono, 2=stereo).
            - **`audio_level`**: RMS (average volume) in decibels. Ideal range is -12 to -18 dB.
            - **`peak`**: Maximum volume level. High peaks may indicate clipping.
            - **`noise_floor`**: Background noise level in dBFS. Lower values (<-60 dBFS) are cleaner.
            - **`dynamic_range`**: Difference between peak and average volume. Higher values are more natural.
            - **`silence_percent`**: Percentage of silence. High values (>30%) may be poor recordings.
            - **`filter_type`**: Detects if audio has low-pass, high-pass, or band-pass filters. "No filter" is preferred.
            """)
        
        # Statistical Summary
        with st.expander("Show Statistical Summary", expanded=False):
            show_audio_stats(df_audio)
        
        # Main Visualizations
        st.subheader("Overall Quality Summary")
        st.pyplot(plot_audio_summary(df_audio))
        with st.expander("Interpretation of Audio Visualizations"):
            st.markdown("""
            1.  **Duration Distribution**: Shows consistency in file lengths.
            2.  **Sample Rate Distribution**: A single peak is ideal for uniform audio fidelity.
            3.  **Channels Distribution**: Shows whether audio is mono (1) or stereo (2).
            4.  **Audio Level (RMS in dB)**: Represents the average volume. A tight cluster in the -12 to -18 dB range is good.
            5.  **Dynamic Range**: Higher values indicate better, more natural audio quality.
            6.  **Silence Percentage**: High percentages (>30%) may indicate poor recordings.
            7.  **Noise Floor (dBFS)**: Lower values (below -60 dBFS) suggest cleaner audio.
            8.  **Filter Type Distribution**: "No filter" is typically desired for natural audio.
            9.  **Sample Width Distribution**: Bit depth. 2 bytes (16-bit) is standard quality.
            """)

        # Correlation
        st.subheader("Correlation Analysis")
        st.pyplot(plot_audio_correlation(df_audio))
        with st.expander("Interpretation of Correlation Analysis"):
            st.markdown("""
            **Correlation Matrix**: This heatmap identifies relationships between different audio metrics:
            * **Positive correlations (red)**: Two metrics increase or decrease together (e.g., `audio_level` and `dynamic_range`).
            * **Negative correlations (blue)**: One metric increases while the other decreases.
            * **Near-zero correlations**: Metrics are independent.

            **Audio Level vs Dynamic Range Scatter Plot**: This visualization reveals patterns between volume and audio quality:
            * **Positive trend**: Increasing audio level associated with increasing dynamic range indicates good quality recordings.
            * **Negative trend or clustering**: May indicate compression artifacts or quality issues.
            """)

        # Raw Data
        with st.expander("Show Raw Audio Data"):
            st.dataframe(df_audio)