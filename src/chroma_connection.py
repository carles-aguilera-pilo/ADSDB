import boto3
import os
from dotenv import load_dotenv
import chromadb

class ChromaConnection:
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            load_dotenv()
            chroma_host = os.getenv("CHROMADB_ENDPOINT")
            chroma_port = os.getenv("CHROMADB_PORT")
            cls._instance = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        return cls._instance