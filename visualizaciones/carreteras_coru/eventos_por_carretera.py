import pandas as pd

# Cargar el CSV
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv", low_memory=False)

# Convertir fechas
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)

# Filtrar eventos válidos
df = df.dropna(subset=["id", "road", "start_time_obj", "provincia"])

# Quitar duplicados por evento
df_unicos = df.sort_values("start_time_obj").drop_duplicates(subset="id", keep="first")

# Formatear mes como "abril 2025"
df_unicos["mes_inicio"] = df_unicos["start_time_obj"].dt.strftime("%B %Y").str.capitalize()

# Seleccionar columnas deseadas
df_resultado = df_unicos[["id", "road", "provincia", "mes_inicio"]]

# Guardar
df_resultado.to_csv("visualizaciones/carreteras_coru/eventos_unicos_carretera_provincia_mes_lindo.csv", index=False)

# Muestra
print(df_resultado.head())
