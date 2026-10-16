"""Utilidades geográficas para el adaptador en memoria.

En PostgreSQL la distancia la calcula PostGIS (ST_Distance sobre geography);
aquí se usa la fórmula de haversine, que da el mismo resultado a escala de CU.
"""

from math import asin, cos, radians, sin, sqrt

RADIO_TIERRA_M = 6_371_008.8

# Punto por defecto cuando el usuario no comparte su ubicación (coordenadas aproximadas).
FACULTAD_DE_INGENIERIA = (19.3311, -99.1839)


def distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    dp, dl = radians(lat2 - lat1), radians(lon2 - lon1)
    h = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_M * asin(sqrt(h))
