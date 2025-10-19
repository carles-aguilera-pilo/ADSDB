
import boto3
import os
from dotenv import load_dotenv
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import math
import pandas as pd
from pydub import AudioSegment
from pydub.silence import detect_silence
import matplotlib.pyplot as plt
import pandas as pd
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import split_on_silence, detect_silence
import io
from tqdm import tqdm
import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from minio_connection import MinIOConnection
from src.trusted_zone.aStrategyTrusted import StrategyTrustedZone

new_bucket = "trusted-zone"
bucket_origen = "formatted-zone"
prefix_origen = "audio/"
bucket_desti = "trusted-zone"
freq_final = 48000

class TrustedZoneAudio(StrategyTrustedZone):
    
    def executar(self):
        
        global bucket_origen
        global prefix_origen
        global bucket_desti
        global freq_final
        global new_bucket
        minio_client = MinIOConnection()
        self.provar_existencia_bucket(new_bucket, minio_client)
        self.fer_analysis(minio_client, "formatted-zone")
        paginator = minio_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_origen, Prefix=prefix_origen):
            for obj in tqdm(page.get("Contents", []), desc="Processant àudios"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket=bucket_origen, Key=key)
                audio_data = response["Body"].read()
                try:
                    audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
                except Exception as e:
                    print(f"Error amb {filename}: {e}")
                    continue
                audio = audio.set_frame_rate(freq_final)
                silence_threshold = -50
                silence_duration = 500
                silence_ranges = detect_silence(audio, min_silence_len=silence_duration, silence_thresh=silence_threshold)
                if silence_ranges:
                    if silence_ranges[-1][1] > len(audio) - 1000:  # If the last silence is near the end
                        audio = audio[:silence_ranges[-1][0]]
                    if silence_ranges[0][0] < 1000:
                        audio = audio[silence_ranges[0][1]:]
                audio = normalize(audio)
                audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
                audio = audio.high_pass_filter(80)  # Hz
                audio = audio.low_pass_filter(16000)
                audio = normalize(audio)
                audio = audio + 2
                buffer = io.BytesIO()
                audio.export(buffer, format="mp3", bitrate="192k")
                buffer.seek(0)
                new_key = f"audio/{filename}"
                self.put_object(minio_client, bucket_desti, new_key, buffer)
        self.fer_analysis(minio_client, "trusted-zone")
        
    def detectar_filtro(self, centroid, rolloff, ratio):
            if centroid < 1500 and rolloff < 3000 and ratio < 0.5:
                return "Low-pass filter"
            elif centroid > 4000 and rolloff > 6000 and ratio > 1.5:
                return "High-pass filter"
            elif 1500 <= centroid <= 4000 and 3000 <= rolloff <= 6000 and 0.5 <= ratio <= 1.5:
                return "Band-pass filter"
            else:
                return "No filter"
            
    def analyze_audio_file(self, audio_bytes):
            audio = AudioSegment.from_file(BytesIO(audio_bytes))
            duration = len(audio) / 1000        # DURATION IN SECONDS.
            frame_rate = audio.frame_rate       # SAMPLING FREQUENCY.
            channels = audio.channels           # CHANNELS.
            sample_width = audio.sample_width   # SAMPLING WIDTH IN BYTES. IF WE WANT IT IN BITS MULTIPLY BY 8.
            rms = audio.rms
            audio_level = 20 * math.log10(rms) if rms > 0 else -float('inf')    #RMS CONVERSION TO DECIBELS.
            peak = audio.max                                                    # PEAK VOLUME.
            noise_floor = audio.dBFS                                            # NOISE FLOOR.
            silence_ranges = detect_silence(audio, min_silence_len=500, silence_thresh=-50)     # DETECT SILENCES.
            total_silence_duration = sum(end - start for start, end in silence_ranges) / 1000   # CONVERT TO SECONDS.
            silence_percent = (total_silence_duration / duration) * 100 if duration > 0 else 0  # PERCENTAGE OF SILENCE.
            dynamic_range = peak - rms
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)                 # GET SAMPLES.
            
            if channels == 2:                                                                   # IF CHANEL IS ESTEREO WE CONVERT TO MONO.
                samples = samples.reshape((-1, 2))
                samples = np.mean(samples, axis=1)
                
            samples /= np.iinfo(audio.array_type).max                                          # NORMALIZE SAMPLES.
            sr = audio.frame_rate                                                               # GET SAMPLING RATE.
            centroid = librosa.feature.spectral_centroid(y=samples, sr=sr)
            bandwidth = librosa.feature.spectral_bandwidth(y=samples, sr=sr)
            rolloff = librosa.feature.spectral_rolloff(y=samples, sr=sr, roll_percent=0.95)
            S = np.abs(librosa.stft(samples))
            freqs = librosa.fft_frequencies(sr=sr)
            low_energy = np.sum(S[(freqs > 0) & (freqs < 1000)])
            high_energy = np.sum(S[freqs > 5000])
            ratio = high_energy / (low_energy + 1e-9)
            # GLOBAL AVERAGES
            centroid_mean = np.mean(centroid)
            bandwidth_mean = np.mean(bandwidth)
            rolloff_mean = np.mean(rolloff)
            # FILTER DETECTION
            filter_type = self.detectar_filtro(centroid_mean, rolloff_mean, ratio)
            return {
                "duration": duration,
                "frame_rate": frame_rate,
                "channels": channels,
                "sample_width": sample_width,
                "audio_level": audio_level,
                "peak": peak,
                "noise_floor": noise_floor,
                "silence_ranges": silence_ranges,
                "total_silence_duration": total_silence_duration,
                "silence_percent": silence_percent,
                "dynamic_range": dynamic_range,
                "filter_type": filter_type
            }
            
    
    def make_plot_analysis(self, df):
        primeros_dos = df.sample(n=2, random_state=42)
        fig, axes = plt.subplots(2, 2, figsize=(5, 3))
        fig.suptitle('Comparación de los dos primeros archivos de audio', fontsize=16)
        axes[0,0].bar(['Archivo 1', 'Archivo 2'], primeros_dos['peak'])
        axes[0,0].set_title('Peak Frequency')
        axes[0,0].set_ylabel('%')
        axes[0,1].bar(['Archivo 1', 'Archivo 2'], primeros_dos['frame_rate'])
        axes[0,1].set_title('Frame Rate')
        axes[0,1].set_ylabel('Hz')
        axes[1,0].bar(['Archivo 1', 'Archivo 2'], primeros_dos['audio_level'])
        axes[1,0].set_title('Audio Level (dB)')
        axes[1,0].set_ylabel('dB')
        axes[1,1].bar(['Archivo 1', 'Archivo 2'], primeros_dos['filter_type'])
        axes[1,1].set_title('Filter Type')
        axes[1,1].set_ylabel('%')
        plt.tight_layout()
        plt.show()
    
    def provar_existencia_bucket(self, bucket_name, minio_client):
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")
            
            
    def fer_analysis(self, minio_client, bucket):
        analysis = []
        paginator = minio_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix="audio/"):
            for obj in tqdm(page.get("Contents", []), desc="Processant àudios"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket=bucket, Key=key)
                audio_data = response["Body"].read()
                analysis.append(self.analyze_audio_file(audio_data))
        df = pd.DataFrame(analysis)
        df.head()
        self.make_plot_analysis(df)
    
    def put_object(self, minio_client, bucket, key, buffer):
        minio_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=buffer
        )