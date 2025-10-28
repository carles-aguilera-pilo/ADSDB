from src.llm.ILLM import ILLM
from google import genai
from google.genai import types
import io

class GeminiModel(ILLM):
    def __init__(self, api_key, model):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def query(self, text, files): # type: ignore
        uploaded_files = []
        print(files)
        for f in files:
            uploaded_files.append(self._client.files.upload(file=f))

        response = self._client.models.generate_content(
            model=self._model,
            contents=[text] + uploaded_files
        )

        return response

