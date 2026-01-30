import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
from zoneinfo import ZoneInfo


NS = {
    "d2": "http://datex2.eu/schema/3/d2Payload",
    "sit": "http://datex2.eu/schema/3/situation",
    "com": "http://datex2.eu/schema/3/common",
    "loc": "http://datex2.eu/schema/3/locationReferencing",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def _txt(node, default=None):
    return node.text.strip() if node is not None and node.text is not None else default


def _attr(node, attr, default=None):
    return node.get(attr, default) if node is not None else default

def _parse_iso(dt_str):
    """Devuelve datetime (naive) si parsea, si no None."""
    if not dt_str:
        return None
    try:
        # fromisoformat soporta offsets tipo +02:00
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None

def _parse_iso_to_utc(dt_str):
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str)  # suele venir aware por el +02:00
        if dt.tzinfo is None:
            # por si algún día viniera sin tz: asumimos Madrid
            dt = dt.replace(tzinfo=ZoneInfo("Europe/Madrid"))
        return dt.astimezone(ZoneInfo("UTC"))
    except Exception:
        return None

SPAIN_TZ = ZoneInfo("Europe/Madrid")
def infer_snapshot_datetime_from_filename(path: str):
    """
    Nombre: dgt_YYYYMMDD_HHMMSS.xml  -> snapshot local Europe/Madrid
    Ej: dgt_20250313_120145.xml => 2025-03-13 12:01:45 (Madrid)
    Devuelve datetime timezone-aware en UTC (recomendado para BI)
    """
    name = os.path.basename(path)

    m = re.search(r"dgt_(\d{8})_(\d{6})\.xml$", name, re.IGNORECASE)
    if not m:
        return None

    yyyymmdd = m.group(1)
    hhmmss = m.group(2)

    y = int(yyyymmdd[0:4])
    mo = int(yyyymmdd[4:6])
    d = int(yyyymmdd[6:8])

    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])

    dt_local = datetime(y, mo, d, hh, mm, ss, tzinfo=SPAIN_TZ)
    return dt_local.astimezone(ZoneInfo("UTC"))


def _extract_type_tag_value(situation_record):
    """
    Busca el 'subtipo' según el record_xsi_type:
    p.ej. ConstructionWorks -> sit:constructionWorkType
         GeneralObstruction -> sit:obstructionType
         EnvironmentalObstruction -> sit:environmentalObstructionType
         PoorEnvironmentConditions -> sit:poorEnvironmentType
         AbnormalTraffic -> sit:abnormalTrafficType
         ...
    Devuelve (type_tag, type_value) o (None, None)
    """
    # preferimos: primer hijo tag que acabe en "Type" y tenga texto
    for child in list(situation_record):
        tag = child.tag.split("}")[-1]  # sin namespace
        if tag.endswith("Type"):
            val = _txt(child)
            if val:
                return tag, val
    return None, None


