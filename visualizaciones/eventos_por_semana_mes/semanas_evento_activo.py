import pandas as pd

# Leer CSV
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv", low_memory=False)

# Asegurar formato datetime
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)
df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)

# Eliminar filas sin fechas válidas
df = df.dropna(subset=["id", "start_time_obj", "fecha_publicacion"])

# Lista para las filas expandidas por semana
rows = []

# Expandir cada evento por sus semanas activas
for _, row in df.iterrows():
    fecha_inicio = row["start_time_obj"]
    fecha_fin = row["fecha_publicacion"]
    
    # Generar rangos semanales desde el lunes de la semana de inicio hasta la semana de fin
    semanas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='W-MON')
    
    for semana in semanas:
        rows.append({
            "id": row["id"],
            "tipo_evento": row["type"],
            "provincia": row["provincia"],
            "semana": semana.strftime("%Y-%m-%d")  # Indica el lunes de la semana que le corresponde
        })

# Crear DataFrame final
df_semanas_activas = pd.DataFrame(rows)

# Exportar
df_semanas_activas.to_csv("visualizaciones/eventos_por_semana_mes/semanas_evento_activo.csv", index=False)
