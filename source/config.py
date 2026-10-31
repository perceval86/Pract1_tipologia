# Configuracion general del scraper de Steam.
# Todo lo que se puede querer cambiar esta aqui para no tocar el resto del codigo.

URL_BASE = "https://store.steampowered.com"

# Busqueda de juegos (category1=998 -> solo juegos) ordenada por mas vendidos,
# en espanol y con precios de Espana.
URL_BUSQUEDA = URL_BASE + "/search/?l=spanish&cc=es&category1=998&filter=topsellers"

URL_ROBOTS = URL_BASE + "/robots.txt"

# Servicio externo que devuelve el User-Agent con el que llega la peticion.
# Solo se usa para comprobar que el User-Agent es el que queremos.
URL_COMPROBAR_UA = "https://httpbin.org/user-agent"

# User-Agent de un navegador normal. Si no se pone, requests se identifica
# como "python-requests/x.y" y Selenium en modo headless como "HeadlessChrome".
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
)

CABECERAS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "es-ES,es;q=0.9",
}

# Cookies para saltar la pagina de verificacion de edad de algunos juegos.
# Equivale a decir que se ha nacido el 1 de enero de 1990.
COOKIES_EDAD = {
    "birthtime": "631152001",
    "lastagecheckage": "1-0-1990",
    "wants_mature_content": "1",
}

# Uso responsable: pausa aleatoria entre peticiones (en segundos).
PAUSA_MIN = 1.5
PAUSA_MAX = 3.5

# Reintentos si el servidor responde con error (429 = demasiadas peticiones).
MAX_REINTENTOS = 3
TIMEOUT = 20

# Valores por defecto de los argumentos del programa.
MAX_JUEGOS = 200
FICHERO_SALIDA = "../dataset/steam_juegos.csv"
