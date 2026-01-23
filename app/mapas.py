import folium
import os
from folium.plugins import FeatureGroupSubGroup, MarkerCluster
import pandas as pd
from app.utilidades import icono_por_tipo, safe_replace, add_segment_line_js
from app.descarga import *
from app.parsing import *
import schedule
import time

# Funcion para que se siga cargando el mapa hasta que se muestre algo (nunca será necesario refrescar manualmente)
def save_atomic(m, output_file):
    tmp = output_file + ".tmp"
    m.save(tmp)
    os.replace(tmp, output_file)

def expose_leaflet_map(base_map):
    map_var = base_map.get_name()
    js = f"""
    (function() {{
        function bind() {{
            if (typeof {map_var} !== "undefined" && {map_var}) {{
                window.map = {map_var};
            }} else {{
                setTimeout(bind, 50);
            }}
        }}
        bind();
    }})();
    """
    # OJO: aquí NO ponemos <script>...</script>
    base_map.get_root().script.add_child(folium.Element(js))

# Función para crear el mapa combinado
def create_actuales_map(eventos_df, radares_df, output_file="mapa_actuales.html"):
    OFFSET = 0.0001
    added_locations = set()
    added_radar_locations = set()

    base_map = folium.Map(location=[40.4168, -3.7038], zoom_start=6)

    cluster_eventos = MarkerCluster(name="Eventos agrupados", maxClusterRadius=50, disableClusteringAtZoom=15).add_to(base_map)
    cluster_radares = MarkerCluster(name="Radares agrupados", maxClusterRadius=50, disableClusteringAtZoom=15).add_to(base_map)

    def añadir_eventos(df, fijos_fg, tramos_fg):
        for _, event in df.iterrows():
            icon_name, icon_color = icono_por_tipo(event.get("cause_type_raw") or "unknown") # 21-01

            provincia = event["provincia"]

            if pd.notna(event.get("latitude")) and pd.notna(event.get("longitude")):
                lat, lon = event["latitude"], event["longitude"]
                while (lat, lon) in added_locations:
                    lat += OFFSET
                    lon += OFFSET
                added_locations.add((lat, lon))

                html_popup = f"""
                <div data-provincia="{provincia}" data-lat="{lat}" data-lng="{lon}">
                <div style="font-size:14px; line-height:1.25;">
                    <div style="font-weight:700; font-size:15px;">{event.get('type','Evento')}</div>
                    <div style="font-weight:600;">{event.get('cause_type','')}</div>
                    <div style="font-style:italic; color:#444;">{event.get('cause_detail','')}</div>

                    <hr style="margin:8px 0;">

                    <div>📍 <b>{event.get('road','')}</b> · Km <b>{event.get('kilometro','')}</b></div>
                    <div>🏙️ {event.get('locality','Desconocido')} ({event.get('provincia','Desconocida')})</div>
                    <div>➡️ Sentido de circulación: {event.get('sentido_kilometracion','Sentido desconocido')}</div>
                    <div>🛣️ Carril de circulación: {event.get('carril_usado','')}</div>

                    <hr style="margin:8px 0;">

                    <div>⚠️ Severidad: <b>{event.get('severity','desconocida')}</b> · Prob.: <b>{event.get('probability','desconocida')}</b></div>
                    <div>🕒 Inicio: {event.get('start_time','Fecha desconocida')}</div>

                    <div style="margin-top:6px; font-size:12px; color:#666;">ID: {event.get('id','')}</div>
                </div>
                </div>
                """



                folium.Marker(
                    location=[lat, lon],
                    tooltip= f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_popup, max_width=300),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                ).add_to(fijos_fg)

            if pd.notna(event.get("latitude_ini")) and pd.notna(event.get("longitude_ini")):
                lat_ini, lon_ini = event["latitude_ini"], event["longitude_ini"]
                lat_fin, lon_fin = event["latitude_fin"], event["longitude_fin"]

                while (lat_ini, lon_ini) in added_locations:
                    lat_ini += OFFSET
                    lon_ini += OFFSET
                added_locations.add((lat_ini, lon_ini))

                while (lat_fin, lon_fin) in added_locations:
                    lat_fin += OFFSET
                    lon_fin += OFFSET
                added_locations.add((lat_fin, lon_fin))

                seg_id = f"event_{event['id']}"


                html_ini = f"""
                <div data-seg="{seg_id}"
                    data-lat-ini="{lat_ini}" data-lng-ini="{lon_ini}"
                    data-lat-fin="{lat_fin}" data-lng-fin="{lon_fin}"
                    data-provincia="{provincia}" data-lat="{lat_ini}" data-lng="{lon_ini}">
                <div style="font-size:14px; line-height:1.25;">
                    <div style="font-weight:700; font-size:15px;">{event.get('type','Evento')}</div>
                    <div style="font-weight:600;">{event.get('cause_type','')}</div>
                    <div style="font-style:italic; color:#444;">{event.get('cause_detail','')}</div>

                    <hr style="margin:8px 0;">

                    <div>🛣️ <b>{event.get('road','')}</b> ({event.get('provincia','Desconocida')})</div>
                    <div>▶️ <b>TRAMO</b>:
                    Km <b>{event.get('kilometro_ini','')}</b> — {event.get('locality_ini','Desconocido')}
                    → Km <b>{event.get('kilometro_fin','')}</b> — {event.get('locality_fin','Desconocido')}
                    </div>
                    <div>➡️ Sentido de circulación: {event.get('sentido_kilometracion','Sentido desconocido')}</div>
                    <div>🛣️ Carril: {event.get('carril_usado','')}</div>

                    <hr style="margin:8px 0;">

                    <div>⚠️ Severidad: <b>{event.get('severity','desconocida')}</b> · Prob.: <b>{event.get('probability','desconocida')}</b></div>
                    <div>🕒 Inicio: {event.get('start_time','Fecha desconocida')}</div>

                    <div style="margin-top:6px; font-size:12px; color:#666;">ID: {event.get('id','')}</div>
                </div>
                </div>
                """

                html_fin = f"""
                <div data-seg="{seg_id}"
                    data-lat-ini="{lat_ini}" data-lng-ini="{lon_ini}"
                    data-lat-fin="{lat_fin}" data-lng-fin="{lon_fin}"
                    data-provincia="{provincia}" data-lat="{lat_fin}" data-lng="{lon_fin}">
                <div style="font-size:14px; line-height:1.25;">
                    <div style="font-weight:700; font-size:15px;">{event.get('type','Evento')}</div>
                    <div style="font-weight:600;">{event.get('cause_type','')}</div>
                    <div style="font-style:italic; color:#444;">{event.get('cause_detail','')}</div>

                    <hr style="margin:8px 0;">

                    <div>🛣️ <b>{event.get('road','')}</b> ({event.get('provincia','Desconocida')})</div>
                    <div>▶️ <b>TRAMO</b>:
                    Km <b>{event.get('kilometro_ini','')}</b> — {event.get('locality_ini','Desconocido')}
                    → Km <b>{event.get('kilometro_fin','')}</b> — {event.get('locality_fin','Desconocido')}
                    </div>
                    <div>➡️ Sentido de circulación: {event.get('sentido_kilometracion','Sentido desconocido')}</div>
                    <div>🛣️ Carril: {event.get('carril_usado','')}</div>

                    <hr style="margin:8px 0;">

                    <div>⚠️ Severidad: <b>{event.get('severity','desconocida')}</b> · Prob.: <b>{event.get('probability','desconocida')}</b></div>
                    <div>🕒 Inicio: {event.get('start_time','Fecha desconocida')}</div>

                    <div style="margin-top:6px; font-size:12px; color:#666;">ID: {event.get('id','')}</div>
                </div>
                </div>
                """


                folium.Marker(
                    location=[lat_ini, lon_ini],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_ini, max_width=300),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                ).add_to(tramos_fg)

                folium.Marker(
                    location=[lat_fin, lon_fin],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_fin, max_width=300),
                    icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
                ).add_to(tramos_fg)


    añadir_eventos(eventos_df, cluster_eventos, cluster_eventos)

    for _, radar in radares_df.iterrows():
        icon_color = "red" if radar["type"] == "Cabina" else "orange"
        provincia = radar["provincia"]


        if radar["type"] == "Cabina":
            lugar = radar.get("location_name") or radar.get("provincia", "Desconocida")
            lat, lon = radar["latitude"], radar["longitude"]
            if (lat, lon) not in added_radar_locations:

                html = f"""
                <div data-provincia="{provincia}">
                <div style="font-size:14px; line-height:1.25;">
                    <div style="font-weight:700; font-size:15px;">Radar fijo (cabina)</div>
                    <div style="font-weight:600;">Control de velocidad</div>
                    <div style="font-style:italic; color:#444;">Ubicación puntual</div>

                    <hr style="margin:8px 0;">

                    <div>📍 <b>{radar.get('road','')}</b> · Km <b>{radar.get('kilometro','')}</b></div>
                    <div>🏙️ {lugar} ({radar.get('provincia','Desconocida')})</div>
                    <div>➡️ Sentido de circulación: {radar.get('sentido_kilometracion','Desconocido')}</div>

                    <hr style="margin:8px 0;">

                    <div style="margin-top:6px; font-size:12px; color:#666;">ID: {radar.get('radar_id_fijo','')}</div>
                </div>
                </div>
                """


                folium.Marker(
                    location=[lat, lon],
                    tooltip=f"{radar['type']}<br>{provincia}",
                    popup=folium.Popup(html, max_width=300),
                    icon=folium.Icon(color=icon_color, icon="tachometer-alt", prefix="fa")
                ).add_to(cluster_radares)
                added_radar_locations.add((lat, lon))

        else:
            seg_id = f"radar_{radar['radar_id_ini']}_{radar['radar_id_fin']}"
            lat_ini_r, lon_ini_r = radar.get("latitude_ini"), radar.get("longitude_ini")
            lat_fin_r, lon_fin_r = radar.get("latitude_fin"), radar.get("longitude_fin")

            coords = [
                ("INI", lat_ini_r, lon_ini_r, radar["radar_id_ini"]),
                ("FIN", lat_fin_r, lon_fin_r, radar["radar_id_fin"])
            ]
            lugar = radar.get("location_name") or radar.get("provincia", "Desconocida")
            for label, lat, lon, radar_id in coords:
                if pd.notna(lat) and pd.notna(lon) and (lat, lon) not in added_radar_locations:

                    html = f"""
                    <div data-seg="{seg_id}"
                        data-lat-ini="{lat_ini_r}" data-lng-ini="{lon_ini_r}"
                        data-lat-fin="{lat_fin_r}" data-lng-fin="{lon_fin_r}"
                        data-provincia="{provincia}" data-lat="{lat}" data-lng="{lon}">
                    <div style="font-size:14px; line-height:1.25;">
                        <div style="font-weight:700; font-size:15px;">Radar de tramo — {label}</div>
                        <div style="font-weight:600;">Control de velocidad media</div>
                        <div style="font-style:italic; color:#444;">Tramo controlado (línea en el mapa)</div>

                        <hr style="margin:8px 0;">

                        <div>📍 <b>{radar.get('road','')}</b> · Km ref. <b>{radar.get('kilometro','')}</b></div>
                        <div>🏙️ {lugar} ({radar.get('provincia','Desconocida')})</div>
                        <div>➡️ Sentido de circulación: {radar.get('sentido_kilometracion','Desconocido')}</div>

                        <hr style="margin:8px 0;">

                        <div style="font-size:12px; color:#666;">
                        ID INI: {radar.get('radar_id_ini','')}<br>
                        ID FIN: {radar.get('radar_id_fin','')}
                        </div>
                    </div>
                    </div>
                    """


                    folium.Marker(
                        location=[lat, lon],
                        tooltip=f"{radar['type']}<br>{provincia}",
                        popup=folium.Popup(html, max_width=300),
                        icon=folium.Icon(
                            color=icon_color,
                            icon="arrow-right" if label == "FIN" else "arrow-left",
                            prefix="fa"
                        )
                    ).add_to(cluster_radares)
                    added_radar_locations.add((lat, lon))


    folium.LayerControl(collapsed=False).add_to(base_map)
    expose_leaflet_map(base_map)
    add_segment_line_js(base_map, max_km=50) 
    save_atomic(base_map, output_file)

