from src.dataobj.ADataObj import ADataObj
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import detect_silence
from src.minio_connection import MinIOConnection
from src.chroma_connection import ChromaConnection
from src.embedder import embed_audio
import os
import io

TARGET_SAMPLE_RATE = 48000

class AudioObj(ADataObj):
    def __init__(self, key, audio_data):
        self.path_prefix = key.split("/")[0]
        split_filename = os.path.splitext(key.split("/")[1])
        self.filename = split_filename[0]
        self.extension = split_filename[1].lower()
        self.extension_multimodal = "multimodal_collection_audios"
        self.audio_bytes = audio_data
        self.audio = AudioSegment.from_file(io.BytesIO(audio_data))
        self.embeddings = None

    def save(self, bucket_destination, chromadb: bool=False, collection_name: str=None):        
        buffer = io.BytesIO()
        self.audio.export(buffer, format=self.extension[1:])
        buffer.seek(0)

        key = self.path_prefix + "/" + self.filename + self.extension
        minio_client = MinIOConnection()
        minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=key)
        minio_client.head_object(Bucket=bucket_destination, Key=key)
        if chromadb:
            chroma_client = ChromaConnection()
            collection_name = f"audio_{collection_name}"
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
        key = self.path_prefix + "/" + self.filename + self.extension
        self.embeddings = embed_audio(key).cpu().tolist()
