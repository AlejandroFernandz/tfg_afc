import pandas as pd
# Puntaje por tipo de evento traducido
PUNTAJES_EVENTOS = {
    "Obras": 1,
    "Desvío temporal": 1,
    "Tráfico denso": 2,
    "Obstrucción de carretera": 3,
    "Obstrucción por vehículo": 3,
    "Evento público": 1,
    "Obstrucción meteorológica": 3,
    "Gestión de velocidad": 1,
    "Malas condiciones meteorológicas": 2,
    "Trabajos de mantenimiento": 1,
    "Gestión general de la carretera": 1,
    "Gestión de redireccionamiento": 1,
    "Condiciones de carretera no relacionadas con la meteorología": 2,
    "Condiciones de carretera relacionadas con la meteorología": 2,
    "Gestión de la conducción invernal": 2,
    "Actividad de perturbación": 1,
    "Obstrucción por presencia de animales": 3
}

# Cargar eventos
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv", low_memory=False)

# Convertir fechas
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)

# Filtrar registros válidos
df = df.dropna(subset=["id", "road", "start_time_obj", "severity", "type"])

# Eliminar duplicados por evento
df_unicos = df.sort_values("start_time_obj").drop_duplicates(subset="id", keep="first")

# Traducir tipo de evento
df_unicos["tipo_evento_es"] = df_unicos["type"].map(df["type"])

# Extraer mes con nombre en español
df_unicos["mes"] = df_unicos["start_time_obj"].dt.strftime("%B %Y").str.capitalize()

# Puntaje por severidad
df_unicos["puntaje_severidad"] = df_unicos["severity"].map({"Baja": 1, "Alta": 2}).fillna(1)

# Puntaje por tipo de evento
df_unicos["puntaje_tipo"] = df_unicos["tipo_evento_es"].map(PUNTAJES_EVENTOS).fillna(1)

# Puntaje total
df_unicos["puntaje_total"] = df_unicos["puntaje_severidad"] + df_unicos["puntaje_tipo"]

# Agrupar por mes y carretera
ranking = df_unicos.groupby(["mes", "road"]).agg(
    conteo_eventos=("id", "count"),
    puntaje_total=("puntaje_total", "sum")
).reset_index()

# Ordenar y rankear dentro de cada mes
ranking = ranking.sort_values(by=["mes", "puntaje_total", "conteo_eventos"], ascending=[True, False, False])
ranking["ranking_mensual"] = ranking.groupby("mes")["puntaje_total"].rank(method="dense", ascending=False).astype(int)

# Exportar
ranking.to_csv("visualizaciones/carreteras_coru/ranking_mensual_carreteras_conflictivas_ponderado.csv", index=False)

# Ver top 3 por mes
print(ranking.groupby("mes").head(3))