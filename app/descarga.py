# Funciones para leer y descargar los datos de las fuentes de datos
import requests

# Función para descargar los eventos del tráfico
def download_trafico(file_path="data/trafico.xml"):
    response = requests.get("https://infocar.dgt.es/datex2/v3/dgt/SituationPublication/incidencias.xml")
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Archivo XML descargado correctamente: {file_path}")
    else:
        print("Error al descargar el archivo XML")

# Función para descargar los radares
def download_radares(file_path="data/radares.xml"):
    response = requests.get("https://infocar.dgt.es/datex2/dgt/PredefinedLocationsPublication/radares/content.xml")
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Archivo XML descargado correctamente: {file_path}")
    else:
        print("Error al descargar el archivo XML")


# download_trafico
# download_radares()