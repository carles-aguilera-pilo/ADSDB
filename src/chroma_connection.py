import boto3
import os
from dotenv import load_dotenv
import chromadb

class ChromaConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        load_dotenv()
        chroma_host = os.getenv("CHROMADB_ENDPOINT", "localhost")
        chroma_port = os.getenv("CHROMADB_PORT", 8000)
        try:
            chroma_port = int(chroma_port)
        except Exception:
            chroma_port = 8000
        self._client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        self._initialized = True

    def get_or_create_collection(self, name):
        collection = self._client.get_or_create_collection(name=name)
        return collection

    def query(self, collection_name, query_embeddings, n_results=5):
        collection = self.get_or_create_collection(name=collection_name)
        print("Embeddings for query:")
        print(query_embeddings)
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
        return results