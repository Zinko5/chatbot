# Ficha Técnica – **El Deber Bot**

---

## 1️⃣ Visión General del Proyecto

**El Deber Bot** es un agente conversacional especializado en noticias del portal boliviano *eldeber.com.bo*.  Combina varias capas de procesamiento:

1. **Scraper robusto** que extrae titulares y contenidos de múltiples secciones.
2. **Análisis de sentimientos híbrido** (palabras‑clave bolivianas + modelo BERT multilingual).
3. **Generación de embeddings** con *Sentence‑Transformer* para búsqueda semántica.
4. **Motor de IA** basado en la API de **Groq** (modelo `llama‑3.1‑8b‑instant`).
5. **Interfaz web** (Flask) y **bot de Telegram** que exponen la funcionalidad al usuario.

Todo el flujo está orquestado por la clase `NewsChatBot` que se inicializa en segundo plano para que la UI sea responsiva.

---

## 2️⃣ Arquitectura de Componentes

```
┌─────────────────────┐          ┌─────────────────────┐
│  Telegram Bot       │          │  Flask Web UI       │
│  (telegram_bot.py) │  <--->   │  (app.py)          │
└─────────▲───────────┘          └───────▲─────────────┘
          │                               │
          │   Shared global DATA_STORE    │
          │   (config.py)                │
          ▼                               ▼
   ┌─────────────────────┐   ┌─────────────────────┐
   │  NewsChatBot        │   │  Sentiment Engine   │
   │  (chatbot.py)      │   │  (sentiment.py)    │
   └───────▲─────────────┘   └───────▲─────────────┘
           │                         │
   ┌───────┴─────────────┐   ┌───────┴─────────────┐
   │  Scraper            │   │  Embeddings Engine  │
   │  (scraper.py)       │   │  (brain.py)        │
   └─────────────────────┘   └─────────────────────┘
```

* **DATA_STORE** – diccionario global que mantiene el estado compartido (titulares, progreso, flags de inicialización, etc.).
* Cada componente es **thread‑safe** porque se accede únicamente desde el hilo de inicialización o desde peticiones HTTP/Telegram que solo leen.

---

## 3️⃣ Configuración y Variables de Entorno

| Variable | Descripción | Fuente |
|----------|-------------|--------|
| `GROQ_API_KEY` | API‑key para la plataforma Groq. | `.env` (cargado con `dotenv`)
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram. | `.env`
| `SECCIONES_CONFIG` | Mapeo *URL → número de páginas* a rastrear. | `config.py`
| `HEADERS` | Cabecera HTTP para evitar bloqueos de scraper. | `config.py`
| `EMBEDDING_MODEL` | Modelo Sentence‑Transformer usado para embeddings. | `config.py`
| `DATA_STORE` | Estructura global de estado (titulares, progreso, flags). | `config.py`

---

## 4️⃣ Scraper – `scraper.py`

### 4.1 Sesión HTTP Resistente
* **`crear_sesion()`** crea una `requests.Session` con `urllib3.Retry` (3 intentos, back‑off exponencial, códigos 429/5xx).
* Cabecera `User‑Agent` configurable en `HEADERS`.

### 4.2 Extracción de Contenido
* `extraer_contenido_noticia(url)`:
  * Pausa aleatoria `0.1‑0.5 s` para respetar el sitio.
  * Busca varios selectores (`text-editor`, `nota-body`, …) y, como fallback, cualquier `<article>`.
  * Filtra párrafos menores a 30 caracteres y elimina frases “Lee también”.
  * Limita a 1500 caracteres para no superar el contexto de LLM.

### 4.3 Procesado de Artículos
* `procesar_articulo(art)` extrae título, URL y contenido, normaliza enlaces relativos.
* Devuelve `None` si falla; los errores se capturan y no interrumpen el flujo.

