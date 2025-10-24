from abc import ABC, abstractmethod
import re
import unicodedata
from src.dataobj.ADataObj import ADataObj
from src.minio_connection import MinIOConnection
from src.chroma_connection import ChromaConnection
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import os
import io
import chromadb
from chromadb.utils.data_loaders import TextLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction

_default_ef = DefaultEmbeddingFunction()
embedding_function = OpenCLIPEmbeddingFunction()

class TextObj(ADataObj):
    def __init__(self, key, text_data):
        self.path_prefix = key.split("/")[0]
        split_filename = os.path.splitext(key.split("/")[1])
        self.filename = split_filename[0]
        self.extension = split_filename[1].lower()
        self.extension_multimodal = "multimodal_collection_text"
        self.text = text_data.decode("utf-8", errors="ignore")
        self.embeddings = None
        self.multimodal_embeddings = None

    def save(self, bucket_destination, chromadb: bool=False):        
        buffer = io.BytesIO(self.text.encode('utf-8'))

        key = self.path_prefix + "/" + self.filename + self.extension
        minio_client = MinIOConnection()
        minio_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_destination, Key=key)
        minio_client.head_object(Bucket=bucket_destination, Key=key)
        if chromadb:
            chroma_client = ChromaConnection()
            collection_name = self.extension[1:] + "_collection"
            collection = chroma_client.get_or_create_collection(name=collection_name)
            
            collection.add(
                documents=[self.text],
                embeddings=[self.embeddings],
                ids=[key]
            )
            
            # FOR THE TASK 2
            collection_multimodal = chroma_client.get_or_create_collection(name=self.extension_multimodal)
            collection_multimodal.add(
                ids=[key],
                embeddings=[self.multimodal_embeddings],
                metadatas=[{"bucket": bucket_destination, "key": key, "type": "text"}]
            )

    def format(self):
        buffer = io.BytesIO(self.text.encode('utf-8'))
        self.extension = ".txt"

    def clean(self):
        self.text = unicodedata.normalize('NFKD', self.text)
        self.text = ''.join(char for char in self.text if unicodedata.category(char)[0] != 'C' or char in '\n\t')
        self.text = re.sub(r"[ \t]+", " ", self.text)          # Espacios y tabs múltiples → un espacio
        self.text = re.sub(r"\s+", " ", self.text)
        self.text = re.sub(r"\n\s*\n\s*\n+", "\n\n", self.text) # Múltiples líneas vacías → máximo 2
        lines = self.text.split('\n')
        lines = [line.strip() for line in lines]
        self.text = '\n'.join(lines)
        self.text = re.sub(r'\n\s*\n+', '\n\n', self.text)
        lines = [line for line in lines if line.strip()]  # Eliminar líneas vacías del medio también
        self.text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\"\'\-\+\=\%\&\$\/\@\#\*]', '', self.text)
        self.text = re.sub(r'["""]', '"', self.text)      # Comillas tipográficas → comillas normales
        self.text = re.sub(r"[‘’]", "'", self.text)     # Apostrofes tipográficos → apostrofes normales
        self.text = re.sub(r'-{2,}', '-', self.text)      # Múltiples guiones → un guión
        self.text = re.sub(r'\s+([.!?;:])', r'\1', self.text)  # Eliminar espacios antes de puntuación
        self.text = re.sub(r'([.!?;:])\s*', r'\1 ', self.text) # Un espacio después de puntuación
        self.text = self.text.strip()
        if not self.text.strip():
            print(f"Advertencia: {self.filename} quedó vacío después del procesamiento")

    def embed(self):
        self.embeddings = _default_ef([self.text])[0]
        
    def multimodal_embed(self):
        embedd = embedding_function([self.text])[0]
        if hasattr(embedd, "tolist"):
            embedd = embedd.tolist()
        self.multimodal_embeddings = embedd



