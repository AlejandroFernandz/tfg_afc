# Creo que solo coge 1000 archivos, por lo que llega solo hasta la semana del 21 de abril

# Distribucion de tipos de eventos
import sys
import os

# Añadir la carpeta raíz del proyecto al path (dos niveles arriba)
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(RAIZ_PROYECTO)

import boto3
import io
import xml.etree.ElementTree as ET
import pandas as pd
from tqdm import tqdm
from app.parsing import parse_datex

# ------------------------------
# Función de normalización del texto para nombres de provincias
def normalizar_texto(valor):
    if pd.isna(valor):
        return None
    texto = (
        str(valor)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ñ", "n")
    )
    if "," in texto:
        partes = [p.strip() for p in texto.split(",")]
        texto = " ".join(reversed(partes))
    return texto.title()
# ------------------------------

# Parámetros de conexión
BUCKET = "datos-dgt"
# Meter aqui las claves de Onenote

# Crear cliente S3
s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

# Filtrar con prefix: solo archivos de abril 2025, por ejemplo
response = s3.list_objects_v2(Bucket=BUCKET, Prefix="dgt_2025")
xml_files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".xml")]

# Dataset acumulado
all_events = []

# Recorrer archivos
for key in tqdm(xml_files, desc="Procesando XMLs"):
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    xml_content = obj["Body"].read()

    # Extraer publicationTime
    try:
        root = ET.fromstring(xml_content)
        ns = { "com": "http://datex2.eu/schema/3/common" }
        pub_time_str = root.find(".//com:publicationTime", namespaces=ns).text
        publication_time = pd.to_datetime(pub_time_str, utc=True)
    except Exception as e:
        print(f"No se pudo leer publicationTime en {key}: {e}")
        continue

    # Parsear contenido y normalizar
    with io.BytesIO(xml_content) as temp_file:
        try:
            df = parse_datex(temp_file)
            df["fecha_publicacion"] = publication_time

            # Normalizar columnas clave si existen
            columnas_a_normalizar = ["provincia", "locality", "type"]
            for col in columnas_a_normalizar:
                if col in df.columns:
                    df[col] = df[col].apply(normalizar_texto)

            all_events.append(df)
        except Exception as e:
            print(f"Error procesando {key}: {e}")

# Unir en un solo DataFrame
df_all_events = pd.concat(all_events, ignore_index=True)
print("Numero total de eventos sin eliminar duplicados:", len(df_all_events))

# Guardar CSV completo con eventos de todos los días (repetidos si siguen activos)
df_all_events.to_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas.csv", index=False)