def create_futuros_map(eventos_df, output_file="mapa_futuros.html"):
    OFFSET = 0.0001
    added_locations = set()

    base_map = folium.Map(location=[40.4168, -3.7038], zoom_start=6)

    cluster_eventos = MarkerCluster(name="Eventos futuros agrupados", maxClusterRadius=50, disableClusteringAtZoom=15).add_to(base_map)

    def añadir_eventos(df, fijos_fg, tramos_fg):
        for _, event in df.iterrows():
            icon_name, icon_color = icono_por_tipo(event.get("cause_type_raw") or "unknown") # 21-01
            provincia = event["provincia"]

            # Eventos fijos
            if pd.notna(event.get("latitude")) and pd.notna(event.get("longitude")):
                lat, lon = event["latitude"], event["longitude"]
                while (lat, lon) in added_locations:
                    lat += OFFSET
                    lon += OFFSET
                added_locations.add((lat, lon))

                html_popup = f"""
                <div data-provincia="{provincia}" data-lat="{lat}" data-lng="{lon}">
                    <b>EVENTO FUTURO</b><br>ID: {event['id']}<br>{event['type']} ({event['probability']}) - {event['severity']}<br>
                    Carretera {event['road']} ({event['locality']}, Km {event['kilometro']})<br>
                    Sentido de circulación: {event['sentido_kilometracion']}<br>
                    Hora esperada: {event['start_time']}<br>
                    Carril de circulación: {event['carril_usado']}
                </div>
                """

                folium.Marker(
                    location=[lat, lon],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_popup, max_width=300),
                    icon=folium.Icon(color="purple", icon=icon_name, prefix="fa")
                ).add_to(fijos_fg)


            if pd.notna(event.get("latitude_ini")) and pd.notna(event.get("longitude_ini")):
                lat_ini, lon_ini = event["latitude_ini"], event["longitude_ini"]
                lat_fin, lon_fin = event["latitude_fin"], event["longitude_fin"]

                while (lat_ini, lon_ini) in added_locations:
                    lat_ini += OFFSET
                    lon_ini += OFFSET
                added_locations.add((lat_ini, lon_ini))

                while (lat_fin, lon_fin) in added_locations:
                    lat_fin += OFFSET
                    lon_fin += OFFSET
                added_locations.add((lat_fin, lon_fin))

                seg_id = f"event_{event['id']}"

                html_ini = f"""
                <div data-seg="{seg_id}"
                    data-lat-ini="{lat_ini}" data-lng-ini="{lon_ini}"
                    data-lat-fin="{lat_fin}" data-lng-fin="{lon_fin}"
                    data-provincia="{provincia}" data-lat="{lat_ini}" data-lng="{lon_ini}">
                    <b>INICIO EVENTO FUTURO</b><br>ID: {event['id']}<br>{event['type']}<br>
                    {event['road']} ({event.get('locality_ini','Desconocido')}, Km {event['kilometro_ini']})<br>
                    Sentido de circulación: {event.get('sentido_kilometracion','Sentido desconocido')}<br>
                    Hora esperada: {event['start_time']}<br>
                    Carril de circulación: {event['carril_usado']}
                </div>
                """

                html_fin = f"""
                <div data-seg="{seg_id}"
                    data-lat-ini="{lat_ini}" data-lng-ini="{lon_ini}"
                    data-lat-fin="{lat_fin}" data-lng-fin="{lon_fin}"
                    data-provincia="{provincia}" data-lat="{lat_fin}" data-lng="{lon_fin}">
                    <b>FIN EVENTO FUTURO</b><br>ID: {event['id']}<br>{event['type']}<br>
                    {event['road']} ({event.get('locality_fin','Desconocido')}, Km {event['kilometro_fin']})<br>
                    Hora esperada: {event['start_time']}
                </div>
                """

                folium.Marker(
                    location=[lat_ini, lon_ini],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_ini, max_width=300),
                    icon=folium.Icon(color="purple", icon=icon_name, prefix="fa")
                ).add_to(tramos_fg)

                folium.Marker(
                    location=[lat_fin, lon_fin],
                    tooltip=f"{event['type']}<br>{provincia}",
                    popup=folium.Popup(html_fin, max_width=300),
                    icon=folium.Icon(color="purple", icon=icon_name, prefix="fa")
                ).add_to(tramos_fg)


    añadir_eventos(eventos_df, cluster_eventos, cluster_eventos)

    folium.LayerControl(collapsed=False).add_to(base_map)
    expose_leaflet_map(base_map)
    add_segment_line_js(base_map, max_km=50)   # 22-01 para segmentos entre popups
    save_atomic(base_map, output_file)

