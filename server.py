from flask import Flask, send_from_directory, make_response
import threading
import time
import os
from app.mapas import update_map

app = Flask(__name__)

MAPA_DIR = "mapas_generados"
MAPA_HTML = "mapa_completo.html"

def nocache(resp):
    """Añade headers para evitar el cacheo del mapa en el navegador. 30/12"""
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

def actualizar_mapa_periodicamente():
    """Actualiza el mapa cada 5 minutos."""
    time.sleep(15)  # Espera inicial para evitar colisión al arrancar 30/12
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
    # return send_from_directory(MAPA_DIR, MAPA_HTML)
    resp = make_response(send_from_directory(MAPA_DIR, MAPA_HTML))
    return nocache(resp)

@app.route("/mapa_actuales.html")
def mapa_actuales():
    # return send_from_directory(MAPA_DIR, "mapa_actuales.html")
    resp = make_response(send_from_directory(MAPA_DIR, "mapa_actuales.html"))
    return nocache(resp)

@app.route("/mapa_futuros.html")
def mapa_futuros():
    # return send_from_directory(MAPA_DIR, "mapa_futuros.html")
    resp = make_response(send_from_directory(MAPA_DIR, "mapa_futuros.html"))
    return nocache(resp)

if __name__ == "__main__":
    print("[🚀] Generando mapa inicial completo...")

    try:
        update_map()
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
