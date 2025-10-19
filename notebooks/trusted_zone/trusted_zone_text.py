
import boto3
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
import unicodedata
from tqdm import tqdm
import sys
from pathlib import Path

# Añadir el directorio padre al path para imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from connection import Connection
from notebooks.trusted_zone.aStrategyTrusted import StrategyTrustedZone

new_bucket = "trusted-zone"
bucket_origen = "formatted-zone"
bucket_desti = "trusted-zone"
prefix_origen = "text/"


class TrustedZoneText(StrategyTrustedZone):
    
    def executar(self):
        minio_client = connection.Connection()
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")

        analysis = []
        paginator = minio_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket="formatted-zone", Prefix="text/"):
            for obj in tqdm(page.get("Contents", []), desc="Processant fitxers de text"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket="formatted-zone", Key=key)
                text = response["Body"].read().decode("utf-8", errors="ignore")
                analysis.append(self.analisi_text(text))
                

        df = pd.DataFrame(analysis)
        df.head()
        self.fer_plot_analysis(df)

        paginator = minio_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_origen, Prefix=prefix_origen):
            for obj in tqdm(page.get("Contents", []), desc="Processant fitxers de text"):
                key = obj["Key"]

                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket=bucket_origen, Key=key)
                text = response["Body"].read().decode("utf-8", errors="ignore")
                text_clean = unicodedata.normalize('NFKD', text)
                text_clean = ''.join(char for char in text_clean if unicodedata.category(char)[0] != 'C' or char in '\n\t')
                text_clean = re.sub(r"[ \t]+", " ", text_clean)          # Espacios y tabs múltiples → un espacio
                text_clean = re.sub(r"\s+", " ", text_clean)
                text_clean = re.sub(r"\n\s*\n\s*\n+", "\n\n", text_clean) # Múltiples líneas vacías → máximo 2
                lines = text_clean.split('\n')
                lines = [line.strip() for line in lines]
                text_clean = '\n'.join(lines)
                text_clean = re.sub(r'\n\s*\n+', '\n\n', text_clean)
                lines = [line for line in lines if line.strip()]  # Eliminar líneas vacías del medio también
                text_clean = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\"\'\-\+\=\%\&\$\/\@\#\*]', '', text_clean)
                text_clean = re.sub(r'["""]', '"', text_clean)      # Comillas tipográficas → comillas normales
                text_clean = re.sub(r"[‘’]", "'", text_clean)     # Apostrofes tipográficos → apostrofes normales
                text_clean = re.sub(r'-{2,}', '-', text_clean)      # Múltiples guiones → un guión
                text_clean = re.sub(r'\s+([.!?;:])', r'\1', text_clean)  # Eliminar espacios antes de puntuación
                text_clean = re.sub(r'([.!?;:])\s*', r'\1 ', text_clean) # Un espacio después de puntuación
                text_clean = text_clean.strip()
                if not text_clean.strip():
                    print(f"Advertencia: {filename} quedó vacío después del procesamiento")
                    continue
                new_key = f"text/{filename}"
                minio_client.put_object(
                    Bucket=bucket_desti,
                    Key=new_key,
                    Body=text_clean.encode("utf-8")
                )

        analysis_2= []
        paginator = minio_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket="trusted-zone", Prefix="text/"):
            for obj in tqdm(page.get("Contents", []), desc="Processant fitxers de text"):
                key = obj["Key"]
                filename = key.split("/")[-1]
                response = minio_client.get_object(Bucket="trusted-zone", Key=key)
                text = response["Body"].read().decode("utf-8", errors="ignore")
                analysis_2.append(analisi_text(text))
                
        df_2 = pd.DataFrame(analysis_2)
        df_2.head()
        self.fer_plot_analysis(df_2)


    def fer_plot_analysis(df):
        plt.figure(figsize=(5, 3))
        plt.plot(df['problems_lineas_vacias'], label='Líneas vacías')
        plt.plot(df['problems_caracteres_especiales'], label='Caracteres especiales')
        plt.legend()
        plt.show()

    def analisi_text(text):
        problemas = {}

        control_chars = [c for c in text if unicodedata.category(c)[0] == 'C' and c not in '\n\t']
        problemas["caracteres_control"] = len(control_chars)

        lineas_con_espacios = [line for line in text.splitlines() if line.startswith(" ") or line.endswith(" ")]
        problemas["lineas_con_espacios"] = len(lineas_con_espacios)

        saltos_multiples = bool(re.search(r"\n\s*\n\s*\n+", text))
        problemas["saltos_multiples"] = saltos_multiples

        lineas_vacias = [line for line in text.splitlines() if not line.strip()]
        problemas["lineas_vacias"] = len(lineas_vacias)

        caracteres_invalidos = re.findall(r"[^\w\s\.\,\;\:\!\?\(\)\[\]\"\'\-\+\=\%\&\$\/\@\#\*]", text)
        problemas["caracteres_especiales"] = len(caracteres_invalidos)

        comillas_tipograficas = re.findall(r"[“”«»]", text)
        apostrofes_tipograficos = re.findall(r"[‘’]", text)
        problemas["comillas_tipograficas"] = len(comillas_tipograficas)
        problemas["apostrofes_tipograficos"] = len(apostrofes_tipograficos)

        guiones_multiples = bool(re.search(r"-{2,}", text))
        problemas["guiones_multiples"] = guiones_multiples

        texto_vacio = not text.strip()
        problemas["texto_vacio"] = texto_vacio

        return{
            "problems_control_caracters": problemas["caracteres_control"],
            "problems_lineas_con_espacios": problemas["lineas_con_espacios"],
            "problems_saltos_multiples": problemas["saltos_multiples"],
            "problems_lineas_vacias": problemas["lineas_vacias"],
            "problems_caracteres_especiales": problemas["caracteres_especiales"],
            "problems_comillas_tipograficas": problemas["comillas_tipograficas"],
            "problems_apostrofes_tipograficos": problemas["apostrofes_tipograficos"],
            "problems_guiones_multiples": problemas["guiones_multiples"],
            "problems_texto_vacio": problemas["texto_vacio"]
        }