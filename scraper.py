# ================================================================================
# scraper.py - WEB SCRAPING ROBUSTO (MEJORADO)
# ================================================================================

import time
import random
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List , Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import HEADERS

# --- CONFIGURACIÓN DE SESIÓN ROBUSTA ---
def crear_sesion():
    """Crea una sesión con estrategia de reintentos"""
    session = requests.Session()
    
    # Estrategia de reintentos: 3 intentos, esperando más tiempo entre cada uno
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,  # espera 1s, 2s, 4s...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session

# Instancia global de sesión para reutilizar conexiones
SESSION = crear_sesion()

def extraer_contenido_noticia(url: str) -> str:
    """Extrae el texto de una noticia individual con robustez"""
    try:
        # Pequeña pausa aleatoria para no saturar el servidor
        time.sleep(random.uniform(0.1, 0.5))
        
        response = SESSION.get(url, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Lista de selectores posibles (fallback)
        selectores = ['text-editor', 'nota-body', 'cuerpo-nota', 'article-body', 'content-body']
        cuerpo = None
        
        for clase in selectores:
            cuerpo = soup.find('div', class_=clase)
            if cuerpo:
                break
        
        # Intento final: buscar cualquier article
        if not cuerpo:
            cuerpo = soup.find('article')
        
        if cuerpo:
            # Extraer párrafos y limpiar
            parrafos = cuerpo.find_all('p')
            textos = []
            for p in parrafos:
                texto = p.get_text(strip=True)
                # Filtrar textos muy cortos o irrelevantes
                if len(texto) > 30 and "Lee también" not in texto:
                    textos.append(texto)
            
            return " ".join(textos)[:1500] # Limitamos a 1500 chars para no exceder contexto
            
        return ""
    except Exception as e:
        print(f"   ⚠️ Error extrayendo {url[:30]}...: {e}")
        return ""


def procesar_articulo(art) -> Optional[Dict]:
    """Procesa un artículo individual"""
    try:
        tag_titulo = art.find('h2', class_='nota__titulo-item')
        
        if tag_titulo and tag_titulo.find('a'):
            enlace = tag_titulo.find('a')['href']
            titulo = tag_titulo.get_text(strip=True)
            
            if not enlace.startswith('http'):
                enlace = "https://eldeber.com.bo" + enlace
            
            contenido = extraer_contenido_noticia(enlace)
            
            # Solo devolvemos si logramos extraer contenido real
            if contenido:
                return {
                    'titulo': titulo,
                    'url': enlace,
                    'contenido': contenido,
                    'resumen': contenido[:200] + "..."
                }
    except Exception as e:
        # Errores puntuales no detienen el proceso
        pass
    return None


def extraer_titulares_pagina(url_base: str, pagina: int) -> List[Dict]:
    """Extrae titulares de una página específica de una sección"""
    url = url_base if pagina == 1 else f"{url_base}/{pagina}"
    titulares = []
    
    try:
        print(f"   ...leyendo {url}")
        response = SESSION.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"   ❌ Error {response.status_code} en {url}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        articulos = soup.find_all('article', class_='nota')
        
        # Procesar artículos en paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(procesar_articulo, art) for art in articulos]
            
            for future in as_completed(futures):
                resultado = future.result()
                if resultado:
                    titulares.append(resultado)
        
        return titulares
    
    except Exception as e:
        print(f"   ❌ Error crítico en {url}: {e}")
        return []


def extraer_todas_las_noticias() -> List[Dict]:
    """Función principal de scraping multi-sección"""
    from config import SECCIONES_CONFIG, DATA_STORE
    
    print(f"\n🔄 Iniciando scraping robusto de {len(SECCIONES_CONFIG)} secciones...")
    start_time = time.time()
    
    todas_las_noticias = []
    
    # Calcular total de tareas para la barra de progreso
    total_paginas = sum(SECCIONES_CONFIG.values())
    paginas_procesadas = 0
    
    # Iterar sobre cada sección configurada
    for seccion_url, num_paginas in SECCIONES_CONFIG.items():
        nombre_seccion = seccion_url.split('/')[-1].capitalize()
        print(f"\n📂 Procesando sección: {seccion_url} ({num_paginas} páginas)")
        
        DATA_STORE['current_action'] = f"Leyendo sección: {nombre_seccion}..."
        
        # Procesamos páginas de esta sección
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(extraer_titulares_pagina, seccion_url, pag): pag 
                for pag in range(1, num_paginas + 1)
            }
            
            for future in as_completed(futures):
                noticias_pagina = future.result()
                if noticias_pagina:
                    todas_las_noticias.extend(noticias_pagina)
                    DATA_STORE['titulares'].extend(noticias_pagina)
                
                # Actualizar progreso
                paginas_procesadas += 1
                # El scraping es el 45% del proceso total
                progreso_actual = int((paginas_procesadas / total_paginas) * 45)
                DATA_STORE['progress'] = progreso_actual
    
    duration = time.time() - start_time
    print(f"\n✅ Scraping completado: {len(todas_las_noticias)} noticias en {duration:.1f}s\n")
    return todas_las_noticias
