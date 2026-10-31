# Funciones de apoyo: sesion HTTP, pausas, robots.txt y comprobacion del User-Agent.

import random
import re
import time
from urllib import robotparser

import requests

import config


def crear_sesion():
    """Crea una sesion de requests con nuestras cabeceras y las cookies de edad.

    Usar una sesion reutiliza la conexion con el servidor, asi que es mas
    rapido y genera menos carga que abrir una conexion nueva cada vez.
    """
    sesion = requests.Session()
    sesion.headers.update(config.CABECERAS)
    for nombre, valor in config.COOKIES_EDAD.items():
        sesion.cookies.set(nombre, valor, domain="store.steampowered.com")
    return sesion


def pausa():
    """Espera un tiempo aleatorio para no saturar el servidor."""
    segundos = random.uniform(config.PAUSA_MIN, config.PAUSA_MAX)
    time.sleep(segundos)


def cargar_robots():
    """Descarga y lee el robots.txt de Steam."""
    robots = robotparser.RobotFileParser()
    robots.set_url(config.URL_ROBOTS)
    robots.read()
    return robots


def permitido(robots, url):
    """Indica si el robots.txt nos deja visitar esa URL."""
    return robots.can_fetch(config.USER_AGENT, url)


def descargar(sesion, url):
    """Descarga una pagina y devuelve su HTML, o None si no se ha podido.

    Si el servidor devuelve 429 (demasiadas peticiones) o un error 5xx,
    se espera cada vez mas tiempo antes de volver a intentarlo.
    """
    for intento in range(1, config.MAX_REINTENTOS + 1):
        try:
            respuesta = sesion.get(url, timeout=config.TIMEOUT)
            if respuesta.status_code == 200:
                return respuesta.text
            if respuesta.status_code == 429 or respuesta.status_code >= 500:
                espera = 10 * intento
                print(f"  Codigo {respuesta.status_code}, reintento en {espera} s")
                time.sleep(espera)
            else:
                print(f"  Codigo {respuesta.status_code} en {url}")
                return None
        except requests.RequestException as error:
            print(f"  Error de conexion ({error}), intento {intento}")
            time.sleep(5 * intento)
    return None


def comprobar_user_agent_requests(sesion):
    """Pregunta a httpbin con que User-Agent llegan nuestras peticiones."""
    try:
        respuesta = sesion.get(config.URL_COMPROBAR_UA, timeout=config.TIMEOUT)
        return respuesta.json()["user-agent"]
    except (requests.RequestException, ValueError, KeyError):
        return "No se ha podido comprobar"


def solo_numero(texto):
    """Saca un numero entero de un texto quitando puntos y comas de miles.

    Ejemplo: "(2.839)" -> 2839. Si no hay numero devuelve None.
    """
    if not texto:
        return None
    numeros = re.sub(r"[^\d]", "", texto)
    if numeros == "":
        return None
    return int(numeros)


def precio_a_float(texto):
    """Convierte un precio como "19,99€" en 19.99. Devuelve None si no es un precio."""
    if not texto:
        return None
    encontrado = re.search(r"(\d+(?:[.,]\d+)?)", texto.replace(" ", ""))
    if not encontrado:
        return None
    return float(encontrado.group(1).replace(",", "."))