# Actualizar el mapa
def update_map():
    from datetime import datetime, timezone
    import os

    # 1. Descargar datos
    download_trafico("data/trafico.xml")
    download_radares("data/radares.xml")

    # 2. Parsear datos
    eventos_df = parse_datex("data/trafico.xml")
    radares_df = parse_radares("data/radares.xml")

    # 3. Provincias únicas. Son los nombres que saldran en los desplegables
    provincias = [
    "A Coruña", "Albacete", "Alicante", "Almería", "Ávila", "Badajoz", "Barcelona", "Bilbao",
    "Cádiz", "Castellón", "Ciudad Real", "Córdoba", "Cuenca", "Girona", "Granada", "Guadalajara",
    "Huelva", "Huesca", "Jaén", "La Rioja", "Las Palmas", "León", "Lleida", "Lugo", "Madrid",
    "Málaga", "Murcia", "Ourense", "Oviedo", "Palencia", "Pontevedra", "Salamanca", "San Sebastián",
    "Santa Cruz de Tenerife", "Santander", "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel",
    "Toledo", "Valencia/València", "Valladolid", "Vitoria", "Zamora", "Zaragoza"
    ]
    opciones_provincia = "<br>".join([f'<option value="{prov}">{prov}</option>' for prov in provincias])    

    # 4. Separar eventos en actuales y futuros en base a la hora de inicio del evento
    now = datetime.now(timezone.utc)
    eventos_actuales = eventos_df[eventos_df["start_time_obj"] <= now]
    eventos_futuros = eventos_df[eventos_df["start_time_obj"] > now]

    # 5. Generar mapas individuales para eventos actuales y eventos futuros
    create_actuales_map(eventos_actuales, radares_df, "mapas_generados/mapa_actuales.html")
    create_futuros_map(eventos_futuros, "mapas_generados/mapa_futuros.html")

    # 6. Leer mapas generados
    with open("mapas_generados/mapa_actuales.html", encoding="utf-8") as f:
        mapa_actuales_html = f.read()
    with open("mapas_generados/mapa_futuros.html", encoding="utf-8") as f:
        mapa_futuros_html = f.read()

    # 7. Crear HTML principal embebiendo los iframes
    html_con_tabs = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mapa de Tráfico</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; overflow: hidden; height: 100vh; }}
        .layout {{ display: flex; height: 100vh; overflow: hidden; }}
        .sidebar {{ width: 250px; background: #f9f9f9; padding: 1em; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }}
        .main {{ flex-grow: 1; position: relative; }}
        .tabs {{ display: flex; flex-direction: column; margin-top: 1em; }}
        .tab {{ padding: 0.5em; cursor: pointer; border-left: 4px solid transparent; }}
        .tab.active {{ background: #e0e0ff; border-left: 4px solid #007BFF; }}
        .map-container {{ display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        .map-container.active {{ display: block; }}
    </style>
</head>
<body>

<div class="layout">
  <div class="sidebar">
    <label for="provinciaSelect"><b>Filtrar por provincia:</b></label><br>
    <select id="provinciaSelect" style="width: 100%; margin-top: 0.5em;">
        <option value="Todas">Todas</option>
        {opciones_provincia}
    </select>
    <div class="tabs">
        <div class="tab active" data-tab="actuales">Eventos actuales y radares</div>
        <div class="tab" data-tab="futuros">Eventos futuros</div>
    </div>
  </div>
  <div class="main">
    <div id="actuales" class="map-container active">
        <iframe id="iframe_actuales" style="width:100%; height:100%; border:none;"></iframe>
    </div>

    <div id="futuros" class="map-container">
        <iframe id="iframe_futuros" style="width:100%; height:100%; border:none;"></iframe>
    </div>
  </div>
</div>

    

<script>
    document.getElementById("iframe_actuales").src =
        "/mapa_actuales.html?ts=" + Date.now();

    document.getElementById("iframe_futuros").src =
        "/mapa_futuros.html?ts=" + Date.now();

    // Provincias y coordenadas para que se relacionen con las de la DGT (todas en mayusculas para que coincidan y se lean)
    const coordenadas_provincias = {{
    "A CORUÑA": [43.3623, -8.4115],
    "ALBACETE": [38.9943, -1.8585],
    "ALICANTE": [38.3452, -0.4810],
    "ALMERÍA": [36.8381, -2.4597],
    "ÁVILA": [40.6565, -4.6818],
    "BADAJOZ": [38.8786, -6.9703],
    "BARCELONA": [41.3888, 2.1590],
    "BILBAO": [43.2630, -2.9350],
    "CÁDIZ": [36.5160, -6.2994],
    "CASTELLÓN": [39.9864, -0.0513],
    "CIUDAD REAL": [38.9861, -3.9271],
    "CÓRDOBA": [37.8882, -4.7794],
    "CUENCA": [40.0704, -2.1374],
    "GIRONA": [41.9794, 2.8214],
    "GRANADA": [37.1773, -3.5986],
    "GUADALAJARA": [40.6330, -3.1669],
    "HUELVA": [37.2614, -6.9447],
    "HUESCA": [42.1401, -0.4089],
    "JAÉN": [37.7796, -3.7849],
    "LA RIOJA": [42.4650, -2.4480],
    "LAS PALMAS": [28.1272, -15.4314],
    "LEÓN": [42.5987, -5.5671],
    "LLEIDA": [41.6176, 0.6200],
    "LUGO": [43.0097, -7.5560],
    "MADRID": [40.4168, -3.7038],
    "MÁLAGA": [36.7213, -4.4214],
    "MURCIA": [37.9834, -1.1299],
    "OURENSE": [42.3360, -7.8642],
    "OVIEDO": [43.3619, -5.8494],
    "PALENCIA": [42.0095, -4.5270],
    "PONTEVEDRA": [42.4333, -8.6333],
    "SALAMANCA": [40.9701, -5.6635],
    "SAN SEBASTIÁN": [43.3183, -1.9812],
    "SANTA CRUZ DE TENERIFE": [28.4636, -16.2518],
    "SANTANDER": [43.4623, -3.8099],
    "SEGOVIA": [40.9481, -4.1184],
    "SEVILLA": [37.3886, -5.9823],
    "SORIA": [41.7666, -2.4689],
    "TARRAGONA": [41.1189, 1.2445],
    "TERUEL": [40.3456, -1.1065],
    "TOLEDO": [39.8628, -4.0273],
    "VALENCIA/VALÈNCIA": [39.4737, -0.3758],
    "VALLADOLID": [41.6520, -4.7286],
    "VITORIA": [42.8467, -2.6727],
    "ZAMORA": [41.5033, -5.7446],
    "ZARAGOZA": [41.6488, -0.8891],
    "TODAS": [40.4168, -3.7038]
}};
    const tabs = document.querySelectorAll(".tab");
    const containers = {{
        actuales: document.getElementById("actuales"),
        futuros: document.getElementById("futuros")
    }};

    function showTab(tabName) {{
        tabs.forEach(t => t.classList.remove("active"));
        document.querySelector(`.tab[data-tab="${{tabName}}"]`).classList.add("active");
        Object.keys(containers).forEach(key => {{
            containers[key].classList.toggle("active", key === tabName);
        }});
    }}

    tabs.forEach(tab => {{
        tab.addEventListener("click", () => showTab(tab.dataset.tab));
    }});

    showTab("actuales");

    // 🔄 Refrescar automáticamente cada 5 minutos
    setTimeout(() => {{
        location.reload();
    }}, 60000);  // Actualmente está cada 1 minuto - 300.000 ms = 5 minutos

    // 🔍 Filtro por provincia con zoom
    document.getElementById("provinciaSelect").addEventListener("change", function () {{
    const seleccion = this.value.trim().toUpperCase();
    const coords = coordenadas_provincias[seleccion] || coordenadas_provincias["TODAS"];
    const zoom = seleccion === "TODAS" ? 6 : 10;

    const iframe = containers.actuales.classList.contains("active")
        ? document.querySelector("#actuales iframe")
        : document.querySelector("#futuros iframe");

    const intentarZoom = () => {{
        try {{
            const mapa = iframe.contentWindow.map;
            if (mapa && typeof mapa.setView === "function") {{
                mapa.setView(coords, zoom);
            }} else {{
                setTimeout(intentarZoom, 200);
            }}
        }} catch (e) {{
            setTimeout(intentarZoom, 200);
        }}
    }};

    intentarZoom();
}});

</script>

</body>
</html>"""

    
    # 8. Escribir de forma atómica para evitar corrupción
    temp_path = "mapas_generados/mapa_completo.tmp.html"
    final_path = "mapas_generados/mapa_completo.html"

    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(html_con_tabs)

    os.replace(temp_path, final_path)

    print("[✅] Mapa principal generado con pestañas en: mapas_generados/mapa_completo.html")