def parse_datex_historico_enriquecido(file_path: str) -> pd.DataFrame:
    tree = ET.parse(file_path)
    root = tree.getroot()

    # publicationTime del payload
    publication_time = root.find(".//com:publicationTime", NS)
    publication_time = _parse_iso(_txt(publication_time))

    snapshot_datetime = infer_snapshot_datetime_from_filename(file_path)

    rows = []

    for record in root.findall(".//sit:situationRecord", NS):
        record_id = _attr(record, "id")
        record_version = _attr(record, "version")

        xsi_type = _attr(record, "{http://www.w3.org/2001/XMLSchema-instance}type", "Unknown")
        record_xsi_type = xsi_type.split(":")[-1] if xsi_type else "Unknown"

        probability = _txt(record.find("sit:probabilityOfOccurrence", NS))
        severity = _txt(record.find("sit:severity", NS))
        validity_status = _txt(record.find(".//sit:validity/com:validityStatus", NS))

        record_creation_time = _parse_iso(_txt(record.find("sit:situationRecordCreationTime", NS)))
        record_version_time = _parse_iso(_txt(record.find("sit:situationRecordVersionTime", NS)))
        overall_start_time = _parse_iso(_txt(record.find(".//com:validityTimeSpecification/com:overallStartTime", NS)))

        # Carretera + provincia
        road = _txt(record.find(".//loc:linearElement/loc:roadNumber", NS))
        admin_point = record.find(".//loc:administrativeAreaOfPoint/com:values/com:value", NS)
        admin_linear = record.find(".//loc:administrativeAreaOfLinearSection/com:values/com:value", NS)
        provincia = _txt(admin_point) or _txt(admin_linear)

        # lane usage
        carril_usado = _txt(record.find(".//loc:lane/loc:laneUsage", NS))

        # kilometración punto y tramo
        km_point_m = _txt(record.find(".//loc:distanceAlongLinearElement/loc:distanceAlong", NS))
        km_ini_m = _txt(record.find(".//loc:fromPoint/loc:distanceAlong", NS))
        km_fin_m = _txt(record.find(".//loc:toPoint/loc:distanceAlong", NS))

        # sentido
        sentido_point = _txt(record.find(".//loc:directionRelativeAtPoint", NS))
        sentido_ini = _txt(record.find(".//loc:directionRelativeOnLinearSection", NS))

        type_tag, type_value = _extract_type_tag_value(record)

        # Puede haber 1..n locationReference por record; tu base debería “explotar” si ocurre.
        location_refs = record.findall(".//sit:locationReference", NS)
        if not location_refs:
            # aun así guardamos una fila “sin geometría”
            rows.append({
                "id": record_id,
                "version": record_version,
                "record_xsi_type": record_xsi_type,
                "type_tag": type_tag,
                "type_value": type_value,
                "probability": probability,
                "severity": severity,
                "validity_status": validity_status,
                "road": road,
                "provincia": provincia,
                "carril_usado": carril_usado,
                "sentido_kilometracion": sentido_point,
                "sentido_kilometracion_ini": sentido_ini,
                "kilometro": float(km_point_m)/1000 if km_point_m else None,
                "kilometro_ini": float(km_ini_m)/1000 if km_ini_m else None,
                "kilometro_fin": float(km_fin_m)/1000 if km_fin_m else None,
                "geometry_type": None,
                "locality": None,
                "locality_ini": None,
                "locality_fin": None,
                "latitude": None,
                "longitude": None,
                "latitude_ini": None,
                "longitude_ini": None,
                "latitude_fin": None,
                "longitude_fin": None,
                "overall_start_time": overall_start_time,
                "record_creation_time": record_creation_time,
                "record_version_time": record_version_time,
                "publication_time": publication_time,
                "snapshot_datetime": snapshot_datetime,
                "snapshot_file": os.path.basename(file_path),
            })
            continue

        for locref in location_refs:
            # nombre (descriptor)
            loc_name = locref.find(".//loc:descriptor/com:values/com:value", NS)
            locality = _txt(loc_name)

            # Punto
            point = locref.find(".//loc:pointByCoordinates/loc:pointCoordinates", NS)
            if point is not None:
                lat = _txt(point.find("loc:latitude", NS))
                lon = _txt(point.find("loc:longitude", NS))
                rows.append({
                    "id": record_id,
                    "version": record_version,
                    "record_xsi_type": record_xsi_type,
                    "type_tag": type_tag,
                    "type_value": type_value,
                    "probability": probability,
                    "severity": severity,
                    "validity_status": validity_status,
                    "road": road,
                    "provincia": provincia,
                    "carril_usado": carril_usado,
                    "sentido_kilometracion": sentido_point,
                    "sentido_kilometracion_ini": sentido_ini,
                    "kilometro": float(km_point_m)/1000 if km_point_m else None,
                    "kilometro_ini": None,
                    "kilometro_fin": None,
                    "geometry_type": "point",
                    "locality": locality,
                    "locality_ini": None,
                    "locality_fin": None,
                    "latitude": float(lat) if lat else None,
                    "longitude": float(lon) if lon else None,
                    "latitude_ini": None,
                    "longitude_ini": None,
                    "latitude_fin": None,
                    "longitude_fin": None,
                    "overall_start_time": overall_start_time,
                    "record_creation_time": record_creation_time,
                    "record_version_time": record_version_time,
                    "publication_time": publication_time,
                    "snapshot_datetime": snapshot_datetime,
                    "snapshot_file": os.path.basename(file_path),
                })
                continue

            # Tramo (from/to)
            ini = locref.find(".//loc:from/loc:pointCoordinates", NS)
            fin = locref.find(".//loc:to/loc:pointCoordinates", NS)
            if ini is not None and fin is not None:
                lat_i = _txt(ini.find("loc:latitude", NS))
                lon_i = _txt(ini.find("loc:longitude", NS))
                lat_f = _txt(fin.find("loc:latitude", NS))
                lon_f = _txt(fin.find("loc:longitude", NS))

                loc_ini_name = locref.find(".//loc:from//loc:name/loc:descriptor/com:values/com:value", NS)
                loc_fin_name = locref.find(".//loc:to//loc:name/loc:descriptor/com:values/com:value", NS)

                rows.append({
                    "id": record_id,
                    "version": record_version,
                    "record_xsi_type": record_xsi_type,
                    "type_tag": type_tag,
                    "type_value": type_value,
                    "probability": probability,
                    "severity": severity,
                    "validity_status": validity_status,
                    "road": road,
                    "provincia": provincia,
                    "carril_usado": carril_usado,
                    "sentido_kilometracion": None,
                    "sentido_kilometracion_ini": sentido_ini,
                    "kilometro": None,
                    "kilometro_ini": float(km_ini_m)/1000 if km_ini_m else None,
                    "kilometro_fin": float(km_fin_m)/1000 if km_fin_m else None,
                    "geometry_type": "segment",
                    "locality": locality,
                    "locality_ini": _txt(loc_ini_name),
                    "locality_fin": _txt(loc_fin_name),
                    "latitude": None,
                    "longitude": None,
                    "latitude_ini": float(lat_i) if lat_i else None,
                    "longitude_ini": float(lon_i) if lon_i else None,
                    "latitude_fin": float(lat_f) if lat_f else None,
                    "longitude_fin": float(lon_f) if lon_f else None,
                    "overall_start_time": overall_start_time,
                    "record_creation_time": record_creation_time,
                    "record_version_time": record_version_time,
                    "publication_time": publication_time,
                    "snapshot_datetime": snapshot_datetime,
                    "snapshot_file": os.path.basename(file_path),
                })

    df = pd.DataFrame(rows)

    # Normaliza fechas como datetime (Power BI se lleva mejor esto que strings raros)
    for c in ["publication_time", "snapshot_datetime", "overall_start_time", "record_creation_time", "record_version_time"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], utc=True, errors="coerce")

    return df
