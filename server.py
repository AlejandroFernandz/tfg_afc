from flask import Flask, send_from_directory
import threading
import time
import os
from app.mapas import update_map

app = Flask(__name__)

MAPA_DIR = "mapas_generados"
MAPA_HTML = "mapa_completo.html"
# FLAG_PRIMERA_ACTUALIZACION = os.path.join(MAPA_DIR, "primera_actualizacion.ok")

# Funcion nueva 18/07
# def esperar_archivos_mapa():
#     """Espera hasta que todos los archivos de mapa estén generados."""
#     intentos = 0
#     while not (
#         os.path.exists(os.path.join(MAPA_DIR, "mapa_actuales.html")) and
#         os.path.exists(os.path.join(MAPA_DIR, "mapa_futuros.html")) and
#         os.path.exists(os.path.join(MAPA_DIR, MAPA_HTML))
#     ):
#         time.sleep(1)
#         intentos += 1
#         if intentos > 60:
#             raise TimeoutError("❌ Timeout: No se generaron todos los mapas a tiempo.")
#     print("[✅] Todos los archivos de mapa están disponibles.")


def actualizar_mapa_periodicamente():
    """Actualiza el mapa cada 5 minutos."""
    while True:
        try:
            print("[🛰️] Actualizando mapa...")
            update_map()
            print("[✅] Mapa actualizado correctamente.")
        except Exception as e:
            print(f"[❌] Error al actualizar el mapa: {e}")
        time.sleep(300)  # 5 minutos

@app.route("/")
def home():
    """HTML que muestra un iframe con el mapa completo."""
    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Mapa de Tráfico en Tiempo Real</title>
        <meta http-equiv="refresh" content="300"> <!-- recarga cada 5 min -->
    </head>
    <body style="margin:0">
        <iframe src="/mapa" width="100%" height="100%" style="border:none;"></iframe>
    </body>
    </html>
    """

@app.route("/mapa")
def mostrar_mapa():
    """Sirve el HTML del mapa completo con pestañas."""
    return send_from_directory(MAPA_DIR, MAPA_HTML)

@app.route("/mapa_actuales.html")
def mapa_actuales():
    return send_from_directory(MAPA_DIR, "mapa_actuales.html")

@app.route("/mapa_futuros.html")
def mapa_futuros():
    return send_from_directory(MAPA_DIR, "mapa_futuros.html")

# @app.route("/primera_actualizacion")
# def primera_actualizacion():
#     """Devuelve 1 si ya se ha generado el primer mapa, 0 si no."""
#     return "1" if os.path.exists(FLAG_PRIMERA_ACTUALIZACION) else "0"

if __name__ == "__main__":
    print("[🚀] Generando mapa inicial completo...")

    try:
        update_map()
        # esperar_archivos_mapa()
        print("[✅] Mapa actualizado correctamente.")

    except Exception as e:
        print(f"[❌] Error en la actualización inicial: {e}")
        exit(1)

    print("[⏳] Verificando existencia de mapa completo...")
    intentos = 0
    while not os.path.exists(os.path.join(MAPA_DIR, MAPA_HTML)):
        time.sleep(1)
        intentos += 1
        if intentos > 60:
            raise TimeoutError("❌ Timeout: No se generó el mapa completo a tiempo.")

    print("[✅] Mapa completo generado. Iniciando servidor Flask...")

    threading.Thread(target=actualizar_mapa_periodicamente, daemon=True).start()

    print("[🌐] Servidor corriendo en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
