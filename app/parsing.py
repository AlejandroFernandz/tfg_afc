# Funciones parser de los datos de trafico y de radares
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import pandas as pd

# 10/01 traducciones nuevas sobre actualizacion del dataset, y nuevo formato implementado categoria: subcategoria
# --- Traducciones y jerarquía de tipos (DGT profile v3.6) ---

# Subtitulos de eventos traducidos
CAT_EVENT_TYPE = {
    "GenericSituationRecord": "Genérico",

    "OperatorAction": "Gestión",
    "NetworkManagement": "Gestión",
    "RoadOrCarriagewayOrLaneManagement": "Gestión",
    "WinterDrivingManagement": "Gestión",
    "SpeedManagement": "Gestión",
    "GeneralInstructionOrMessageToRoadUsers": "Gestión",

    "Roadworks": "Obras",
    "MaintenanceWorks": "Obras",

    "TrafficElement": "Tráfico",
    "AbnormalTraffic": "Tráfico",
    "PoorEnvironmentConditions": "Tráfico",
    "NonWeatherRelatedRoadConditions": "Tráfico",

    "Obstruction": "Obstrucción",
    "VehicleObstruction": "Obstrucción",
    "AnimalPresenceObstruction": "Obstrucción",
    "GeneralObstruction": "Obstrucción",
    "objectOnTheRoad": "Obstrucción",
    "vehicleStuck": "Obstrucción",
    "vehicleOnFire": "Obstrucción",

    "ServiceInformation": "Servicio",
    "TransitInformation": "Servicio",

    "Accident": "Accidente"
}
# Titulo principal traducido (situationRecord xsi:type)
TRAD_EVENT_TYPE = {
    "GenericSituationRecord": "Incidencia genérica",

    "OperatorAction": "Acción del operador",
    "NetworkManagement": "Gestión de red",
    "RoadOrCarriagewayOrLaneManagement": "Gestión de carril / calzada",
    "WinterDrivingManagement": "Gestión de conducción invernal",
    "SpeedManagement": "Gestión de velocidad",
    "GeneralInstructionOrMessageToRoadUsers": "Aviso a conductores",

    "Roadworks": "Obras",
    "MaintenanceWorks": "Obras de mantenimiento",

    "TrafficElement": "Evento de tráfico",
    "AbnormalTraffic": "Tráfico anómalo",
    "PoorEnvironmentConditions": "Condiciones meteorológicas adversas",
    "NonWeatherRelatedRoadConditions": "Condiciones adversas en la vía",

    "Obstruction": "Obstrucción",
    "VehicleObstruction": "Vehículo obstaculizando",
    "AnimalPresenceObstruction": "Presencia de animales",
    "GeneralObstruction": "Obstáculo en la vía",
    "objetctOnTheRoad": "Objeto en la vía",
    "vehicleStuck": "Vehículo atascado en la vía",
    "vehicleOnFire": "Vehículo en llamas",

    "ServiceInformation": "Información de servicio",
    "TransitInformation": "Información de transporte público",

    "Accident": "Accidente en la vía "
}

# Subtitulos de eventos traducidos
# Traducciones para causeType (valores que vienen en sit:causeType) # 22-01
TRAD_CAUSE_TYPE = {
    "abnormalTraffic": "Tráfico anómalo",
    "accident": "Accidente",
    "environmentalObstruction": "Obstrucción por condiciones ambientales",
    "infrastructureDamageObstruction": "Daños en la infraestructura",
    "obstruction": "Obstrucción",
    "poorEnvironment": "Condiciones meteorológicas adversas",
    "roadMaintenance": "Mantenimiento de la vía",
    "roadOrCarriagewayOrLaneManagement": "Gestión de carril / calzada",
    "vehicleObstruction": "Obstrucción por vehículo",
}
# Traducciones para detailedCauseType (cause_detail)
TRAD_CAUSE_DETAIL = {
    # Obstrucciones
    "objectOnTheRoad": "Objeto en la vía",
    "vehicleStuck": "Vehículo atascado",
    "vehicleOnFire": "Vehículo en llamas",
    "animalsOnTheRoad": "Animales en la calzada",

    # Tráfico / accidentes
    "accident": "Accidente",
    "seriousAccident": "Accidente grave",
    "multiVehicleAccident": "Accidente múltiple",

    # Obras / mantenimiento
    "roadworks": "Obras",
    "maintenanceWorks": "Trabajos de mantenimiento",
    "resurfacing": "Reasfaltado",
    "laneClosures": "Cierre de carriles",

    # Meteorología
    "heavyRain": "Lluvias intensas",
    "snow": "Nieve",
    "ice": "Hielo",
    "fog": "Niebla",
    "strongWinds": "Viento fuerte",

    # Infraestructura
    "bridgeDamage": "Daños en puente",
    "tunnelClosure": "Cierre de túnel",
}


