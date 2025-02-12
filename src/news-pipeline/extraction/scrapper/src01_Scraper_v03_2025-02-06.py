import asyncio
import json
import locale
import requests
from urllib.parse import urljoin
from typing import List, Optional
from datetime import date, datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import time
from pydantic import BaseModel, Field, HttpUrl, field_validator
import csv

# MODELOS
class ArticuloBase(BaseModel):
    Title: str = Field(default="TituloDefault")
    Date: str = Field(default_factory=lambda: date.today().isoformat())
    Link: HttpUrl

    @field_validator("Date", mode='before')
    def validate_fecha(cls, value):
        if isinstance(value, date):
            return value.isoformat()
        return value

class Referencia(BaseModel):
    texto: str
    link: str

class Articulo(ArticuloBase):
    parrafos: Optional[List[str]] = Field(default_factory=list)
    referencias: Optional[List[Referencia]] = Field(default_factory=list)

# DICCIONARIO FUENTES
fuentes = {
    'theverge': {
        'base_url': 'https://www.theverge.com',
        'url': 'https://www.theverge.com/archives/{anio}/{mes}/{page}',
        'selector_articulo': 'duet--content-cards--content-card _1ufh7nr1 _1ufh7nr0 _1lkmsmo0',
        'formato_fecha': '%b %d',
        'selector_boton': None,
    },
    'techcrunch': {
        'base_url': 'https://techcrunch.com',
        'url': 'https://techcrunch.com/{anio}/{mes}/page/{page}',
        'selector_articulo': 'loop-card loop-card--post-type-post loop-card--default loop-card--horizontal loop-card--wide loop-card--force-storyline-aspect-ratio',
        'formato_fecha': '%b %d, %Y',
        'selector_boton': None,
    },
    'wired': {
        'base_url': 'https://es.wired.com',
        'url': 'https://es.wired.com/tag/inteligencia-artificial?page={page}',
        'selector_articulo': 'summary-item__content',
        'formato_fecha': '%d de %B de %Y',
        'selector_boton': None,
    },
    'arstechnica': {
        'base_url': 'https://arstechnica.com',
        'url': 'https://arstechnica.com/{anio}/page/{page}',
        'selector_articulo': 'flex flex-1 flex-col justify-between pl-3 sm:pl-5',
        'formato_fecha': '%d/%m/%Y',
        'selector_boton': 'post-navigation-link',
    },
    'xataka': {
        'base_url': 'https://www.xataka.com',
        'url': 'https://www.xataka.com/archivos/{anio}/{mes}',
        'selector_articulo': None,
        'formato_fecha': '%d de %B de %Y',
        'selector_boton': None,
    },
    'theregister': {
        'base_url': 'https://www.theregister.com',
        'url': 'https://www.theregister.com/Archive/{anio}/{mes}/{dia}/',
        'selector_articulo': 'article_text_elements',
        'formato_fecha': '%d %b, %Y',
        'selector_boton': None,
    },
}

# FUNCIONES Y AUXILIAR
class SafeDict(dict):
    """Clase auxiliar para formatear strings con diccionarios seguros que devuelven string vacía en caso de no existir la key."""
    def __missing__(self, key):
        return f"{{{key}}}"

def formato_url_seguro(template: str, **kwargs) -> str:
    return template.format_map(SafeDict(**kwargs))

def arregla_links(url_base: str, url_relativa: str) -> str:
    if not url_relativa.startswith(('http', 'www')):
        return urljoin(url_base, url_relativa)
    return url_relativa

