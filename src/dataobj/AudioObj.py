from src.dataobj.ADataObj import ADataObj
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import detect_silence
from transformers import ClapModel, ClapProcessor
from src.minio_connection import MinIOConnection
from src.chroma_connection import ChromaConnection
import librosa
import torch
import os
import io

TARGET_SAMPLE_RATE = 48000

class AudioObj(ADataObj):
    _model_id = "laion/clap-htsat-unfused"
    _model = ClapModel.from_pretrained(_model_id)
    _processor = ClapProcessor.from_pretrained(_model_id)

    def __init__(self, key, audio_data):
        self.path_prefix = key.split("/")[0]
        split_filename = os.path.splitext(key.split("/")[1])
        self.filename = split_filename[0]
        self.extension = split_filename[1].lower()
        self.audio_bytes = audio_data
        self.audio = AudioSegment.from_file(io.BytesIO(audio_data))
        self.embeddings = None

    def save(self, bucket_destination, chromadb: bool=False):        
        buffer = io.BytesIO()
        self.audio.export(buffer, format=self.extension[1:])
        buffer.seek(0)

        key = self.path_prefix + "/" + self.filename + self.extension
        minio_client = MinIOConnection()
        minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=key)
        minio_client.head_object(Bucket=bucket_destination, Key=key)
        if chromadb:
            chroma_client = ChromaConnection()
            collection_name = self.extension[1:] + "_collection"
            collection = chroma_client.get_or_create_collection(name=collection_name)
            collection.add(
                ids=[key],
                embeddings=[self.embeddings],
            )
   
    def format(self):
        buffer = io.BytesIO()
        self.audio.export(buffer, format="mp3")
        buffer.seek(0)
        self.audio = AudioSegment.from_file(buffer)
        self.extension = ".mp3"

    def clean(self):
        self.audio = self.audio.set_frame_rate(TARGET_SAMPLE_RATE)
        self.audio = self.audio.set_channels(1)
        silence_threshold = -50
        silence_duration = 500
        
        silence_ranges = detect_silence(self.audio, min_silence_len=silence_duration, silence_thresh=silence_threshold)
        
        if silence_ranges:
            if silence_ranges[-1][1] > len(self.audio) - 1000:
                self.audio = self.audio[:silence_ranges[-1][0]]
            
            if silence_ranges[0][0] < 1000:
                self.audio = self.audio[silence_ranges[0][1]:]
        
        self.audio = normalize(self.audio)
        self.audio = compress_dynamic_range(self.audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        self.audio = self.audio.high_pass_filter(80)
        self.audio = self.audio.low_pass_filter(16000)
        self.audio = normalize(self.audio)
        self.audio = self.audio + 2
    
    def embed(self):
        audio_waveform, _ = librosa.load(
            io.BytesIO(self.audio_bytes), 
            sr=TARGET_SAMPLE_RATE, 
            mono=True
        )
        inputs = self._processor(
            audio=audio_waveform, 
            sampling_rate=TARGET_SAMPLE_RATE, 
            return_tensors="pt"
        )
        with torch.no_grad():
            audio_features = self._model.get_audio_features(**inputs)

        self.embeddings = audio_features[0].numpy().tolist()
