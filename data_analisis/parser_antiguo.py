import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import pandas as pd


# =========================
# Traducciones (ajusta/une a las tuyas si ya las tienes en app/parsing.py)
# =========================

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

TRAD_CAUSE_DETAIL = {
    # Obstrucciones
    "objectOnTheRoad": "Objeto en la vía",
    "vehicleStuck": "Vehículo atascado",
    "vehicleOnFire": "Vehículo en llamas",
    "animalsOnTheRoad": "Animales en la calzada",
    "brokenDownVehicle": "Vehículo averiado",
    "damagedVehicle": "Vehículo dañado",
    "shedLoad": "Carga caída",
    "peopleOnRoadway": "Personas en la calzada",
    "spillageOnTheRoad": "Derrame en la calzada",

    # Tráfico / accidentes
    "accident": "Accidente",
    "seriousAccident": "Accidente grave",
    "multiVehicleAccident": "Accidente múltiple",

    # Obras / mantenimiento / gestión
    "constructionWork": "Obras",
    "maintenanceWork": "Trabajos de mantenimiento",
    "roadworks": "Obras",
    "maintenanceWorks": "Trabajos de mantenimiento",
    "resurfacing": "Reasfaltado",
    "laneClosures": "Cierre de carriles",
    "roadClosed": "Carretera cortada",
    "singleAlternateLineTraffic": "Tráfico alternativo",
    "narrowLanes": "Carriles estrechos",
    "intermittentShortTermClosures": "Cierres intermitentes",
    "doNotUseSpecifiedLanesOrCarriageways": "No usar carriles especificados",
    "REDACTED_AWS_SECRET_ACCESS_KEY": "Uso permitido carriles especificados",
    "weightRestrictionInOperation": "Restricción de peso",
    "contraflow": "Sentido contrario habilitado",
    "tidalFlowLaneInOperation": "Carril reversible activo",

    # Meteorología / condiciones
    "rain": "Lluvia",
    "heavyRain": "Lluvias intensas",
    "snow": "Nieve",
    "snowfall": "Nevada",
    "ice": "Hielo",
    "fog": "Niebla",
    "visibilityReduced": "Visibilidad reducida",
    "strongWinds": "Viento fuerte",
    "blowingDust": "Polvo en suspensión",
    "smokeHazard": "Humo",
    "hail": "Granizo",

    # Ambiental / infraestructura / calzada
    "flooding": "Inundación",
    "rockfalls": "Desprendimientos",
    "roadSurfaceInPoorCondition": "Firme en mal estado",
}


# =========================
# Helpers
# =========================

def _text(el):
    return el.text.strip() if (el is not None and el.text and el.text.strip()) else None


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _iso_to_utc(dt_str: str):
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo:
            return dt.astimezone(timezone.utc)
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _extract_publication_time(root, ns):
    pub = root.find(".//com:publicationTime", namespaces=ns)
    pub_str = _text(pub)
    return _iso_to_utc(pub_str)


