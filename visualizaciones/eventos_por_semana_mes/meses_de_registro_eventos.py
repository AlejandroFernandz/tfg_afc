import pandas as pd

# Cargar datos
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv", low_memory=False)

# Convertir a datetime
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)

# Filtrar eventos válidos, eliminando filas con valores nulos en alguna de estas columnas
df = df.dropna(subset=["id", "start_time_obj", "type", "provincia"])

# Ordenar y eliminar duplicados por id (quedarse solo con el primer evento al ordenarlo por fecha)
df = df.sort_values("start_time_obj").drop_duplicates(subset="id", keep="first")

# Extraer mes de inicio como texto YYYY-MM
df["mes_inicio"] = df["start_time_obj"].dt.to_period("M").astype(str)

# Seleccionar columnas deseadas
df_resultado = df[["id", "mes_inicio", "type", "provincia"]]

# Guardar archivo final
df_resultado.to_csv("visualizaciones/eventos_por_semana_mes/eventos_mes_registro_unico.csv", index=False)
