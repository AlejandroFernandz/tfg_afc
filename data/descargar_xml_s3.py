import boto3
import os

# ================== CONFIGURACIÓN ==================

AWS_REGION = "eu-north-1"   # cámbiala si tu bucket está en otra región

BUCKET_NAME = "datos-dgt"
PREFIX = ""                # ej: "carpeta/xml/"
DESTINO_LOCAL = "data/xml_descargados"
# REDACTED_AWS_SECRET_ACCESS_KEY===========

os.makedirs(DESTINO_LOCAL, exist_ok=True)

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

paginator = s3.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=PREFIX):
    if "Contents" not in page:
        continue

    for obj in page["Contents"]:
        key = obj["Key"]

        if key.lower().endswith(".xml"):
            nombre_archivo = os.path.basename(key)
            ruta_local = os.path.join(DESTINO_LOCAL, nombre_archivo)

            print(f"Descargando {key}")
            s3.download_file(BUCKET_NAME, key, ruta_local)

print("✔ Descarga completada")
