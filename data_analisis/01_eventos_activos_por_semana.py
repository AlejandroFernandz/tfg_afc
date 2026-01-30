import os
import pandas as pd

# -----------------
# Config
# -----------------
INPUT_CSV = "data_analisis/output/00_snapshots_eventos_base_nuevo_espanol.csv"
OUTPUT_DIR = "data_analisis/output/"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "01_eventos_activos_por_dia.csv")

COORD_DECIMALS = 5


def build_event_key(row, nd=5):
    """Clave única de evento (punto o tramo, tramo canonizado)."""
    road = str(row.get("road") or "NA")
    prov = str(row.get("provincia") or "NA")

    if bool(row.get("is_segment")):
        a = (round(float(row["latitude_ini"]), nd), round(float(row["longitude_ini"]), nd))
        b = (round(float(row["latitude_fin"]), nd), round(float(row["longitude_fin"]), nd))
        A, B = (a, b) if a <= b else (b, a)
        return f"seg|{road}|{prov}|{A}-{B}"
    else:
        lat = round(float(row["latitude"]), nd)
        lon = round(float(row["longitude"]), nd)
        return f"pt|{road}|{prov}|({lat},{lon})"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV, low_memory=False)

    # Columnas mínimas
    cols = [
        "snapshot_datetime",
        "is_segment",
        "road", "provincia",
        "cause_type",
        "latitude", "longitude",
        "latitude_ini", "longitude_ini",
        "latitude_fin", "longitude_fin",
    ]
    df = df[cols].copy()

    # Datetime
    df["snapshot_datetime"] = pd.to_datetime(df["snapshot_datetime"], utc=True, errors="coerce")

    # Fecha (día)
    df["date"] = df["snapshot_datetime"].dt.date

    # Semana ISO
    iso = df["snapshot_datetime"].dt.isocalendar()
    df["iso_year"] = iso["year"]
    df["iso_week"] = iso["week"]

    # Día de la semana
    df["weekday"] = df["snapshot_datetime"].dt.day_name()
    df["weekday_num"] = df["snapshot_datetime"].dt.weekday  # 0 = lunes

    # Limpieza básica
    df["cause_type"] = df["cause_type"].fillna("Desconocido")

    # Clave de evento único
    df["event_key"] = df.apply(lambda r: build_event_key(r, COORD_DECIMALS), axis=1)

    # 🔹 AGREGADO GENERAL 🔹
    out = (
        df.groupby(
            ["date", "iso_year", "iso_week", "weekday", "weekday_num", "cause_type"],
            dropna=False
        )["event_key"]
        .nunique()
        .reset_index(name="eventos_activos")
        .sort_values("date")
    )

    out.to_csv(OUTPUT_CSV, index=False)
    print(f"[OK] Generado: {OUTPUT_CSV} | filas: {len(out):,}")


if __name__ == "__main__":
    main()
