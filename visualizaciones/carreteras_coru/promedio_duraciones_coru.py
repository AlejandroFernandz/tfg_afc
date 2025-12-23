import pandas as pd

# Cargar la base
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv", low_memory=False)

# Convertir fechas
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)
df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)

# Filtrar eventos válidos
df = df.dropna(subset=["id", "provincia", "road", "start_time_obj", "fecha_publicacion"])

# Filtrar por provincia A Coruña (normalizando nombre)
# df = df[df["provincia"].str.strip().str.lower() == "a coruña"]

# Quedarse con un único registro por evento
df_unicos = df.sort_values("start_time_obj").drop_duplicates(subset="id", keep="first")

# Calcular duración en días
df_unicos["duracion_dias"] = (df_unicos["fecha_publicacion"] - df_unicos["start_time_obj"]).dt.total_seconds() / 86400

# Seleccionar columnas deseadas
df_resultado = df_unicos[["id", "road", "duracion_dias", "type", "severity", "start_time_obj", "fecha_publicacion"]]

# Exportar para análisis en Power BI
df_resultado.to_csv("visualizaciones/carreteras_coru/eventos_a_coruna_con_duracion.csv", index=False)

# Vista previa
print(df_resultado.head())
