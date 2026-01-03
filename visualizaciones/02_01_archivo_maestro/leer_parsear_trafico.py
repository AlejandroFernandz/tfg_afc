import os
import sys
import io
import xml.etree.ElementTree as ET

import boto3
import pandas as pd
from tqdm import tqdm

# Añadir la carpeta raíz del proyecto al path (dos niveles arriba)
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(RAIZ_PROYECTO)

from app.parsing import parse_datex  # noqa: E402


# ==============================
# CONFIG
BUCKET = "datos-dgt"
PREFIX = "dgt_2025"  # ajusta si tus claves tienen otro patrón

# Credenciales: mejor por entorno (recomendado)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or "AKIA4SZHNVFRBQQVFQFT"
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or "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"

OUT_DIR = "output"
OUT_CSV_FINAL = os.path.join(OUT_DIR, "archivo_maestro_trafico.csv")

# MODO PRUEBA: crea 1 CSV pequeño con N filas para validar formato
MODO_PRUEBA = True
MAX_FILAS_PRUEBA = 5000  # total filas máximas en el CSV de prueba
OUT_CSV_PRUEBA = os.path.join(OUT_DIR, "TEST_archivo_maestro_trafico.csv")
# ==============================


def normalizar_columna_serie(s: pd.Series) -> pd.Series:
    """Normalización rápida vectorizada, equivalente a tu función original."""
    s = s.astype("string")
    s = s.str.strip().str.lower()
    s = (
        s.str.replace("á", "a", regex=False)
         .str.replace("é", "e", regex=False)
         .str.replace("í", "i", regex=False)
         .str.replace("ó", "o", regex=False)
         .str.replace("ú", "u", regex=False)
         .str.replace("ü", "u", regex=False)
         .str.replace("ñ", "n", regex=False)
    )

    # "prov, algo" -> "Algo Prov" (misma lógica que antes)
    mask = s.str.contains(",", na=False)
    if mask.any():
        partes = s[mask].str.split(",", n=1, expand=True)
        s.loc[mask] = partes[1].str.strip() + " " + partes[0].str.strip()

    return s.str.title()


def listar_xmls_s3(s3_client, bucket: str, prefix: str) -> list[str]:
    """Lista TODOS los XML con paginación (evita el límite de 1000)."""
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    xml_files = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj.get("Key", "")
            if key.endswith(".xml"):
                xml_files.append(key)

    xml_files.sort()  # consistencia
    return xml_files


def extraer_publication_time(xml_bytes: bytes, key: str) -> pd.Timestamp | None:
    """Extrae publicationTime de Datex2."""
    try:
        root = ET.fromstring(xml_bytes)
        ns = {"com": "http://datex2.eu/schema/3/common"}
        node = root.find(".//com:publicationTime", namespaces=ns)
        if node is None or not node.text:
            print(f"[WARN] No publicationTime en {key}")
            return None
        return pd.to_datetime(node.text, utc=True)
    except Exception as e:
        print(f"[WARN] No se pudo leer publicationTime en {key}: {e}")
        return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise RuntimeError(
            "Faltan credenciales AWS. Define AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY "
            "como variables de entorno (recomendado) o ponlas en el script."
        )

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    xml_files = listar_xmls_s3(s3, BUCKET, PREFIX)
    print(f"Total XML encontrados con prefix '{PREFIX}': {len(xml_files)}")

    output_path = OUT_CSV_PRUEBA if MODO_PRUEBA else OUT_CSV_FINAL

    # Borrar output si existe para no duplicar
    if os.path.exists(output_path):
        os.remove(output_path)

    header_written = False
    total_rows = 0

    columnas_a_normalizar = ["provincia", "locality", "type"]

    for key in tqdm(xml_files, desc="Procesando XMLs"):
        if MODO_PRUEBA and total_rows >= MAX_FILAS_PRUEBA:
            break

        # Descargar XML
        try:
            obj = s3.get_object(Bucket=BUCKET, Key=key)
            xml_content = obj["Body"].read()
        except Exception as e:
            print(f"[WARN] Error descargando {key}: {e}")
            continue

        # publicationTime
        publication_time = extraer_publication_time(xml_content, key)
        if publication_time is None:
            continue

        # Parsear Datex
        try:
            with io.BytesIO(xml_content) as temp_file:
                df = parse_datex(temp_file)
        except Exception as e:
            print(f"[WARN] Error parseando {key}: {e}")
            continue

        # Añadir fecha_publicacion
        df["fecha_publicacion"] = publication_time

        # Normalizar si existen columnas
        for col in columnas_a_normalizar:
            if col in df.columns:
                df[col] = normalizar_columna_serie(df[col])

        # En prueba, recortar para no pasar MAX_FILAS_PRUEBA
        if MODO_PRUEBA:
            remaining = MAX_FILAS_PRUEBA - total_rows
            if remaining <= 0:
                break
            if len(df) > remaining:
                df = df.iloc[:remaining].copy()

        # Escribir incremental al ÚNICO CSV final
        df.to_csv(output_path, mode="a", index=False, header=not header_written)
        header_written = True
        total_rows += len(df)

    print(f"\nCSV generado: {output_path}")
    print(f"Filas escritas: {total_rows}")

    # Validación rápida (solo para comprobar formato)
    try:
        sample = pd.read_csv(output_path, nrows=10)
        print("\nMuestra (10 filas):")
        print(sample)
        print("\nColumnas:")
        print(list(sample.columns))
    except Exception as e:
        print(f"[WARN] No pude leer el CSV de salida para validar: {e}")


if __name__ == "__main__":
    main()
