# Programa principal: genera un dataset con los juegos mas vendidos de Steam.
#
# Pasos:
#   1. Comprueba el robots.txt y el User-Agent.
#   2. Recorre la busqueda de Steam con Selenium (scroll infinito) y descubre
#      los enlaces a las fichas de los juegos.
#   3. Visita cada ficha con requests, con pausas entre peticiones.
#   4. Guarda todo en un CSV.
#
# Uso:  python main.py --max-juegos 100

import argparse
import csv
import os
import sys
from datetime import datetime

import config
import utilidades
from buscador import buscar_juegos
from ficha import leer_ficha

# Orden de las columnas en el CSV
COLUMNAS = [
    "appid", "titulo", "tipo", "url", "fecha_lanzamiento",
    "precio_final", "precio_original", "descuento_pct", "gratuito",
    "valoracion", "porcentaje_positivas", "num_resenas", "metacritic",
    "generos", "desarrollador", "editor", "franquicia",
    "etiquetas", "caracteristicas", "num_idiomas",
    "windows", "mac", "linux", "acceso_anticipado", "contenido_adulto", "usa_ia",
    "ram_min_gb", "disco_min_gb", "descripcion_corta",
    "posicion_ventas", "fecha_extraccion",
]


def leer_argumentos():
    parser = argparse.ArgumentParser(description="Scraper de los juegos mas vendidos de Steam")
    parser.add_argument("--max-juegos", type=int, default=config.MAX_JUEGOS,
                        help=f"numero de juegos a extraer (por defecto {config.MAX_JUEGOS})")
    parser.add_argument("--salida", default=config.FICHERO_SALIDA,
                        help="ruta del fichero CSV de salida")
    parser.add_argument("--ver-navegador", action="store_true",
                        help="muestra la ventana de Chrome en vez de usarlo en segundo plano")
    return parser.parse_args()


def guardar_csv(juegos, ruta):
    """Escribe la lista de juegos en un CSV (separador coma, codificacion UTF-8)."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=COLUMNAS, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(juegos)


def main():
    # La consola de Windows no siempre usa UTF-8 y fallaria con algunos titulos
    sys.stdout.reconfigure(encoding="utf-8")
    args = leer_argumentos()
    inicio = datetime.now()

    # --- 1. Comprobaciones previas ---
    sesion = utilidades.crear_sesion()
    print(f"User-Agent de requests: {utilidades.comprobar_user_agent_requests(sesion)}")

    robots = utilidades.cargar_robots()
    if not utilidades.permitido(robots, config.URL_BUSQUEDA):
        print("El robots.txt no permite acceder a la busqueda. Se para el programa.")
        return

    # --- 2. Busqueda con Selenium ---
    print(f"\nBuscando los {args.max_juegos} juegos mas vendidos...")
    juegos, _ = buscar_juegos(args.max_juegos, args.ver_navegador)
    print(f"Se han encontrado {len(juegos)} juegos")

    # --- 3. Visitar la ficha de cada juego ---
    fecha_extraccion = inicio.strftime("%Y-%m-%d")
    for posicion, juego in enumerate(juegos, start=1):
        juego["posicion_ventas"] = posicion
        juego["fecha_extraccion"] = fecha_extraccion

        url = juego["url"] + "?l=spanish&cc=es"
        if not utilidades.permitido(robots, url):
            print(f"[{posicion}/{len(juegos)}] {juego['titulo']}: no permitido por robots.txt")
            continue

        print(f"[{posicion}/{len(juegos)}] {juego['titulo']}")
        html = utilidades.descargar(sesion, url)
        if html:
            detalles = leer_ficha(html)
            if "error" in detalles:
                print(f"  No se ha podido leer la ficha: {detalles['error']}")
            juego.update(detalles)

        utilidades.pausa()

        # Guardamos cada 25 juegos para no perder lo descargado si algo falla
        if posicion % 25 == 0:
            guardar_csv(juegos[:posicion], args.salida)

    # --- 4. Guardar ---
    guardar_csv(juegos, args.salida)
    duracion = datetime.now() - inicio
    print(f"\nDataset guardado en {args.salida} ({len(juegos)} filas, {duracion})")


if __name__ == "__main__":
    main()
