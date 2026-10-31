# Primera fase: recorrer la busqueda de Steam con Selenium.
#
# La lista de juegos de Steam usa "scroll infinito": solo carga 50 juegos y,
# cuando el usuario baja hasta el final, pide mas por JavaScript. Con requests
# solo veriamos los 50 primeros, por eso aqui se usa un navegador real
# (Chrome controlado por Selenium) que hace scroll hasta tener los juegos que
# queremos. De cada fila se guardan los datos basicos y el enlace a su ficha.

import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from utilidades import precio_a_float, solo_numero


def abrir_navegador(visible=False):
    """Abre Chrome con nuestro User-Agent. Por defecto sin ventana (headless)."""
    opciones = Options()
    if not visible:
        opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1400,1000")
    opciones.add_argument("--lang=es-ES")
    # Sin esta linea Chrome headless se identifica como "HeadlessChrome".
    opciones.add_argument(f"--user-agent={config.USER_AGENT}")
    # Selenium Manager descarga solo el chromedriver adecuado.
    return webdriver.Chrome(options=opciones)


def user_agent_navegador(navegador):
    """Devuelve el User-Agent que esta usando realmente el navegador."""
    return navegador.execute_script("return navigator.userAgent;")


def rechazar_cookies(navegador):
    """Si aparece el aviso de cookies, rechaza las opcionales."""
    try:
        boton = WebDriverWait(navegador, 5).until(
            EC.element_to_be_clickable((By.ID, "rejectAllButton"))
        )
        boton.click()
        print("Aviso de cookies cerrado (rechazadas las opcionales)")
    except TimeoutException:
        pass  # No ha salido el aviso


def hacer_scroll(navegador, max_juegos):
    """Baja hasta el final de la pagina hasta tener max_juegos filas cargadas.

    Para si ya no se cargan mas juegos despues de varios intentos.
    """
    intentos_sin_cambios = 0
    filas_antes = 0

    while True:
        filas = len(navegador.find_elements(By.CSS_SELECTOR, "#search_resultsRows > a"))
        print(f"  Juegos cargados en la lista: {filas}")
        if filas >= max_juegos:
            break

        if filas == filas_antes:
            intentos_sin_cambios += 1
            if intentos_sin_cambios >= 4:
                print("  No se cargan mas juegos, se para el scroll")
                break
        else:
            intentos_sin_cambios = 0
        filas_antes = filas

        navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Pausa para que cargue el siguiente bloque y para no saturar el servidor
        time.sleep(config.PAUSA_MAX)


def leer_fila(fila):
    """Extrae los datos de una fila de la busqueda (un elemento <a> de BeautifulSoup)."""
    juego = {}
    juego["appid"] = fila.get("data-ds-appid")
    # Quitamos los parametros de seguimiento (?snr=...) del enlace
    juego["url"] = fila.get("href", "").split("?")[0]
    # Algunas filas son paquetes (/sub/) con varios juegos; su ficha es distinta
    juego["tipo"] = "paquete" if "/sub/" in juego["url"] else "juego"

    titulo = fila.select_one(".title")
    juego["titulo"] = titulo.get_text(strip=True) if titulo else None

    fecha = fila.select_one(".search_released")
    juego["fecha_lanzamiento"] = fecha.get_text(strip=True) if fecha else None

    # Plataformas: cada una es un <span class="platform_img win|mac|linux">
    juego["windows"] = fila.select_one(".platform_img.win") is not None
    juego["mac"] = fila.select_one(".platform_img.mac") is not None
    juego["linux"] = fila.select_one(".platform_img.linux") is not None

    # Las resenas vienen en un tooltip: "Muy positivas<br>El 92 % de las 1,234 resenas..."
    juego["valoracion"] = None
    juego["porcentaje_positivas"] = None
    juego["num_resenas"] = None
    resenas = fila.select_one(".search_review_summary")
    if resenas:
        tooltip = resenas.get("data-tooltip-html", "")
        partes = tooltip.split("<br>")
        juego["valoracion"] = partes[0]
        encontrado = re.search(r"(\d+)\s*%.*?([\d.,]+)\s*rese", tooltip)
        if encontrado:
            juego["porcentaje_positivas"] = int(encontrado.group(1))
            juego["num_resenas"] = solo_numero(encontrado.group(2))

    # Precios. data-price-final viene en centimos.
    juego["precio_final"] = None
    bloque_precio = fila.select_one(".search_price_discount_combined")
    if bloque_precio and bloque_precio.get("data-price-final"):
        juego["precio_final"] = int(bloque_precio["data-price-final"]) / 100

    original = fila.select_one(".discount_original_price")
    juego["precio_original"] = precio_a_float(original.get_text()) if original else juego["precio_final"]

    descuento = fila.select_one(".discount_pct")
    juego["descuento_pct"] = solo_numero(descuento.get_text()) if descuento else 0

    juego["gratuito"] = fila.select_one(".discount_final_price.free") is not None
    return juego


def buscar_juegos(max_juegos, visible=False):
    """Abre la busqueda, hace scroll y devuelve (lista de juegos, User-Agent usado)."""
    navegador = abrir_navegador(visible)
    try:
        ua = user_agent_navegador(navegador)
        print(f"User-Agent de Selenium: {ua}")

        navegador.get(config.URL_BUSQUEDA)
        WebDriverWait(navegador, 15).until(
            EC.presence_of_element_located((By.ID, "search_resultsRows"))
        )
        rechazar_cookies(navegador)
        hacer_scroll(navegador, max_juegos)

        # Cuando ya esta todo cargado, se analiza el HTML con BeautifulSoup
        html = BeautifulSoup(navegador.page_source, "lxml")
    except WebDriverException as error:
        print(f"Error con el navegador: {error}")
        return [], None
    finally:
        navegador.quit()

    juegos = []
    vistos = set()
    for fila in html.select("#search_resultsRows > a"):
        juego = leer_fila(fila)
        # Los packs o bundles no tienen appid; tambien evitamos repetidos
        if not juego["appid"] or juego["appid"] in vistos:
            continue
        vistos.add(juego["appid"])
        juegos.append(juego)
        if len(juegos) >= max_juegos:
            break

    return juegos, ua
