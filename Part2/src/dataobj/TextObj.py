import re
import unicodedata
from src.dataobj.ADataObj import ADataObj
from src.minio_connection import MinIOConnection
from src.chroma_connection import ChromaConnection
from src.embedder import embed_text
import os
import io

class TextObj(ADataObj):
    def __init__(self, key, text_data):
        self.path_prefix = key.split("/")[0]
        split_filename = os.path.splitext(key.split("/")[1])
        self.filename = split_filename[0]
        self.extension = split_filename[1].lower()
        self.texts = [text_data.decode("utf-8", errors="ignore")]
        self.embeddings = []

    def save(self, bucket_destination, chromadb: bool=False, collection_name: str=None):        
        for i, text in enumerate(self.texts):
            buffer = io.BytesIO(text.encode('utf-8'))
            key = self.path_prefix + "/" + self.filename + f"_{i}" + self.extension
            minio_client = MinIOConnection()
            minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=key)
            minio_client.head_object(Bucket=bucket_destination, Key=key)
        
            if chromadb:
                chroma_client = ChromaConnection()
                collection_str = f"text_{collection_name}"
                collection = chroma_client.get_or_create_collection(name=collection_str)
                collection.add(
                    documents=[text],
                    embeddings=[self.embeddings[i]],
                    ids=[key]
                )

    def format(self):
        for text in self.texts:
            buffer = io.BytesIO(text.encode('utf-8'))
            self.extension = ".txt"

    def clean(self):
        for i, text in enumerate(self.texts):
            text = unicodedata.normalize('NFKD', text)
            text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\s+", " ", text)
            text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
            lines = text.split('\n')
            lines = [line.strip() for line in lines]
            text = '\n'.join(lines)
            text = re.sub(r'\n\s*\n+', '\n\n', text)
            lines = [line for line in lines if line.strip()]
            text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\"\'\-\+\=\%\&\$\/\@\#\*]', '', text)
            text = re.sub(r'["""]', '"', text)
            text = re.sub(r"[‘’]", "'", text)
            text = re.sub(r'-{2,}', '-', text)
            text = re.sub(r'\s+([.!?;:])', r'\1', text)
            text = re.sub(r'([.!?;:])\s*', r'\1 ', text)
            text = text.strip()
            if not text:
                print(f"Advertencia: {self.filename} quedó vacío después del procesamiento")
            
            self.texts[i] = text


    def embed(self):
        for _, text in enumerate(self.texts):
            parts = self.partition_text(text)
            self.texts = parts
            for _, part in enumerate(parts):
                embedding = embed_text(part)
                self.embeddings.append(embedding)

    def partition_text(self, text):
        parts = text.split('.')
        valid_phrases = []
        for phrase in parts:
            clean_phrase = phrase.strip()
            if clean_phrase:
                final_phrase = clean_phrase + "."
                if len(final_phrase) <= 100:
                    valid_phrases.append(final_phrase)
        return valid_phrases
