import time
import shutil

def safe_replace(src, dst, retries=5, delay=1):
    for i in range(retries):
        try:
            shutil.move(src, dst)
            return
        except PermissionError as e:
            print(f"[WARN] Intento {i+1}: no se pudo reemplazar el archivo. Reintentando en {delay}s...")
            time.sleep(delay)
    print(f"[ERROR] Fallo definitivo al mover {src} -> {dst}")

# Funcion para asignar un icono distinto a los popups en base al tipo de EVENTO:
def icono_por_tipo(tipo_evento):
    icon_map = {
        "Obras": ("person-digging", "orange"),
        "Desvío temporal": ("route", "darkblue"),
        "Tráfico denso": ("traffic-light", "darkred"),
        "Obstrucción de carretera": ("ban", "black"),
        "Obstrucción por vehículo": ("car-crash", "darkpurple"),
        "Evento público": ("users", "green"),
        "Obstrucción meteorológica": ("cloud-showers-heavy", "cadetblue"),
        "Gestión de velocidad": ("tachometer-alt", "lightgray"),
        "Malas condiciones meteorológicas": ("cloud", "blue"),
        "Trabajos de mantenimiento": ("tools", "gray"),
        "Gestión general de la carretera": ("cogs", "lightblue"),
        "Gestión de redireccionamiento": ("exchange-alt", "purple"),
        "Condiciones de carretera no relacionadas con la mateorologia": ("road", "lightgreen"),
        "Condiciones de carretera relacionadas con la meteorologia": ("snowflake", "lightblue")
    }
    return icon_map.get(tipo_evento, ("exclamation-triangle", "red"))  # Valor por defecto

# Coordenadas para hacer la seleccion del zoom por provincias
coordenadas_provincias = {
    "A Coruña": [43.3623, -8.4115],
    "Albacete": [38.9943, -1.8585],
    "Alicante": [38.3452, -0.4810],
    "Almería": [36.8381, -2.4597],
    "Ávila": [40.6565, -4.6818],
    "Badajoz": [38.8786, -6.9703],
    "Barcelona": [41.3888, 2.1590],
    "Bilbao": [43.2630, -2.9350],
    "Cádiz": [36.5160, -6.2994],
    "Castellón": [39.9864, -0.0513],
    "Ciudad Real": [38.9861, -3.9271],
    "Córdoba": [37.8882, -4.7794],
    "Cuenca": [40.0704, -2.1374],
    "Girona": [41.9794, 2.8214],
    "Granada": [37.1773, -3.5986],
    "Guadalajara": [40.6330, -3.1669],
    "Huelva": [37.2614, -6.9447],
    "Huesca": [42.1401, -0.4089],
    "Jaén": [37.7796, -3.7849],
    "La Rioja": [42.4650, -2.4480],
    "Las Palmas": [28.1272, -15.4314],
    "León": [42.5987, -5.5671],
    "Lleida": [41.6176, 0.6200],
    "Lugo": [43.0097, -7.5560],
    "Madrid": [40.4168, -3.7038],
    "Málaga": [36.7213, -4.4214],
    "Murcia": [37.9834, -1.1299],
    "Ourense": [42.3360, -7.8642],
    "Oviedo": [43.3619, -5.8494],
    "Palencia": [42.0095, -4.5270],
    "Pontevedra": [42.4333, -8.6333],
    "Salamanca": [40.9701, -5.6635],
    "San Sebastián": [43.3183, -1.9812],
    "Santa Cruz de Tenerife": [28.4636, -16.2518],
    "Santander": [43.4623, -3.8099],
    "Segovia": [40.9481, -4.1184],
    "Sevilla": [37.3886, -5.9823],
    "Soria": [41.7666, -2.4689],
    "Tarragona": [41.1189, 1.2445],
    "Teruel": [40.3456, -1.1065],
    "Toledo": [39.8628, -4.0273],
    "Valencia": [39.4699, -0.3763],
    "Valladolid": [41.6520, -4.7286],
    "Vitoria": [42.8467, -2.6727],
    "Zamora": [41.5033, -5.7446],
    "Zaragoza": [41.6488, -0.8891],
    "Ceuta": [35.8894, -5.3213],
    "Melilla": [35.2923, -2.9381],
    "Todas": [40.4168, -3.7038]
}