def format_fecha(fecha_texto: str, formato: str) -> datetime.date:
    # ELIMINAR UPDATED O ESPACIOS INICIALES
    fecha_texto = re.sub(r'^updated\s*', '', fecha_texto, flags=re.IGNORECASE).strip()
    
    # 1. FORMATOS ESPECIFICADOS
    try:
        parsed_date = datetime.strptime(fecha_texto, formato).date()

        if parsed_date.year == 1900:
                parsed_date = parsed_date.replace(year=datetime.now().year)

        return parsed_date
    except ValueError:
        pass
    
    # 2. INTENTAR FORMATOS COMUNES
    formatos_alternativos = [
        "%d/%m/%Y",    # 22/1/2025
        "%m/%d/%Y",    # 1/22/2025
        "%d-%m-%Y",    # 22-1-2025
        "%m-%d-%Y",    # 1-22-2025
        "%Y-%m-%d",    # 2025-1-22
        "%Y/%m/%d",    # 2025/1/22
        "%d %b %Y",    # 22 Jan 2025
        "%d de %B de %Y",  # 22 de enero de 2025
        "%B %d, %Y",   # January 22, 2025
    ]
    
    for fmt in formatos_alternativos:
        try:
            return datetime.strptime(fecha_texto, fmt).date()
        except ValueError:
            continue

    # 3. INTENTAR FORMATOS RELATIVOS
    if any(keyword in fecha_texto.lower() for keyword in ['ago', 'hace']):
        try:
            matches = None
            # INGLES / ESPAÑOL
            if 'ago' in fecha_texto.lower():
                matches = re.search(r'(\d+)\s+(minute|hour|day)s?\s+ago', fecha_texto, re.IGNORECASE)
            else:
                matches = re.search(r'hace\s+(\d+)\s+(minuto|hora|d[ií]a)s?', fecha_texto, re.IGNORECASE)
            
            if matches:
                cantidad = int(matches.group(1))
                unidad = matches.group(2).lower().replace('í', 'i').replace('á', 'a')
                
                delta_mapping = {
                    'minute': timedelta(minutes=1),
                    'minuto': timedelta(minutes=1),
                    'hour': timedelta(hours=1),
                    'hora': timedelta(hours=1),
                    'day': timedelta(days=1),
                    'dia': timedelta(days=1)
                }
                
                if unidad in delta_mapping:
                    delta = delta_mapping[unidad] * cantidad
                    return (datetime.now() - delta).date()
        
        except Exception as e:
            print(f"Error procesando fecha relativa: {e}")

    # 4. INTENTAR FORMATO ESPECIFICO EN INGLES/ESPAÑOL
    for loc in ["en_US.utf8", "es_ES.utf8"]:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            parsed_date = datetime.strptime(fecha_texto, formato).date()

            if parsed_date.year == 1900:
                parsed_date = parsed_date.replace(year=datetime.now().year)

            return parsed_date
        except (ValueError, locale.Error):
            continue

    # 5. FALLBACK A FECHA DE HOY
    print(f"\t\t(x) Fecha no reconocida: {fecha_texto}. Usando fecha de hoy")
    return datetime.today().date()

def obtener_urls(fuente, fecha_inicio, fecha_fin):
    urls = set()
    current_date = fecha_inicio
    while current_date > fecha_fin:
        url = formato_url_seguro(fuente['url'], anio=current_date.year, mes=f"{current_date.month:02d}", dia=f"{current_date.day:02d}")
        urls.add(url)
        current_date -= timedelta(days=1)
    return urls

