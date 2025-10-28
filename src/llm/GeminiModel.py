from src.llm import ILLM
from google import genai
from google.genai import types

class GeminiModel(ILLM): # type: ignore
    def __init__(self, api_key, model):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def query(self, text, files_paths):
        uploaded_files = []
        for f in files_paths:
            uploaded_files.append(self._client.files.upload(file=files_paths))

        response = self._instance.models.generate_content(
            model=self._model,
            contents=[text] + uploaded_files
        )

        return response

