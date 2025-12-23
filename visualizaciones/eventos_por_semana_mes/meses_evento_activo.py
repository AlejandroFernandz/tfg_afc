### EJECUTAR ###

import pandas as pd

# Leer CSV
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv", low_memory=False)

# Asegurar formato datetime
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)
df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)

# Eliminar filas con fechas nulas
df = df.dropna(subset=["id", "start_time_obj", "fecha_publicacion"])

# Filas expandidas: para cada fila:
# Toma la fecha de inicio y de fin de cada evento
# Genera una lista con todos los primeros dias de los meses que haya entre esas fechas
# Para cada mes en ese rango, genera una fila con: id, tipo, provincia y mes(YYYY-MM)
rows = []

for idx, row in df.iterrows():
    fecha_inicio = row["start_time_obj"]
    fecha_fin = row["fecha_publicacion"]
    meses = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='MS')  # Meses

    for mes in meses:
        rows.append({
            "id": row["id"],
            "tipo_evento": row["type"],
            "provincia": row["provincia"],
            "mes": mes.strftime("%Y-%m")
        })

# Convertir a un dataframe que tiene una fila por evento por mes activo
df_meses_activos = pd.DataFrame(rows)

# Exportar para Power BI
df_meses_activos.to_csv("visualizaciones/eventos_por_semana_mes/meses_evento_activo.csv", index=False)
