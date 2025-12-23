# Funciones parser de los datos de trafico y de radares
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import pandas as pd

# EVENTOS DE TRAFICO - PARSER
def parse_datex(file_path="trafico.xml"):
    tree = ET.parse(file_path)
    root = tree.getroot()

    ns = {
        "sit": "http://datex2.eu/schema/3/situation",
        "com": "http://datex2.eu/schema/3/common",
        "loc": "http://datex2.eu/schema/3/locationReferencing"
    }

    events = []

    for situation in root.findall(".//sit:situationRecord", namespaces=ns):
        record_id = situation.get("id")
        event_type = situation.get("{http://www.w3.org/2001/XMLSchema-instance}type", "Unknown").split(":")[-1]
        probability = situation.find("sit:probabilityOfOccurrence", namespaces=ns)
        probability = probability.text if probability is not None else None 
        road = situation.find(".//loc:linearElement/loc:roadNumber", namespaces=ns)
        road = road.text if road is not None else "Desconocido"
        administrative_area_point = situation.find(".//loc:administrativeAreaOfPoint/com:values/com:value", namespaces=ns)
        administrative_area_linear = situation.find(".//loc:administrativeAreaOfLinearSection/com:values/com:value", namespaces=ns)
        provincia = (
            administrative_area_point.text if administrative_area_point is not None
            else administrative_area_linear.text if administrative_area_linear is not None
            else "Desconocida"
        ) 
        severity = situation.find("sit:severity", namespaces=ns).text
        carril_usado = situation.find(".//loc:lane/loc:laneUsage", namespaces=ns)
        carril_usado = carril_usado.text if carril_usado is not None else "Carril original" # No hace falta, siempre va a haber este campo para el tipo de evento management
        kilometro_ini = situation.find(".//loc:fromPoint/loc:distanceAlong", namespaces=ns) # Punto kilometrico en carretera para el inicio del evento de tramo (en metros)
        kilometro_ini = kilometro_ini.text if kilometro_ini is not None else None
        kilometro_fin = situation.find(".//loc:toPoint/loc:distanceAlong", namespaces=ns) # Punto kilometrico en carretera para el final del evento de tramo (en metros)
        kilometro_fin = kilometro_fin.text if kilometro_fin is not None else None
        kilometro = situation.find(".//loc:distanceAlongLinearElement/loc:distanceAlong", namespaces=ns) # kilometro para un evento de punto fijo
        kilometro = kilometro.text if kilometro is not None else None
        sentido_kilometracion_ini = situation.find(".//loc:directionRelativeOnLinearSection", namespaces=ns) # positive = Sentido creciente de la kilometracion, negative = Sentido decreciente de la kilometracion
        sentido_kilometracion_ini = sentido_kilometracion_ini.text if sentido_kilometracion_ini is not None else None
        start_time = situation.find(".//com:validityTimeSpecification/com:overallStartTime", namespaces=ns)
        sentido_kilometracion = situation.find(".//loc:directionRelativeAtPoint", namespaces=ns) # Sentido de la kilometracion para eventos de punto fijo
        sentido_kilometracion = sentido_kilometracion.text if sentido_kilometracion is not None else None


        
        # Formatear la fecha a formato limpio para mostrar en el popup
        # Guardar el objeto datetime real además del formateado
        if start_time is not None:
            start_time_str = start_time.text
            start_time_obj = datetime.fromisoformat(start_time_str)
            formatted_time = start_time_obj.strftime("%H:%M:%S del %d-%m-%y")
        else:
            formatted_time = "Fecha de inicio desconocida"
            start_time_obj = None


        # Traducciones para todos los eventos posibles
        traducciones_severity = {
            "low": "Baja",
            "medium": "Media",
            "high": "Alta",
            "highest": "Muy alta"
        }
        
        traducciones_probabilidad = {
            "riskOf": "riesgo posible",
            "certain": "evento confirmado",
            "probable": "evento probable"
        }

        # Traducciones de tipo de evento
        traducciones_event_type = {
            "ConstructionWorks": "Obras",
            "RoadOrCarriagewayOrLaneManagement": "Desvío temporal",
            "AbnormalTraffic": "Tráfico denso",
            "GeneralObstruction": "Obstrucción de carretera",
            "VehicleObstruction": "Obstrucción por vehículo",
            "PublicEvent": "Evento público",
            "EnvironmentalObstruction": "Obstrucción meteorológica",
            "SpeedManagement": "Gestión de velocidad",
            "PoorEnvironmentConditions": "Malas condiciones meteorológicas",
            "MaintenanceWorks": "Trabajos de mantenimiento",
            "GeneralNetworkManagement": "Gestión general de la carretera",
            "ReroutingManagement": "Gestión de redireccionamiento",
            "NonWeatherRelatedRoadConditions": "Condiciones de carretera no relacionadas con la meteorología",
            "WeatherRelatedRoadConditions": "Condiciones de carretera relacionadas con la meteorología",
            "Winterdrivingmanagement": "Gestión de la conducción invernal",
            "DisturbanceActivity": "Actividad de perturbación",
            "AnimalPresenceObstruction": "Obstrucción por presencia de animales"
        }

        # Traducciones de carril usado
        traducciones_carril = {
            "middleLane": "Carril central",
            "rightLane": "Carril derecho",
            "leftLane": "Carril izquierdo",
            "hardShoulder": "Arcén",
            "centralReservation": "Mediana central entre carriles bidireccionales",
            "turningLane": "Carril de giro",
            "carPoolLane": "Carril compartido"
        }

        # Traducciones de sentido de la kilometración
        traducciones_sentido = {
            "both": "Ambos",
            "aligned": "Creciente a la kilometración",
            "opposite": "Decreciente a la kilometración"
        }

        # Aplicación de las traducciones con get()
        event_type = traducciones_event_type.get(event_type, event_type)
        carril_usado = traducciones_carril.get(carril_usado, carril_usado)
        sentido_kilometracion_ini = traducciones_sentido.get(sentido_kilometracion_ini, sentido_kilometracion_ini)
        sentido_kilometracion = traducciones_sentido.get(sentido_kilometracion, sentido_kilometracion)
        probability = traducciones_probabilidad.get(probability, "desconocida")
        severity = traducciones_severity.get(severity, "desconocida")
    




        for location_ref in situation.findall(".//sit:locationReference", namespaces=ns):
            location_name_tag = location_ref.find(".//loc:descriptor/com:values/com:value", namespaces=ns)
            location_name = location_name_tag.text if location_name_tag is not None else "Desconocido"
            # Para los EVENTOS FIJOS (un solo par de coordenadas)
            location_point = location_ref.find(".//loc:pointByCoordinates/loc:pointCoordinates", namespaces=ns)
            if location_point is not None:
                latitude = location_point.find("loc:latitude", namespaces=ns)
                longitude = location_point.find("loc:longitude", namespaces=ns)
                if latitude is not None and longitude is not None:
                    events.append({
                        "id": record_id,
                        "road": road,
                        "start_time": formatted_time,
                        "type": event_type,
                        "probability": probability,
                        "severity": severity if severity is not None else "Desconocido",
                        "locality": location_name,
                        "latitude": float(latitude.text),
                        "longitude": float(longitude.text),
                        "carril_usado": carril_usado,
                        "kilometro": float(kilometro)*1/1000 if kilometro is not None else "Km desconocido",
                        "sentido_kilometracion": sentido_kilometracion,
                        "provincia": provincia,
                        "start_time_obj": start_time_obj

                        
                    })
            # En el caso de que sea un EVENTO DE TRAMO, y que por lo tanto haya un par de coordenadas:
            location_ini = location_ref.find(".//loc:from/loc:pointCoordinates", namespaces=ns)
            location_fin = location_ref.find(".//loc:to/loc:pointCoordinates", namespaces=ns)
            
            if location_ini is not None and location_fin is not None:
                latitude_ini = location_ini.find("loc:latitude", namespaces=ns)
                longitude_ini = location_ini.find("loc:longitude", namespaces=ns)
                latitude_fin = location_fin.find("loc:latitude", namespaces=ns)
                longitude_fin = location_fin.find("loc:longitude", namespaces=ns)
                
                if all(v is not None for v in [latitude_ini, longitude_ini, latitude_fin, longitude_fin]):
                    events.append({
                        "id": record_id,
                        "road": road,
                        "start_time": formatted_time,
                        "type": event_type,
                        "probability": probability,
                        "severity": severity if severity is not None else "Unknown",
                        "locality": location_name,
                        "latitude_ini": float(latitude_ini.text),
                        "longitude_ini": float(longitude_ini.text),
                        "latitude_fin": float(latitude_fin.text),
                        "longitude_fin": float(longitude_fin.text),
                        "carril_usado": carril_usado,
                        "kilometro_ini": float(kilometro_ini)*1/1000 if kilometro_ini is not None else "Km inicio desconocido",
                        "kilometro_fin": float(kilometro_fin)*1/1000 if kilometro_fin is not None else "Km fin desconocido",
                        "sentido_kilometracion_ini": sentido_kilometracion_ini if sentido_kilometracion_ini is not None else "Sentido desconocido",
                        "provincia": provincia,
                        "start_time_obj": start_time_obj


                    })
        
    return pd.DataFrame(events)


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

        kilometro = predefined_location.find(".//_0:referencePointDistance", namespaces=ns).text # Punto kilometrico en carretera para RADAR FIJO y RADAR DE TRAMO

        sentido_kilometracion = predefined_location.find(".//_0:directionRelative", namespaces=ns).text # Sentido RADAR FIJO y RADAR DE TRAMO
        if sentido_kilometracion == "negative":
            sentido_kilometracion = "Decreciente de la kilometración"
        else:
            sentido_kilometracion = "Creciente de la kilometracion"
        
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
                    "kilometro": float(kilometro)*1/1000,
                    "sentido_kilometracion": sentido_kilometracion,
                    "latitude_ini": float(latitude_ini.text),
                    "longitude_ini": float(longitude_ini.text),
                    "latitude_fin": float(latitude_fin.text),
                    "longitude_fin": float(longitude_fin.text)
                })
    
    return pd.DataFrame(radares)