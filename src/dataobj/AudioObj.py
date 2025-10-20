from abc import ABC, abstractmethod
from src.dataobj.ADataObj import ADataObj
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import split_on_silence, detect_silence
from src.minio_connection import MinIOConnection
import os
import io

class AudioObj(ADataObj):

    def __init__(self, key, audio_data):
        self.path_prefix = key.split("/")[0]
        split_filename = os.path.splitext(key.split("/")[1])
        self.filename = split_filename[0]
        self.extension = split_filename[1].lower()
        self.audio = AudioSegment.from_file(io.BytesIO(audio_data))

    def save(self, bucket_destination):        
        buffer = io.BytesIO()
        self.audio.export(buffer, format=self.extension[1:])
        buffer.seek(0)

        key = self.path_prefix + "/" + self.filename + self.extension
        minio_client = MinIOConnection()
        minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=key)
        minio_client.head_object(Bucket=bucket_destination, Key=key) # Checks if the file was uploaded successfully and throws an exception otherwise.
   
    def format(self):
        buffer = io.BytesIO()
        self.audio.export(buffer, format="mp3")
        buffer.seek(0)
        self.audio = AudioSegment.from_file(buffer)
        self.extension = ".mp3"

    def clean(self):
        self.audio = self.audio.set_frame_rate(48000)
        
        # 2. Clean silences at the beginning and end
        # Detect and remove long silences at the beginning and end
        silence_threshold = -50  # dB
        silence_duration = 500   # ms
        
        # Detect silence
        silence_ranges = detect_silence(self.audio, min_silence_len=silence_duration, silence_thresh=silence_threshold)
        
        if silence_ranges:
            # Remove silence at the end
            if silence_ranges[-1][1] > len(self.audio) - 1000:  # If the last silence is near the end
                self.audio = self.audio[:silence_ranges[-1][0]]
            
            # Remove silence at the beginning
            if silence_ranges[0][0] < 1000:  # If the first silence is near the beginning
                self.audio = self.audio[silence_ranges[0][1]:]
        
        # Normalize volume (equalize levels)
        self.audio = normalize(self.audio)
        
        # Dynamic compression to balance levels
        self.audio = compress_dynamic_range(self.audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        
        # Noise filter (reduce background noise)
        # Apply a very soft high-pass filter to eliminate low-frequency noise
        self.audio = self.audio.high_pass_filter(80)  # Hz
        
        # Noise filter (reduce high-frequency noise)
        # Apply a low-pass filter to eliminate high-frequency noise
        self.audio = self.audio.low_pass_filter(16000)  # Hz
        
        # Final volume normalization
        self.audio = normalize(self.audio)
        
        # Final gain adjustment (optional: +2dB for more presence)
        self.audio = self.audio + 2
