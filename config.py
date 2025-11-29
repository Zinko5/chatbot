# ================================================================================
# config.py - CONFIGURACIÓN DEL NEWSBOT
# ================================================================================

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- API KEY DE GROQ ---
# Se lee desde el archivo .env (nunca se sube a GitHub)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️ ADVERTENCIA: No se encontró GROQ_API_KEY en el archivo .env")

# --- TELEGRAM TOKEN ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("⚠️ ADVERTENCIA: No se encontró TELEGRAM_BOT_TOKEN en el archivo .env")

# --- CONFIGURACIÓN DE SCRAPING ---
# Configuración de secciones a rastrear
# Formato: "URL": cantidad_de_paginas
SECCIONES_CONFIG = {
    "https://eldeber.com.bo/pais": 1,
    # "https://eldeber.com.bo/economia": 3,
    # "https://eldeber.com.bo/mundo": 3,
    # "https://eldeber.com.bo/educacion-y-sociedad": 3,
    # "https://eldeber.com.bo/deportes": 3
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# --- MODELO DE EMBEDDINGS ---
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# --- ALMACENAMIENTO GLOBAL ---
DATA_STORE = {
    'titulares': [],
    'initialized': False
}
