import os
import glob
import pandas as pd
from tqdm import tqdm

# Importa el parser histórico enriquecido
from data_analisis.antiguo.parser_antiguo import parse_datex_historico_enriquecido


def normalizar_texto(valor):
    if pd.isna(valor):
        return None
    texto = (
        str(valor)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
        .replace("ñ", "n")
    )
    if "," in texto:
        partes = [p.strip() for p in texto.split(",")]
        texto = " ".join(reversed(partes))
    return texto.title()


def main():
    input_dir = "data/xml_historicos"
    output_dir = "datasets_generados/nuevo"
    os.makedirs(output_dir, exist_ok=True)

    xml_paths = sorted(glob.glob(os.path.join(input_dir, "*.xml")))
    if not xml_paths:
        raise FileNotFoundError(f"No se encontraron XML en {input_dir}/")

    all_dfs = []

    for path in tqdm(xml_paths, desc="Procesando snapshots XML"):
        try:
            df = parse_datex_historico_enriquecido(path)
            if df is None or df.empty:
                continue

            # Normalización (para Power BI)
            for col in ["provincia", "locality", "locality_ini", "locality_fin", "road", "type", "cause_type", "cause_detail"]:
                if col in df.columns:
                    df[col] = df[col].apply(normalizar_texto)

            all_dfs.append(df)

        except Exception as e:
            print(f"[WARN] Error procesando {os.path.basename(path)}: {e}")

    if not all_dfs:
        raise RuntimeError("No se generó ningún dataframe. Revisa que los XML tengan situationRecords válidos.")

    df_base = pd.concat(all_dfs, ignore_index=True)

    # -----------------------------
    # ✅ DATASET BASE (snapshots)
    # -----------------------------
    # Importante: ESTE CSV TIENE EVENTOS REPETIDOS.
    # Si un evento (mismo id) aparece en 10 snapshots, tendrás 10 filas (una por snapshot).
    base_path = os.path.join(output_dir, "00_snapshots_eventos_base_nuevo_espanol.csv")
    df_base.to_csv(base_path, index=False)
    print(f"[OK] CSV base generado: {base_path}")
    print(f"     Filas: {len(df_base):,} | Eventos únicos (por id): {df_base['id'].nunique():,}")

if __name__ == "__main__":
    main()