def procesar_articulos(articulos_soup, fuente, fecha_base, fecha_cutoff) -> tuple[list[ArticuloBase], bool]:
    articulos_validos = []
    older_than_cutoff = False
    
    for articulo in articulos_soup:
        titular_elem = articulo.find('h2') or articulo.find('h3') or articulo.find('h4') or articulo.find('a')
        fecha_elem = articulo.find('time')
        enlace_elem = (titular_elem.find('a') if titular_elem else None) or articulo.find('a') or articulo.parent

        # SI NO HAY LINK - SALTAR ARTICULO
        if not enlace_elem or not enlace_elem.get('href'):
            print("\t\t(x) No se encontró enlace")
            continue
        else:
            enlace = arregla_links(fuente['base_url'], enlace_elem.get('href'))

        # SI NO HAY FECHA - PASAR NOFECHA
        if not fecha_elem:
            if '{dia}' in fuente['url']:
                match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', enlace)
                if match:
                    anio_extracted, mes_extracted, dia_extracted = match.groups()
                    fecha_text = f"{dia_extracted}/{mes_extracted}/{anio_extracted}"
                    print(f"\t\t(-) Extraída fecha desde URL: {fecha_text}")
                else:
                    print("\t\t\t(x) No se ha podido extraer fecha desde URL")
                    fecha_text = "NoFecha"
            else:
                    print("\t\t(x) No se encontró fecha")
                    fecha_text = "NoFecha"
        else:
            fecha_text = fecha_elem.get_text(strip=True) or fecha_elem.today().isoformat()

        # SI NO HAY TITULAR - PASAR NOTITULAR
        if not titular_elem:
            print("\t\t(x) No se encontró titular")
            titular = "NoTitular"
        else:
            titular = titular_elem.get_text(strip=True)

        try:
            fecha_articulo = format_fecha(fecha_text, fuente['formato_fecha'])
        except Exception as e:
            print(f"Error al formatear fecha {fecha_text}: {e}")
            continue

        if fecha_articulo > fecha_base:
            print("\t\t(x) Artículo futuro")
            continue
            
        if fecha_articulo < fecha_cutoff:
            older_than_cutoff = True
            break

        articulos_validos.append(ArticuloBase(
            Title=titular,
            Date=fecha_articulo,
            Link=enlace
        ))
    
    return articulos_validos, older_than_cutoff

def obtener_links_xataka(anio: int, mes: int, dia: int, max_dias: int) -> List[ArticuloBase]:
    prefijo = "https://www.xataka.com"
    articulos_validos = []

    fecha_base = date(anio, mes, dia)
    fecha_cutoff = fecha_base - timedelta(days=max_dias)

    current_year = anio
    current_month = mes

    while True:
        current_month_first_day = date(current_year, current_month, 1)
        cutoff_month_first_day = fecha_cutoff.replace(day=1)
        if current_month_first_day < cutoff_month_first_day:
            break

        url_params = {
            "anio": current_year,
            "mes": current_month,
            "dia": dia,
            "page": 1
        }

        print(f"Procesando año {current_year}, mes {current_month:02d} para fuente xataka")
        formatted_url = formato_url_seguro(fuentes['xataka']['url'], **url_params)
        print(f"\tProcesando: {formatted_url}")

        try:
            response = requests.get(formatted_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for h2 in soup.find_all('h2'):
                date_text = h2.get_text(strip=True)
                try:
                    fecha_articulo = format_fecha(date_text, fuentes['xataka']['formato_fecha'])
                except Exception as e:
                    print(f"Error al formatear fecha {date_text}: {e}")
                    continue

                if fecha_articulo > fecha_base:
                    continue
                if fecha_articulo < fecha_cutoff:
                    break

                ul = h2.find_next('ul')
                if not ul:
                    continue

                for li in ul.find_all('li'):
                    a = li.find('a')
                    if not a:
                        continue
                    title = a.get_text(strip=True)
                    link = arregla_links(prefijo, a['href'])

                    articulos_validos.append(ArticuloBase(
                        Title=title,
                        Date=fecha_articulo,
                        Link=link
                    ))

        except requests.HTTPError as e:
            print(f"Failed to retrieve {formatted_url}: {e}")
        except Exception as e:
            print(f"An error occurred processing {formatted_url}: {e}")

        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1

    return articulos_validos

def guardar_articulos(articles: List[ArticuloBase], filename="articles.json"):
    articles_dict = [article.model_dump_json() for article in articles]
    
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(articles_dict, json_file, ensure_ascii=False, indent=4)
    print(f"Guardados {len(articles)} articulos en {filename}")

    campos = list(articles[0].model_dump().keys())
    
    csv_filename = filename.replace(".json", ".csv")

    with open(csv_filename, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=campos)
        writer.writeheader()
        
        for article in articles:
            writer.writerow(article.model_dump())

def scroll_abajo(driver, pausa=1):
    ultima_altura = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pausa)

        nueva_altura = driver.execute_script("return document.body.scrollHeight")
        if nueva_altura == ultima_altura:
            break
        ultima_altura = nueva_altura