def etiqueta_jerarquica(event_type_raw: str) -> str:
    cat = CAT_EVENT_TYPE.get(event_type_raw, "Otros")
    sub = TRAD_EVENT_TYPE.get(event_type_raw, event_type_raw)

    # evita "Obras: Obras"
    if sub.strip().lower() == cat.strip().lower():
        return cat

    return f"{cat}: {sub}"


# EVENTOS DE TRAFICO - PARSER
def parse_datex(file_path="trafico.xml"):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Namespaces NUEVOS (según tu root)
    ns = {
        "sit": "http://levelC/schema/3/situation",
        "com": "http://levelC/schema/3/common",
        "loc": "http://levelC/schema/3/locationReferencing",
        "lse": "http://levelC/schema/3/locationReferencingSpanishExtension",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    events = []

    # Ahora sí debería encontrar situationRecord
    for situation in root.findall(".//sit:situationRecord", namespaces=ns):
        record_id = situation.get("id")

        # xsi:type
        event_type_raw = situation.get("{http://www.w3.org/2001/XMLSchema-instance}type", "Unknown")
        event_type_code = event_type_raw.split(":")[-1] if event_type_raw else "Unknown"  # código técnico 10/01, el situation original

        event_title = TRAD_EVENT_TYPE.get(event_type_code, event_type_code)  # título del popup (traducido) 16/01

        # Tipo real basado en la causa (si existe) - prueba 10/01
        cause_type_el = situation.find(".//sit:cause/sit:causeType", namespaces=ns)
        cause_type = cause_type_el.text.strip() if (cause_type_el is not None and cause_type_el.text) else None
        # 22-01 nuevas variables para traduir subtitulo y detalle
        cause_type_raw = cause_type  # lo original del XML
        cause_type_trad = TRAD_CAUSE_TYPE.get(cause_type_raw, CAT_EVENT_TYPE.get(cause_type_raw, cause_type_raw)) if cause_type_raw else None


        
        #16/01
        cause_detail = None
        detailed_el = situation.find(".//sit:cause/sit:detailedCauseType", namespaces=ns)
        if detailed_el is not None:
            for child in list(detailed_el):
                if child is not None and child.text and child.text.strip():
                    cause_detail = child.text.strip()
                    break
        
        # 22-01
        # Guardamos raw y traducción de cause_detail
        cause_detail_raw = cause_detail
        cause_detail_trad = TRAD_CAUSE_DETAIL.get(cause_detail_raw, cause_detail_raw)

        icon_code = cause_type_raw or event_type_code # 16/01 para poner el icono como el causeType

        probability_el = situation.find("sit:probabilityOfOccurrence", namespaces=ns)
        probability = probability_el.text if probability_el is not None else None

        severity_el = situation.find("sit:severity", namespaces=ns)
        severity = severity_el.text if severity_el is not None else None

        # Start time (igual, pero ojo: viene con offset +01/+02)
        start_time_el = situation.find(".//com:validityTimeSpecification/com:overallStartTime", namespaces=ns)
        if start_time_el is not None and start_time_el.text:
            start_time_str = start_time_el.text.strip()
            start_time_obj = datetime.fromisoformat(start_time_str).astimezone(timezone.utc)
            formatted_time = start_time_obj.strftime("%H:%M:%S del %d-%m-%y")
        else:
            formatted_time = "Fecha de inicio desconocida"
            start_time_obj = None

        # Carril usado: en tu ejemplo está dentro de supplementaryPositionalDescription/carriageway/lane/laneUsage
        carril_el = situation.find(".//loc:lane/loc:laneUsage", namespaces=ns)
        carril_usado = carril_el.text if carril_el is not None else "Carril original"

        # Carretera: en el XML nuevo está como loc:roadInformation/loc:roadName
        road_el = situation.find(".//loc:roadInformation/loc:roadName", namespaces=ns)
        road = road_el.text if road_el is not None else "Desconocido"

        # Provincia: ahora viene en la extensión española, por ejemplo lse:province dentro de extendedTpegNonJunctionPoint
        prov_el = situation.find(".//lse:province", namespaces=ns)
        provincia = prov_el.text if prov_el is not None else "Desconocida"

        # Kilómetros: ahora vienen como lse:kilometerPoint (en tu ejemplo)
        km_from_el = situation.find(".//loc:from//lse:kilometerPoint", namespaces=ns)
        km_to_el   = situation.find(".//loc:to//lse:kilometerPoint", namespaces=ns)

        kilometro_ini = float(km_from_el.text) if (km_from_el is not None and km_from_el.text) else None
        kilometro_fin = float(km_to_el.text)   if (km_to_el is not None and km_to_el.text) else None

        # Sentido: ahora lo tienes como lse:tpegDirectionRoad
        sentido_el = situation.find(".//lse:tpegDirectionRoad", namespaces=ns)
        sentido_kilometracion_ini = sentido_el.text if sentido_el is not None else None

        # Traducciones (las tuyas)
        traducciones_severity = {"low": "Baja", "medium": "Media", "high": "Alta", "highest": "Muy alta"}
        traducciones_probabilidad = {"riskOf": "posible riesgo", "certain": "confirmado", "probable": "probable"}

        traducciones_carril = {
            "allLanesCompleteCarriageway": "Todos los carriles de la calzada",
            "tidalFlowLane": "Carril reversible",
            "middleLane": "Carril central",
            "rightLane": "Carril derecho",
            "leftLane": "Carril izquierdo",
            "hardShoulder": "Arcén",
            "centralReservation": "Mediana central entre carriles bidireccionales",
            "turningLane": "Carril de giro",
            "carPoolLane": "Carril compartido",
            "_extended": "Carril especial",
        }
        traducciones_sentido = {
            "both": "Ambos",
            "negative": "Decreciente de la km",
            "positive": "Creciente de la km",}

        carril_usado = traducciones_carril.get(carril_usado, carril_usado)
        sentido_kilometracion_ini = traducciones_sentido.get(sentido_kilometracion_ini, sentido_kilometracion_ini)
        probability = traducciones_probabilidad.get(probability, "desconocida")
        severity = traducciones_severity.get(severity, "desconocida")

        # LocationReference: en tu XML es sit:locationReference con tpegLinearLocation y from/to
        for location_ref in situation.findall(".//sit:locationReference", namespaces=ns):

            # Municipality para tramo (INI y FIN) y para punto fijo 22-01
            mun_ini_el = location_ref.find(".//loc:from//lse:municipality", namespaces=ns)
            mun_fin_el = location_ref.find(".//loc:to//lse:municipality", namespaces=ns)
            mun_point_el = location_ref.find(".//loc:tpegPointLocation//lse:municipality", namespaces=ns)

            locality_ini = mun_ini_el.text.strip() if (mun_ini_el is not None and mun_ini_el.text) else "Desconocido"
            locality_fin = mun_fin_el.text.strip() if (mun_fin_el is not None and mun_fin_el.text) else "Desconocido"
            locality_point = mun_point_el.text.strip() if (mun_point_el is not None and mun_point_el.text) else "Desconocido"

            # Evento de tramo: hay from y to con pointCoordinates
            from_coords = location_ref.find(".//loc:from/loc:pointCoordinates", namespaces=ns)
            to_coords   = location_ref.find(".//loc:to/loc:pointCoordinates", namespaces=ns)

            if from_coords is not None and to_coords is not None:
                lat_ini = from_coords.find("loc:latitude", namespaces=ns)
                lon_ini = from_coords.find("loc:longitude", namespaces=ns)
                lat_fin = to_coords.find("loc:latitude", namespaces=ns)
                lon_fin = to_coords.find("loc:longitude", namespaces=ns)

                if all(x is not None and x.text for x in [lat_ini, lon_ini, lat_fin, lon_fin]):
                    events.append({
                        "id": record_id,
                        "road": road,
                        "start_time": formatted_time,
                        "type": event_title,      # 16/01
                        "type_code": event_type_code,  # 10/01 esto se guarda para posibles filtros internos y para los iconos, no se muestra en el popup
                        # "cause_type": cçause_type, # 16/01 # 22-01
                        # "cause_detail": cause_detail, #16/01 # 22-01
                        "icon_code": icon_code, # Para meter el icono del causeType 16/01
                        "type_record_code": event_type_code,      # el xsi:type original (opcional pero útil)
                        "cause_type": cause_type_trad,          # lo que se muestra en popup
                        "cause_type_raw": cause_type_raw,       # para iconos / lógica interna
                        "cause_detail": cause_detail_trad,      # lo que se muestra # 22-01
                        "cause_detail_raw": cause_detail_raw,   # por si lo necesitas para lógica interna # 22-01
                        "probability": probability,
                        "severity": severity,
                        "locality_ini": locality_ini, # 22-01
                        "locality_fin": locality_fin, # 22-01
                        "latitude_ini": float(lat_ini.text),
                        "longitude_ini": float(lon_ini.text),
                        "latitude_fin": float(lat_fin.text),
                        "longitude_fin": float(lon_fin.text),
                        "carril_usado": carril_usado,
                        "kilometro_ini": kilometro_ini if kilometro_ini is not None else "Km inicio desconocido",
                        "kilometro_fin": kilometro_fin if kilometro_fin is not None else "Km fin desconocido",
                        # "sentido_kilometracion_ini": sentido_kilometracion_ini if sentido_kilometracion_ini is not None else "Sentido desconocido",
                        "sentido_kilometracion": sentido_kilometracion_ini if sentido_kilometracion_ini is not None else "Sentido desconocido",
                        "sentido_kilometracion_ini": sentido_kilometracion_ini if sentido_kilometracion_ini is not None else "Sentido desconocido",
                        "provincia": provincia,
                        "start_time_obj": start_time_obj,
                    })
                continue # 10/01 para que no duplique si hay from/to, y salgan popups duplicados

            # (Opcional) Evento punto fijo: si en algún caso aparece loc:pointCoordinates suelto
            point_coords = location_ref.find(".//loc:tpegPointLocation//loc:pointCoordinates", namespaces=ns) # Cambio de la ruta, añadiendo tpegPointLocation para que sea mas específico
            # Kilómetro para evento punto fijo (ruta del XML de PointLocation)


            if point_coords is not None:
                lat = point_coords.find("loc:latitude", namespaces=ns)
                lon = point_coords.find("loc:longitude", namespaces=ns)
                km_point_el = location_ref.find( # 22-01 para meter el km en evento fijo
                ".//loc:tpegPointLocation//loc:point//lse:kilometerPoint",
                namespaces=ns)
                kilometro_punto = float(km_point_el.text) if (km_point_el is not None and km_point_el.text) else None # 22-01 para meter el km en evento fijo

                if lat is not None and lon is not None and lat.text and lon.text:
                    events.append({
                        "id": record_id,
                        "road": road,
                        "start_time": formatted_time,
                        "type": event_title,      # 10/01 esto es lo que se mostrará en el popup
                        "type_code": event_type_code,  # 10/01 esto se guarda para posibles filtros internos y para los iconos, no se muestra en el popup
                        # "cause_type": cause_type, # 10/01 opcional por si se depura
                        "cause_type": cause_type_trad,          # lo que se muestra en popup
                        "cause_type_raw": cause_type_raw,       # para iconos / lógica interna
                        "cause_detail": cause_detail_trad,   # subtítulo (detailedCauseType/*Type) # 22-01
                        "cause_detail_raw": cause_detail_raw,   # por si lo necesitas para lógica interna # 22-01
                        "icon_code": icon_code, # 16/01 Para meter el icono del causeType
                        "type_record_code": event_type_code,      # el xsi:type original (opcional pero útil)
                        "probability": probability,
                        "severity": severity,
                        "locality": locality_point, # 22-01
                        "latitude": float(lat.text),
                        "longitude": float(lon.text),
                        "carril_usado": carril_usado,
                        "kilometro": kilometro_punto if kilometro_punto is not None else "Km desconocido",
                        "sentido_kilometracion": sentido_kilometracion_ini,
                        "provincia": provincia,
                        "start_time_obj": start_time_obj,
                    })


    df = pd.DataFrame(events)

    # Normaliza start_time_obj para filtros posteriores (muy recomendado)
    if not df.empty and "start_time_obj" in df.columns:
        df["start_time_obj"] = pd.to_datetime(df["start_time_obj"], utc=True, errors="coerce")

    return df

# RADARES - PARSER
def parse_radares(file_path="radares.xml"):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    ns = {"_0": "http://datex2.eu/schema/1_0/1_0"}
    radares = []
    
    for predefined_location in root.findall(".//_0:predefinedLocation", namespaces=ns):
        # radar_id = predefined_location.get("id")
        radar_id_ini = predefined_location.find(".//_0:referencePointPrimaryLocation/_0:referencePoint/_0:referencePointIdentifier", namespaces=ns)
        radar_id_ini = radar_id_ini.text if radar_id_ini is not None else "Desconocido"

        radar_id_fin = predefined_location.find(".//_0:referencePointSecondaryLocation/_0:referencePoint/_0:referencePointIdentifier", namespaces=ns)
        radar_id_fin = radar_id_fin.text if radar_id_fin is not None else "Desconocido"

        radar_id_fijo = predefined_location.find(".//_0:referencePoint/_0:referencePointIdentifier", namespaces=ns)
        radar_id_fijo = radar_id_fijo.text if radar_id_fijo is not None else "Desconocido"

        road_name = predefined_location.find(".//_0:roadName/_0:value", namespaces=ns).text # Nombre de la carretera
        
        provincia = predefined_location.find(".//_0:administrativeArea/_0:value", namespaces=ns)
        provincia = provincia.text if provincia is not None else "Desconocida"
        # Nombre detallado del radar (si existe) - p.ej. "AS PIAS"
        # loc_name_el = predefined_location.find(".//_0:predefinedLocationName/_0:value", namespaces=ns)
        # location_name = loc_name_el.text.strip() if (loc_name_el is not None and loc_name_el.text) else None
        loc_name_el = predefined_location.find(".//_0:predefinedLocationName/_0:value", namespaces=ns)
        location_name = loc_name_el.text.strip() if (loc_name_el is not None and loc_name_el.text) else None

        # ❌ Filtrar nombres "técnicos" tipo CVM_..., CABINACINEMOMETRO_..., GUID_...
        if location_name:
            up = location_name.strip().upper()
            if (
                up.startswith("CVM_")
                or up.startswith("CABINACINEMOMETRO")
                or up.startswith("GUID_")
                or up.startswith("GUID")
            ):
                location_name = None

  

        kilometro = predefined_location.find(".//_0:referencePointDistance", namespaces=ns).text # Punto kilometrico en carretera para RADAR FIJO y RADAR DE TRAMO

        sentido_kilometracion = predefined_location.find(".//_0:directionRelative", namespaces=ns).text # Sentido RADAR FIJO y RADAR DE TRAMO
        if sentido_kilometracion == "negative":
            sentido_kilometracion = "Decreciente de la km"
        else:
            sentido_kilometracion = "Creciente de la km"
        
        # En el caso de que el radar sea de cabina (solo un par de coordenadas, un punto en el mapa)
        location_point = predefined_location.find(".//_0:point/_0:pointCoordinates", namespaces=ns)
        if location_point is not None:
            latitude = location_point.find("_0:latitude", namespaces=ns)
            longitude = location_point.find("_0:longitude", namespaces=ns)
            if latitude is not None and longitude is not None:
                radares.append({
                    "radar_id_fijo": radar_id_fijo,
                    "type": "Cabina",
                    "road": road_name,
                    "provincia": provincia,
                    "location_name": location_name,
                    "latitude": float(latitude.text),
                    "longitude": float(longitude.text),
                    "kilometro": float(kilometro)*1/1000,
                    "sentido_kilometracion": sentido_kilometracion
                })
        # En el caso de que sea un radar de tramo, y que por lo tanto haya un par de coordenadas:
        location_ini = predefined_location.find(".//_0:from/_0:pointCoordinates", namespaces=ns)
        location_fin = predefined_location.find(".//_0:to/_0:pointCoordinates", namespaces=ns)
        
        if location_ini is not None and location_fin is not None:
            latitude_ini = location_ini.find("_0:latitude", namespaces=ns)
            longitude_ini = location_ini.find("_0:longitude", namespaces=ns)
            latitude_fin = location_fin.find("_0:latitude", namespaces=ns)
            longitude_fin = location_fin.find("_0:longitude", namespaces=ns)
            
            if all(v is not None for v in [latitude_ini, longitude_ini, latitude_fin, longitude_fin]):
                radares.append({
                    "radar_id_ini": radar_id_ini,
                    "radar_id_fin": radar_id_fin,
                    "type": "Tramo",
                    "road": road_name,
                    "provincia": provincia,
                    "location_name": location_name,
                    "kilometro": float(kilometro)*1/1000,
                    "sentido_kilometracion": sentido_kilometracion,
                    "latitude_ini": float(latitude_ini.text),
                    "longitude_ini": float(longitude_ini.text),
                    "latitude_fin": float(latitude_fin.text),
                    "longitude_fin": float(longitude_fin.text)
                })
    
    return pd.DataFrame(radares)