# Segunda fase: entrar en la ficha de cada juego y sacar los datos detallados.
# Estas paginas no necesitan JavaScript, asi que se usa requests + BeautifulSoup,
# que es mucho mas ligero que abrir un navegador por cada juego.

import re

from bs4 import BeautifulSoup

from utilidades import solo_numero


def texto(html, selector):
    """Devuelve el texto de un elemento o None si no existe."""
    elemento = html.select_one(selector)
    if elemento is None:
        return None
    return elemento.get_text(" ", strip=True)


def lista_textos(html, selector, maximo=None):
    """Devuelve los textos de varios elementos unidos con '|'."""
    textos = [e.get_text(strip=True) for e in html.select(selector)]
    textos = [t for t in textos if t and t != "+"]
    if maximo:
        textos = textos[:maximo]
    return "|".join(textos) if textos else None


def dato_ficha(bloque, etiqueta):
    """Busca en el bloque de informacion un dato como 'Desarrollador:' y devuelve sus valores.

    El bloque tiene la forma: <b>Desarrollador:</b> <a>Nombre</a>, <a>Otro</a>
    """
    for negrita in bloque.find_all("b"):
        if negrita.get_text(strip=True).startswith(etiqueta):
            valores = []
            # Recorremos lo que hay despues del <b> hasta el siguiente salto de linea
            for hermano in negrita.next_siblings:
                if hermano.name == "br" or hermano.name == "b":
                    break
                if hermano.name == "a":
                    valores.append(hermano.get_text(strip=True))
                elif hermano.name == "span":
                    # Los generos vienen dentro de un <span> con varios <a>
                    enlaces = hermano.find_all("a")
                    if enlaces:
                        valores.extend(a.get_text(strip=True) for a in enlaces)
                    else:
                        valores.append(hermano.get_text(strip=True))
            return "|".join(valores) if valores else None
    return None


def requisito(lineas, palabra):
    """Busca en los requisitos minimos una linea (p. ej. 'Memoria') y devuelve los GB."""
    for linea in lineas:
        if linea.startswith(palabra):
            encontrado = re.search(r"(\d+(?:[.,]\d+)?)\s*(GB|MB)", linea, re.IGNORECASE)
            if encontrado:
                cantidad = float(encontrado.group(1).replace(",", "."))
                if encontrado.group(2).upper() == "MB":
                    cantidad = cantidad / 1024
                return round(cantidad, 2)
    return None


def leer_ficha(contenido_html):
    """Analiza el HTML de la ficha de un juego y devuelve un diccionario con sus datos."""
    html = BeautifulSoup(contenido_html, "lxml")
    datos = {}

    # Si la cookie de edad no ha funcionado aparece esta pagina en vez de la ficha
    if html.select_one("#app_agegate") or html.select_one(".agegate_birthday_selector"):
        datos["error"] = "verificacion de edad"
        return datos

    datos["descripcion_corta"] = texto(html, ".game_description_snippet")

    bloque = html.select_one("#genresAndManufacturer")
    if bloque:
        datos["generos"] = dato_ficha(bloque, "Género")
        datos["desarrollador"] = dato_ficha(bloque, "Desarrollador")
        datos["editor"] = dato_ficha(bloque, "Editor")
        datos["franquicia"] = dato_ficha(bloque, "Franquicia")
    else:
        datos["generos"] = datos["desarrollador"] = datos["editor"] = datos["franquicia"] = None

    # Etiquetas que ponen los usuarios (nos quedamos con las 10 mas votadas)
    datos["etiquetas"] = lista_textos(html, ".glance_tags.popular_tags a", maximo=10)

    # Caracteristicas: un jugador, cooperativo, logros, soporte de mando...
    datos["caracteristicas"] = lista_textos(html, ".game_area_details_specs_ctn .label")

    # Nota de Metacritic (no todos los juegos la tienen)
    datos["metacritic"] = solo_numero(texto(html, "#game_area_metascore .score"))

    # Numero de idiomas: filas de la tabla de idiomas menos la cabecera
    filas_idiomas = html.select(".game_language_options tr")
    datos["num_idiomas"] = len(filas_idiomas) - 1 if filas_idiomas else None

    datos["acceso_anticipado"] = html.select_one(".early_access_header") is not None

    # Requisitos minimos: el primer bloque es el de Windows
    lineas = []
    primer_bloque = html.select_one(".game_area_sys_req")
    if primer_bloque:
        minimos = primer_bloque.select_one(".game_area_sys_req_leftCol") or primer_bloque
        lineas = [li.get_text(" ", strip=True) for li in minimos.select("li")]
    datos["ram_min_gb"] = requisito(lineas, "Memoria")
    datos["disco_min_gb"] = requisito(lineas, "Almacenamiento")

    # En el mismo bloque Steam avisa del contenido para adultos y del uso de IA generativa
    avisos = texto(html, "#game_area_content_descriptors") or ""
    datos["contenido_adulto"] = "contenido para adultos" in avisos
    datos["usa_ia"] = "generado por IA" in avisos

    return datos
