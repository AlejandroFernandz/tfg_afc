# 05/06/2025: Versión corregida y limpia para incluir eventos de tramo y punto cercanos a estadios

import pandas as pd
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
# from visualizaciones.eventos_por_semana_mes.duraciones_eventos import duracion_eventos

# Función para calcular distancia entre coordenadas (Haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Cargar datasets
df_partidos = pd.read_csv("visualizaciones/eventos_partidos/partidos_estadios.csv")
df_eventos = pd.read_csv("visualizaciones/eventos_por_semana_mes/source_eventospormessemana_todos_confechas_final.csv")

# Parsear fechas
df_partidos["fecha"] = pd.to_datetime(df_partidos["Date"], format="%d/%m/%Y")
df_partidos["hora"] = pd.to_datetime(df_partidos["Time"], format="%H:%M").dt.time
df_eventos["fecha_publicacion"] = pd.to_datetime(df_eventos["fecha_publicacion"], errors="coerce", utc=True).dt.tz_localize(None)
df_eventos["hora_evento"] = df_eventos["fecha_publicacion"].dt.time
df_eventos["fecha"] = df_eventos["fecha_publicacion"].dt.date

# Resultado final
resultados = []

# Para evitar duplicados por id + fecha
guardados = set()

# Parámetros
radio_km = 10
ventana_antes = timedelta(hours=2)
ventana_despues = timedelta(hours=2)

# Iterar sobre partidos
for _, partido in df_partidos.iterrows():
    fecha_partido = partido["fecha"].date()
    hora_partido = datetime.combine(fecha_partido, partido["hora"])
    estadio = partido["Estadio"]
    lat_estadio = partido["Latitud"]
    lon_estadio = partido["Longitud"]

    # Filtrar eventos del mismo día
    eventos_dia = df_eventos[df_eventos["fecha"] == fecha_partido].copy()

    for _, evento in eventos_dia.iterrows():
        lat_evento = None
        lon_evento = None
        distancia = None

        # Evento puntual
        if not pd.isna(evento.get("latitude")) and not pd.isna(evento.get("longitude")):
            lat_evento = evento["latitude"]
            lon_evento = evento["longitude"]
            distancia = haversine(lat_estadio, lon_estadio, lat_evento, lon_evento)

        # Evento de tramo
        elif (
            not pd.isna(evento.get("latitud_ini")) and not pd.isna(evento.get("longitud_ini")) and
            not pd.isna(evento.get("latitud_fin")) and not pd.isna(evento.get("longitud_fin"))
        ):
            d_ini = haversine(lat_estadio, lon_estadio, evento["latitud_ini"], evento["longitud_ini"])
            d_fin = haversine(lat_estadio, lon_estadio, evento["latitud_fin"], evento["longitud_fin"])
            distancia = min(d_ini, d_fin)

            # Tomamos el extremo más cercano como coordenada de referencia
            if d_ini <= d_fin:
                lat_evento = evento["latitud_ini"]
                lon_evento = evento["longitud_ini"]
            else:
                lat_evento = evento["latitud_fin"]
                lon_evento = evento["longitud_fin"]

        else:
            continue  # No tiene coordenadas válidas

        # Si la distancia es válida y dentro del radio
        if distancia is not None and distancia <= radio_km:
            hora_evento = evento["fecha_publicacion"]
            if hora_partido - ventana_antes <= hora_evento <= hora_partido + ventana_despues:
                clave = (evento["id"], evento["fecha"])  # Evita duplicados por id + fecha
                if clave in guardados:
                    continue
                guardados.add(clave)

                resultados.append({
                    "id_evento": evento["id"],
                    "tipo_evento": evento["type"],
                    "distancia_km": round(distancia, 2),
                    "fecha_evento": evento["fecha_publicacion"],
                    "estadio": estadio,
                    "local": partido["HomeTeam"],
                    "visitante": partido["AwayTeam"],
                    "partido": f"{partido['HomeTeam']} vs {partido['AwayTeam']}",
                    "hora_partido": hora_partido,
                    "provincia_evento": evento.get("provincia", ""),
                    "lat_evento": lat_evento,
                    "lon_evento": lon_evento,
                    "lat_estadio": lat_estadio,
                    "lon_estadio": lon_estadio,
                    #" duracion_dias" : duracion_eventos["duracion_dias"]
                })

# Convertir a DataFrame
df_resultados = pd.DataFrame(resultados)

# Exportar a CSV
df_resultados.to_csv("visualizaciones/eventos_partidos/eventos_cercanos_a_partidos_final2.csv", index=False)
print(f"[✅] Exportado CSV con {len(df_resultados)} eventos cercanos a partidos.")