### 4.4 Paralelismo
* `ThreadPoolExecutor(max_workers=4)` procesa artículos de una página en paralelo.
* `extraer_titulares_pagina` y `extraer_todas_las_noticias` usan `max_workers=2` para paralelizar la descarga de páginas por sección.

### 4.5 Progreso y Métricas
* `DATA_STORE['progress']` se actualiza en tiempo real (0‑45 % durante scraping).
* `DATA_STORE['titulares']` acumula resultados y se comparte con la UI.

---

## 5️⃣ Análisis de Sentimientos – `sentiment.py`

### 5.1 Modelo BERT Multilingüe
* Cargado con `pipeline('sentiment-analysis', model='nlptown/bert-base-multilingual-uncased-sentiment')`.
* Ejecutado en CPU (`device=-1`).

### 5.2 Diccionarios de Palabras‑Clave Bolivianas
* **Negativas** (≈ 30 términos) y **Positivas** (≈ 30 términos) enfocadas a la realidad local (p.ej., *tragedia*, *ganó*).
* Prioridad **máxima**: si se detecta cualquier término negativo, la noticia se clasifica como **Negativo** sin consultar BERT.

### 5.3 Función Principal
* `analizar_sentimiento_noticia(texto) → (emocion, color, nivel, descripcion)`
  * Busca coincidencias de palabras‑clave usando expresiones regulares con límites de palabra (`\b`).
  * Si no hay coincidencias, recurre al modelo BERT (estrella 1‑2 → Negativo, 3 → Neutral, 4‑5 → Positivo).
  * Nivel de confianza: **Alto** (> 0.7), **Medio** (≤ 0.7), **Bajo** (error).
  * Devuelve también el color hex asociado (`COLORES`).

### 5.4 Enriquecimiento de Noticias
* `enriquecer_noticias_con_sentimientos(noticias)` recorre la lista, combina título + contenido y añade los campos:
  * `sentimiento`, `color_sentimiento`, `nivel_sentimiento`, `descripcion_sentimiento`.
* Actualiza `DATA_STORE['noticias_analizadas']` para que la UI muestre progreso (0‑65 % del flujo total).

### 5.5 Estadísticas y Búsqueda por Sentimiento
* `mostrar_estadisticas_sentimientos` imprime barras de progreso en consola.
* Funciones `buscar_noticias_positivas/negativas/neutrales` filtran la lista.
* `detectar_consulta_sentimiento(pregunta)` reconoce si el usuario pide “noticias positivas”, etc., para redirigir la lógica en `chatbot.answer`.

---

## 6️⃣ Embeddings y Búsqueda Semántica – `brain.py`

### 6.1 Modelo de Embeddings
* `SentenceTransformer(EMBEDDING_MODEL)` donde `EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"`.
* Cargado una sola vez (singleton) para evitar recargas costosas.

### 6.2 Indexado
* `SemanticSearch.index_documents(documents)` genera embeddings de la concatenación `"{titulo}. {resumen}"`.
* Se muestra barra de progreso (`show_progress_bar=True`).

### 6.3 Búsqueda Híbrida
* **Semántica**: encode la query (y su versión title‑cased) y calcula similitud coseno contra todos los embeddings.
* **Keyword Boosting**: si la query aparece literalmente en título o resumen, se suma **0.3** al score.
* **Ranking**: top‑k (default 3) con umbral 0.12 (más permisivo gracias al boost).
* Resultado incluye `score` y los campos originales de la noticia.

---

## 7️⃣ Motor de IA – Groq (`brain.GroqBrain`)

* Conexión segura mediante `GROQ_API_KEY`.
* Modelo por defecto: `llama-3.1-8b-instant`.
* **Prompt system**: instrucciones estrictas para que el modelo solo use la información de las noticias y no invente datos.
* **Fallback** (`_basic_response`) genera una respuesta estática cuando Groq no está configurado.
* Parámetros de generación: `temperature=0.3`, `max_tokens=500`.

---

## 8️⃣ Bot de Telegram – `telegram_bot.py`