def _parse_snapshot_datetime_from_filename(snapshot_file: str):
    """
    dgt_YYYYMMDD_HHMMSS.xml -> datetime UTC (naive->UTC)
    """
    base = os.path.basename(snapshot_file)
    m = re.search(r"dgt_(\d{8})_(\d{6})\.xml$", base)
    if not m:
        return None
    ymd, hms = m.group(1), m.group(2)
    try:
        dt = datetime.strptime(ymd + hms, "%Y%m%d%H%M%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _extract_provincia_old(situation, ns):
    administrative_area_point = situation.find(
        ".//loc:administrativeAreaOfPoint/com:values/com:value", namespaces=ns
    )
    administrative_area_linear = situation.find(
        ".//loc:administrativeAreaOfLinearSection/com:values/com:value", namespaces=ns
    )
    return _text(administrative_area_point) or _text(administrative_area_linear) or "Desconocida"


def _extract_road_old(situation, ns):
    road = situation.find(".//loc:linearElement/loc:roadNumber", namespaces=ns)
    return _text(road) or "Desconocido"


def _extract_locality_point_old(location_ref, ns):
    tpeg_name = location_ref.find(
        ".//loc:tpegPointLocation//loc:name/loc:descriptor/com:values/com:value",
        namespaces=ns,
    )
    if _text(tpeg_name):
        return _text(tpeg_name)

    desc = location_ref.find(".//loc:descriptor/com:values/com:value", namespaces=ns)
    if _text(desc):
        return _text(desc)

    return "Desconocido"


def _extract_locality_segment_old(location_ref, ns):
    ini = location_ref.find(
        ".//loc:from//loc:name/loc:descriptor/com:values/com:value", namespaces=ns
    )
    fin = location_ref.find(
        ".//loc:to//loc:name/loc:descriptor/com:values/com:value", namespaces=ns
    )
    return (_text(ini) or "Desconocido", _text(fin) or "Desconocido")


def _extract_cause_old(situation, ns):
    """
    XML viejo: no hay sit:cause; hay tags específicos por tipo.
    Devuelve: (cause_type_raw, cause_detail_raw)
    """
    record_xsi_type = situation.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
    record_xsi_type = record_xsi_type.split(":")[-1] if record_xsi_type else "Unknown"

    CAUSE_MAP = {
        "VehicleObstruction": ("vehicleObstructionType", "vehicleObstruction"),
        "GeneralObstruction": ("obstructionType", "obstruction"),
        "AnimalPresenceObstruction": ("animalPresenceType", "obstruction"),

        "AbnormalTraffic": ("abnormalTrafficType", "abnormalTraffic"),
        "DisturbanceActivity": ("disturbanceActivityType", "abnormalTraffic"),
        "PublicEvent": ("publicEventType", "abnormalTraffic"),

        "PoorEnvironmentConditions": ("poorEnvironmentType", "poorEnvironment"),
        "EnvironmentalObstruction": ("environmentalObstructionType", "environmentalObstruction"),
        "NonWeatherRelatedRoadConditions": ("nonWeatherRelatedRoadConditionType", "poorEnvironment"),
        "WeatherRelatedRoadConditions": ("weatherRelatedRoadConditionType", "poorEnvironment"),
        "WinterDrivingManagement": ("winterEquipmentManagementType", "poorEnvironment"),

        "ConstructionWorks": ("constructionWorkType", "roadMaintenance"),
        "MaintenanceWorks": ("roadMaintenanceType", "roadMaintenance"),

        "RoadOrCarriagewayOrLaneManagement": ("roadOrCarriagewayOrLaneManagementType", "roadOrCarriagewayOrLaneManagement"),
        "SpeedManagement": ("speedManagementType", "roadOrCarriagewayOrLaneManagement"),
        "GeneralNetworkManagement": ("generalNetworkManagementType", "roadOrCarriagewayOrLaneManagement"),
        "ReroutingManagement": ("reroutingManagementType", "roadOrCarriagewayOrLaneManagement"),
    }

    if record_xsi_type not in CAUSE_MAP:
        return record_xsi_type, None

    tag_name, cause_type_raw = CAUSE_MAP[record_xsi_type]
    el = situation.find(f"sit:{tag_name}", namespaces=ns)
    cause_detail_raw = _text(el)

    return cause_type_raw, cause_detail_raw


# =========================
# Parser principal
# =========================

def parse_datex_historico_enriquecido(file_path: str) -> pd.DataFrame:
    """
    Lee XML histórico (datex2.eu/schema/3/...) y devuelve DF con:
    - snapshot_file, snapshot_datetime, publication_time
    - columnas de eventos (punto o tramo)
    - cause_type/cause_detail aproximados al parser nuevo (a partir de tags específicos)
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    ns = {
        "sit": "http://datex2.eu/schema/3/situation",
        "com": "http://datex2.eu/schema/3/common",
        "loc": "http://datex2.eu/schema/3/locationReferencing",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    publication_time = _extract_publication_time(root, ns)
    snapshot_dt = _parse_snapshot_datetime_from_filename(file_path)
    snapshot_file = os.path.basename(file_path)

    rows = []

    for situation in root.findall(".//sit:situationRecord", namespaces=ns):
        record_id = situation.get("id")

        record_xsi_type = situation.get("{http://www.w3.org/2001/XMLSchema-instance}type", "Unknown")
        record_xsi_type = record_xsi_type.split(":")[-1] if record_xsi_type else "Unknown"

        probability = _text(situation.find("sit:probabilityOfOccurrence", namespaces=ns))
        severity = _text(situation.find("sit:severity", namespaces=ns))

        # start time
        start_time_el = situation.find(".//com:validityTimeSpecification/com:overallStartTime", namespaces=ns)
        start_time_str = _text(start_time_el)
        start_time_obj = _iso_to_utc(start_time_str)
        start_time_fmt = start_time_obj.strftime("%H:%M:%S del %d-%m-%y") if start_time_obj else "Fecha de inicio desconocida"

        road = _extract_road_old(situation, ns)
        provincia = _extract_provincia_old(situation, ns)

        carril_usado = _text(situation.find(".//loc:lane/loc:laneUsage", namespaces=ns)) or "Carril original"

        # kms
        km_ini_m = _text(situation.find(".//loc:fromPoint/loc:distanceAlong", namespaces=ns))
        km_fin_m = _text(situation.find(".//loc:toPoint/loc:distanceAlong", namespaces=ns))
        km_point_m = _text(situation.find(".//loc:distanceAlongLinearElement/loc:distanceAlong", namespaces=ns))

        km_ini = (_safe_float(km_ini_m) / 1000) if km_ini_m is not None else None
        km_fin = (_safe_float(km_fin_m) / 1000) if km_fin_m is not None else None
        km_point = (_safe_float(km_point_m) / 1000) if km_point_m is not None else None

        # sentidos
        sentido_tramo = _text(situation.find(".//loc:directionRelativeOnLinearSection", namespaces=ns))
        sentido_punto = _text(situation.find(".//loc:directionRelativeAtPoint", namespaces=ns))

        # cause
        cause_type_raw, cause_detail_raw = _extract_cause_old(situation, ns)
        cause_type = TRAD_CAUSE_TYPE.get(cause_type_raw, cause_type_raw) if cause_type_raw else None
        cause_detail = TRAD_CAUSE_DETAIL.get(cause_detail_raw, cause_detail_raw) if cause_detail_raw else None

        icon_code = cause_type_raw or record_xsi_type

        for location_ref in situation.findall(".//sit:locationReference", namespaces=ns):
            # PUNTO
            point_coords = location_ref.find(".//loc:pointByCoordinates/loc:pointCoordinates", namespaces=ns)
            if point_coords is not None:
                lat = _text(point_coords.find("loc:latitude", namespaces=ns))
                lon = _text(point_coords.find("loc:longitude", namespaces=ns))
                if lat and lon:
                    locality = _extract_locality_point_old(location_ref, ns)
                    rows.append({
                        "snapshot_file": snapshot_file,
                        "snapshot_datetime": snapshot_dt,
                        "publication_time": publication_time,

                        "id": record_id,
                        "type_record_code": record_xsi_type,
                        "type_code": record_xsi_type,
                        "type": record_xsi_type,
                        "icon_code": icon_code,

                        "cause_type_raw": cause_type_raw,
                        "cause_type": cause_type,
                        "cause_detail_raw": cause_detail_raw,
                        "cause_detail": cause_detail,

                        "probability": probability,
                        "severity": severity,

                        "road": road,
                        "provincia": provincia,
                        "locality": locality,

                        "latitude": float(lat),
                        "longitude": float(lon),

                        "kilometro": km_point if km_point is not None else None,
                        "sentido_kilometracion": sentido_punto,

                        "carril_usado": carril_usado,

                        "start_time": start_time_fmt,
                        "start_time_obj": start_time_obj,

                        "is_segment": False,
                    })
                continue

            # TRAMO
            from_coords = location_ref.find(".//loc:from/loc:pointCoordinates", namespaces=ns)
            to_coords = location_ref.find(".//loc:to/loc:pointCoordinates", namespaces=ns)

            if from_coords is not None and to_coords is not None:
                lat_ini = _text(from_coords.find("loc:latitude", namespaces=ns))
                lon_ini = _text(from_coords.find("loc:longitude", namespaces=ns))
                lat_fin = _text(to_coords.find("loc:latitude", namespaces=ns))
                lon_fin = _text(to_coords.find("loc:longitude", namespaces=ns))

                if all([lat_ini, lon_ini, lat_fin, lon_fin]):
                    loc_ini, loc_fin = _extract_locality_segment_old(location_ref, ns)

                    rows.append({
                        "snapshot_file": snapshot_file,
                        "snapshot_datetime": snapshot_dt,
                        "publication_time": publication_time,

                        "id": record_id,
                        "type_record_code": record_xsi_type,
                        "type_code": record_xsi_type,
                        "type": record_xsi_type,
                        "icon_code": icon_code,

                        "cause_type_raw": cause_type_raw,
                        "cause_type": cause_type,
                        "cause_detail_raw": cause_detail_raw,
                        "cause_detail": cause_detail,

                        "probability": probability,
                        "severity": severity,

                        "road": road,
                        "provincia": provincia,
                        "locality_ini": loc_ini,
                        "locality_fin": loc_fin,

                        "latitude_ini": float(lat_ini),
                        "longitude_ini": float(lon_ini),
                        "latitude_fin": float(lat_fin),
                        "longitude_fin": float(lon_fin),

                        "kilometro_ini": km_ini if km_ini is not None else None,
                        "kilometro_fin": km_fin if km_fin is not None else None,

                        "sentido_kilometracion_ini": sentido_tramo,
                        "sentido_kilometracion": sentido_tramo,

                        "carril_usado": carril_usado,

                        "start_time": start_time_fmt,
                        "start_time_obj": start_time_obj,

                        "is_segment": True,
                    })

    df = pd.DataFrame(rows)

    # Normaliza datetimes
    if not df.empty:
        for col in ["snapshot_datetime", "publication_time", "start_time_obj"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    return df
