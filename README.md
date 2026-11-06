# Práctica 1 - Web scraping: juegos más vendidos de Steam

Asignatura: M2.851 Tipología y ciclo de vida de los datos (UOC).

## Integrantes del grupo

- Integrante 1: Carlos Bello Erla 
- Integrante 2: Eric Chaume García

## Descripción

Scraper en Python que crea un dataset con los juegos más vendidos de la tienda de Steam
(https://store.steampowered.com) en España: precio, descuento, valoraciones, géneros,
desarrollador, etiquetas, requisitos mínimos, etc.

Funciona en dos fases:

1. **Búsqueda (Selenium).** La lista de "más vendidos" carga los juegos con scroll infinito
   mediante JavaScript, así que se abre Chrome en segundo plano, se rechazan las cookies
   opcionales y se hace scroll hasta tener los juegos pedidos. De cada fila se sacan los datos
   básicos y el enlace a su ficha (descubrimiento de enlaces).
2. **Fichas (requests + BeautifulSoup).** Se visita la ficha de cada juego y se extraen los
   datos detallados. Se usan cookies para saltar la verificación de edad.

Medidas de uso responsable:

- Se lee el `robots.txt` y se comprueba cada URL antes de visitarla.
- Pausa aleatoria de 1,5 a 3,5 segundos entre peticiones.
- Reintentos con espera creciente si el servidor responde 429 o 5xx.
- Una sola sesión HTTP reutilizada y límite de juegos configurable.
- Se comprueba el User-Agent de requests (con httpbin.org) y el de Selenium
  (`navigator.userAgent`), ya que en modo headless Chrome se identifica como `HeadlessChrome`.

## Archivos del repositorio

| Ruta | Contenido |
|------|-----------|
| `source/main.py` | Programa principal: argumentos, flujo del scraping y guardado del CSV |
| `source/buscador.py` | Fase 1: Selenium, cookies, scroll infinito y lectura de las filas de la búsqueda |
| `source/ficha.py` | Fase 2: extracción de datos de la ficha de cada juego |
| `source/utilidades.py` | Sesión HTTP, pausas, reintentos, robots.txt, User-Agent y conversión de números |
| `source/config.py` | URLs, cabeceras, cookies, pausas y valores por defecto |
| `dataset/steam_juegos.csv` | Dataset resultante |
| `requirements.txt` | Librerías y versiones utilizadas |

## Instalación

Hace falta Python 3.10 o superior y Google Chrome instalado (Selenium descarga solo el
chromedriver correcto).

```bash
python -m venv venv
venv\Scripts\activate        # En Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

## Uso

El script se ejecuta desde la carpeta `source`:

```bash
cd source
python main.py
```

Parámetros:

| Parámetro | Por defecto | Descripción |
|-----------|-------------|-------------|
| `--max-juegos N` | 200 | Número de juegos a extraer |
| `--salida RUTA` | `../dataset/steam_juegos.csv` | Fichero CSV de salida |
| `--ver-navegador` | desactivado | Muestra la ventana de Chrome mientras hace scroll |

Ejemplos:

```bash
# Los 50 más vendidos en un fichero aparte
python main.py --max-juegos 50 --salida ../dataset/top50.csv

# Ver cómo Selenium hace el scroll
python main.py --max-juegos 120 --ver-navegador
```

Con 200 juegos tarda unos 10 minutos por las pausas entre peticiones.

## Dataset

- Zenodo DOI: https://doi.org/10.5281/zenodo.23833644
- Licencia: CC BY-NC-SA 4.0