def recopilar_articulos(fuente, driver, url, fecha_base, fecha_cutoff):
    print(f"\tProcesando: {url} ")

    try:
        driver.get(url)
        scroll_abajo(driver)
    except WebDriverException as e:
        print(f"\t\t(x) Error cargando {url}: {e}. No se recopilaron artículos.")
        return None

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articulos = soup.find_all('div', class_=fuentes[fuente]['selector_articulo'])

    articulos_procesados, older_than_cutoff = procesar_articulos(articulos, fuentes[fuente], fecha_base, fecha_cutoff)

    return articulos_procesados, older_than_cutoff

def scrappear_articulos(fuente: str, fecha_base: date, fecha_cutoff: date) -> List[ArticuloBase]:
    # NAVEGADOR
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    lista_articulos = []

    urls = obtener_urls(fuentes[fuente], fecha_base, fecha_cutoff)
    print(f"Cargando fuente {fuente}")
    for url in urls:
        # SI HAY PAGE EN URL -> PAGINACION
        if '{page}' in fuentes[fuente]['url']:
            page_number = 1
            while True:
                url_params = {
                    "page": page_number
                }

                # SE VUELVE A FORMATEAR URL PARA SUSTITUIR LAS PÁGINAS
                formatted_url = formato_url_seguro(url, **url_params)

                articulos_procesados, older_than_cutoff = recopilar_articulos(fuente, driver, formatted_url, fecha_base, fecha_cutoff)
                lista_articulos.extend(articulos_procesados)

                if not articulos_procesados or older_than_cutoff:
                    break

                page_number += 1

        # SI HAY BOTON EN FUENTE -> CARGAR MÁS
        elif fuentes[fuente]['selector_boton']:
            while True:
                articulos_procesados, older_than_cutoff = recopilar_articulos(fuente, driver, url, fecha_base, fecha_cutoff)
                lista_articulos.extend(articulos_procesados)

                if not articulos_procesados or older_than_cutoff:
                    break
                else:
                    try:
                        load_more_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, fuentes[fuente]['selector_boton']))
                        )
                        driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
                        load_more_btn.click()
                        print("\t\tCargando más artículos con botón...")
                        time.sleep(2)
                    except (TimeoutException, ElementClickInterceptedException):
                        print("\t\t(x) No se pudo cargar más artículos.")
                        break

        # SI NO ES NINGUNO DE LOS CASOS -> SIMPLEMENTE RECOPILAR            
        else:
            articulos_procesados, _ = recopilar_articulos(fuente, driver, url, fecha_base, fecha_cutoff)
            lista_articulos.extend(articulos_procesados)

    driver.quit()
    return lista_articulos

def obtener_max_dias():
    try:
        max_dias = int(input("Ingrese el número de días (valor por defecto: 7): "))
        if max_dias <= 0:
            raise ValueError
    except ValueError:
        print("Entrada no válida. Se usará 7 días por defecto.")
        max_dias = 7
    return max_dias

def main():
    fecha_base = datetime.today().date()
    MAX_DIAS = obtener_max_dias()
    fecha_cutoff = fecha_base - timedelta(days=MAX_DIAS)
    articulos = scrappear_articulos('theregister', fecha_base, fecha_cutoff)
    articulos += scrappear_articulos('theverge', fecha_base, fecha_cutoff)
    articulos += scrappear_articulos('techcrunch', fecha_base, fecha_cutoff)
    articulos += scrappear_articulos('wired', fecha_base, fecha_cutoff)
    articulos += scrappear_articulos('arstechnica', fecha_base, fecha_cutoff)
    articulos += obtener_links_xataka(fecha_base.year, fecha_base.month, fecha_base.day, MAX_DIAS)
    guardar_articulos(articulos, filename=f"{fecha_base.strftime("%Y-%m-%d")}_01_links.json")

if __name__ == "__main__":
    main()