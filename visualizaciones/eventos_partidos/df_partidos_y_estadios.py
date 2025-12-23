import pandas as pd

# ------------------------------
# Función de normalización
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
# ------------------------------

# Cargar partidos de primera división
df1 = pd.read_csv('data/SP1.csv', delimiter=',')
df_partidos_primera = df1[["Div", "Date", "Time", "HomeTeam", "AwayTeam"]].copy()

estadios_primera = {
    "Ath Bilbao": "San Mames", "Betis": "Benito Villamarin", "Celta": "Balaidos",
    "Las Palmas": "Estadio de Gran Canaria", "Osasuna": "El Sadar", "Leganes": "Butarque",
    "Sevilla": "Sanchez Pizjuan", "Getafe": "Coliseum", "Vallecano": "Vallecas",
    "Alaves": "Mendizorroza", "Valencia": "Mestalla", "Sociedad": "Anoeta",
    "Mallorca": "Son Moix", "Valladolid": "Jose Zorrilla", "Villarreal": "Ceramica",
    "Barcelona": "Montjuic", "Espanol": "RCDE Stadium", "Real Madrid": "Santiago Bernabeu",
    "Ath Madrid": "Metropolitano", "Girona": "Montilivi"
}
df_partidos_primera["Estadio"] = df_partidos_primera["HomeTeam"].map(estadios_primera)

# Cargar partidos de segunda división
df2 = pd.read_csv('data/SP2.csv', delimiter=',')
df_partidos_segunda = df2[["Div", "Date", "Time", "HomeTeam", "AwayTeam"]].copy()

estadios_segunda = {
    "Granada": "Los Carmenes", "Mirandes": "Municipal de Anduva", "Cadiz": "Nuevo Mirandilla",
    "Eibar": "Ipurua", "Ferrol": "A Malata", "La Coruna": "Riazor", "Santander": "El Sardinero",
    "Sp Gijon": "El Molinon", "Burgos": "El Plantio", "Elche": "Valero", "Eldense": "Pepico Amat",
    "Huesca": "El Alcoraz", "Levante": "Ciutat de Valencia", "Malaga": "La Rosaleda",
    "Tenerife": "Heliodoro", "Albacete": "Carlos Belmonte", "Castellon": "Castalia",
    "Cartagena": "Cartagonova", "Cordoba": "Arcangel", "Oviedo": "Carlos Tartiere",
    "Almeria": "Power Horse", "Zaragoza": "La Romareda"
}
df_partidos_segunda["Estadio"] = df_partidos_segunda["HomeTeam"].map(estadios_segunda)

# Unir ambos datasets
df_partidos = pd.concat([df_partidos_primera, df_partidos_segunda], ignore_index=True)

# Normalizar equipos y estadios
for col in ["HomeTeam", "AwayTeam", "Estadio"]:
    df_partidos[col] = df_partidos[col].apply(normalizar_texto)

# Coordenadas de estadios
estadios_coords = [
    ["San Mames",43.2643, -2.9493], ["Benito Villamarin",37.3568,-5.9817], ["Balaidos",42.2120, -8.7398],
    ["Estadio De Gran Canaria", 28.1006, -15.4567], ["El Sadar",42.7969, -1.6372], ["Butarque",40.3408, -3.7608],
    ["Sanchez Pizjuan", 37.3845, -5.9711], ["Coliseum", 40.3260, -3.7151], ["Vallecas", 40.3922,-3.6587],
    ["Mendizorroza", 42.8374, -2.6883], ["Mestalla", 39.4751, -0.3588], ["Anoeta",43.3017, -1.9735],
    ["Son Moix", 39.5901, 2.6301], ["Jose Zorrilla", 41.6448, -4.7612], ["Ceramica", 39.9440, -0.1031],
    ["Montjuic", 41.3649, 2.1557], ["Rcde Stadium", 41.3483, 2.0747], ["Santiago Bernabeu", 40.4531, -3.6884],
    ["Metropolitano", 40.4364, -3.5995], ["Montilivi", 41.9611, 2.8277], ["Los Carmenes", 37.1530, -3.5957],
    ["Municipal De Anduva", 42.6810, -2.9354], ["Nuevo Mirandilla", 36.5027, -6.2727], ["Ipurua", 43.1819, -2.4758],
    ["A Malata", 43.4915, -8.2399], ["Riazor", 43.3686, -8.4166], ["El Sardinero", 43.4765, -3.7927],
    ["El Molinon", 43.5365, -5.6366], ["El Plantio", 42.3444, -3.6803], ["Valero", 38.2674, -0.6622],
    ["Pepico Amat", 38.4677, -0.7962], ["El Alcoraz", 42.1321, -0.4247], ["Ciutat De Valencia", 39.4947, -0.3629],
    ["La Rosaleda", 36.7337, -4.4262], ["Heliodoro", 28.4634, -16.2601], ["Carlos Belmonte", 38.9811, -1.8528],
    ["Castalia", 39.9963, -0.0383], ["Cartagonova", 37.6099, -0.9953], ["Arcangel", 37.8724, -4.7641],
    ["Carlos Tartiere", 43.3608, -5.8691], ["Power Horse", 36.8402, -2.4347], ["La Romareda", 41.6366, -0.9018]
]

# Normalizar nombres de estadios en coordenadas
df_estadios = pd.DataFrame(estadios_coords, columns=["Estadio", "Latitud", "Longitud"])
df_estadios["Estadio"] = df_estadios["Estadio"].apply(normalizar_texto)

# Unir coordenadas con partidos
df_partidos = df_partidos.merge(df_estadios, on="Estadio", how="left")

def clasificar_partido(row):
    equipos_top = ["real madrid", "barcelona", "ath madrid", "betis", "sevilla", "ath bilbao", "real sociedad"]
    local = row["HomeTeam"].lower()
    visitante = row["AwayTeam"].lower()

    # Clásico
    if ("Real Madrid" in [local, visitante]) and ("Barcelona" in [local, visitante]):
        return "Clasico"
    if ("Sociedad" in [local, visitante]) and ("Ath Bilbao" in [local, visitante]):
        return "Clasico"

    # Derbi Sevilla
    if ("betis" in [local, visitante]) and ("sevilla" in [local, visitante]):
        return "Derbi Andaluz"

    # No esta registrado ninguno de los dos partidos del derbi madrileño
    # Alta intensidad
    if local in equipos_top and visitante in equipos_top:
        return "Top Match"

    return "Normal"

df_partidos["Importancia"] = df_partidos.apply(clasificar_partido, axis=1)


# Guardar en CSV
df_partidos.to_csv("visualizaciones/eventos_partidos/partidos_estadios.csv", index=False, encoding="utf-8")
print(f"[✅] Exportado a visualizaciones/eventos_partidos/partidos_estadios.csv con {len(df_partidos)} partidos.")
