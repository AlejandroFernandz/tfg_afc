<<<<<<< HEAD
# tfg-mapa
Fecha de creación 23/12
=======
# Mapa de Tráfico en Tiempo Real (DGT)

Proyecto que muestra un **mapa interactivo de tráfico en tiempo real en España**, utilizando datos oficiales de la **Dirección General de Tráfico (DGT)**.  
El sistema descarga, procesa y visualiza eventos de tráfico y radares mediante **Flask + Folium + Leaflet**.

---

## Funcionalidades principales

- Descarga automática de datos DGT (eventos y radares)
- Parseo de XML DATEX II
- Visualización en mapa interactivo
- Marcadores agrupados (MarkerCluster)
- Diferenciación entre:
  - Eventos actuales
  - Eventos futuros
  - Radares fijos y de tramo
- Pestañas de navegación
- Selector de provincia con zoom automático
- Actualización automática cada 5 minutos

---

## Tecnologías utilizadas

- **Python 3**
- **Flask** – servidor web
- **Folium / Leaflet** – mapas interactivos
- **Pandas** – manejo de datos
- **XML (DATEX II)** – datos de la DGT
- **JavaScript** – interacción con el mapa
- **Git / GitHub** – control de versiones

---

## Estructura del proyecto

```text
TFG_Final/
├── server.py                 # Servidor Flask
├── app/
│   ├── mapas.py              # Generación de mapas
│   ├── parsing.py            # Parseo de XML DGT
│   ├── descarga.py           # Descarga de datos
│   └── utilidades.py         # Funciones auxiliares
├── data/                     # XML descargados (ignorado por git)
├── mapas_generados/          # HTML generados (ignorado por git)
├── .gitignore
├── requirements.txt
└── README.md
>>>>>>> 2230f2f (Primera version del README)
