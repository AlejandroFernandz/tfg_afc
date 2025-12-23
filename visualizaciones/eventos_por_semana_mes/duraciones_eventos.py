# duracion_eventos_por_id.py (versión corregida)

import pandas as pd

# Cargar CSV con eventos + publicationTime + start_time_obj, ######## TODOS LOS QUE HAY EN S3, NO SOLO EL ULTIMO ########
df = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas.csv", low_memory=False)

# Asegurar que fecha_publicacion (fecha de publicacion del archvio trafico.xml) y start_time_obj (fecha de inicio de cada evento que se encuentre en el ultimo trafico.xml) esten en formato datetime
df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)
df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], errors="coerce", utc=True)

# Filtrar eventos válidos, eliminando filas completas que tengan nulos en alguno de estos campos clave
df = df.dropna(subset=["id", "fecha_publicacion", "start_time_obj"])

# Agrupar por ID de modo que cada ID muestre un unico ID consolidado -> NO SE REPTEN IDS
# fecha_inicio es el valor minimo de start_time_obj que haya para ese id (en teoria aparece siempre el mismo)
# fecha_fin es el valor maximo de fecha_publicacion que haya para ese id (es la ultima fecha publicacion en la que aparece el id, y por lo tanto, la fecha en que acaba el evento)

duracion_eventos = df.groupby("id").agg(
    tipo_evento=("type", "first"),
    provincia=("provincia","first"),
    fecha_inicio=("start_time_obj", "min"),  # inicio real
    fecha_fin=("fecha_publicacion", "max")   # última vez visto
).reset_index()

# Calcular duración real de cada ID/Evento en días
duracion_eventos["duracion_dias"] = (duracion_eventos["fecha_fin"] - duracion_eventos["fecha_inicio"]).dt.days
# Crea una nueva columna semana_inicio que representa la SEMANA EN LA QUE SE REGISTRÓ EL EVENTO 
duracion_eventos["semana_inicio"] = duracion_eventos["fecha_inicio"].dt.to_period("W") # Convierte fecha a formato semanal correspondiente


# Exportar para análisis
duracion_eventos.to_csv("visualizaciones/eventos_por_semana_mes/duracion_eventos_por_id.csv", index=False)