* Usa `python‑telegram‑bot` (versión implícita en `requirements.txt`).
* **Handlers** principales:
  * `/start` – saludo y breve descripción.
  * Mensajes de texto – delega a `bot.answer` y envía la respuesta.
* El bot se inicia **en un thread** separado desde `app.py` para que Flask y Telegram coexistan.
* Manejo de estados: si el bot está todavía inicializando, responde con `⏳ El bot se está inicializando…`.

---

## 9️⃣ Aplicación Web – `app.py`

* Flask app que sirve los templates bajo `templates/` (no mostrados aquí).
* Ruta principal `/` renderiza la UI que muestra:
  * Barra de progreso (`DATA_STORE['progress']`).
  * Lista de titulares (`DATA_STORE['titulares']`).
  * Estadísticas de sentimientos.
* Al iniciar, llama a `bot.initialize_async()` para lanzar la inicialización en background.
* El servidor se ejecuta con `python3 app.py` (modo desarrollo) y está preparado para `npm run dev` solo si se migra a Vite (no usado actualmente).

---

## 🔧 Dependencias – `requirements.txt`
```
flask
python-telegram-bot
requests
beautifulsoup4
urllib3
sentence-transformers
scikit-learn
groq
transformers
torch   # required by transformers (CPU only)
python-dotenv
```
> Todas las librerías son **CPU‑only**; el proyecto está pensado para ejecutarse en una máquina con Python 3.10+.

---

## 🚀 Puesta en Marcha
1. **Clonar** el repositorio.
2. Crear entorno virtual y activar:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Copiar y rellenar `.env`:
   ```bash
   cp .env.example .env
   # editar .env y añadir GROQ_API_KEY y TELEGRAM_BOT_TOKEN
   ```
5. Ejecutar la aplicación:
   ```bash
   python3 app.py
   ```
   * El bot tarda **entre 2 y 5 min** en completarse (scraping + sentimientos + carga de modelos).
   * Acceder a `http://127.0.0.1:5000` para la UI web.
   * Interactuar con el bot de Telegram usando el token configurado.

---

## 📚 Extensibilidad
| Área | Qué se puede ampliar |
|------|----------------------|
| **Scraper** | Añadir nuevas secciones en `SECCIONES_CONFIG`; incrementar `max_workers` para mayor paralelismo.
| **Sentimientos** | Ampliar los diccionarios de palabras‑clave o cambiar el modelo BERT por uno más grande.
| **Embeddings** | Sustituir `EMBEDDING_MODEL` por un modelo especializado en noticias.
| **IA** | Cambiar a otro modelo Groq o a OpenAI/Claude simplemente modificando `GroqBrain`.
| **UI** | Migrar a Vite/Next.js para una SPA más moderna (manteniendo la API Flask).

---

## 🛡️ Seguridad y Buenas Prácticas
* **API keys** nunca se versionan; se cargan desde `.env`.
* Scraper respeta `robots.txt` implícitamente mediante pausas aleatorias y número limitado de peticiones concurrentes.
* Todos los accesos a `DATA_STORE` son de solo lectura desde la UI; la escritura ocurre únicamente en el hilo de inicialización.
* El bot de Telegram valida que el mensaje no sea demasiado largo antes de enviarlo a Groq (limite 500 tokens).

---

## 📌 Resumen rápido para mantenedores
* **Inicialización** → Scraping (0‑45 %) → Sentimientos (45‑65 %) → Carga de modelos (65‑78 %) → Embeddings (78‑90 %) → Final (90‑100 %).
* **Estado global** → `DATA_STORE` (titulares, progreso, flags).
* **Puntos críticos** → Conexión a Groq (requiere API key válida) y disponibilidad del sitio `eldeber.com.bo`.
* **Tiempo de arranque** → 2‑5 min (dependiendo de la velocidad de red).

---

*Ficha técnica generada automáticamente por Antigravity – agente de codificación avanzada.*
