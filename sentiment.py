# ================================================================================
# sentiment.py - ANÁLISIS DE SENTIMIENTOS HÍBRIDO (BERT + PALABRAS CLAVE)
# ================================================================================

from transformers import pipeline
from typing import List, Dict, Tuple
import re

# ================================================================================
# 1. CONFIGURACIÓN DEL MODELO BERT MULTILINGUAL
# ================================================================================

print("🔄 Cargando modelo BERT multilingual para análisis de sentimientos...")
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=-1  # CPU
)
print("✅ Modelo BERT cargado correctamente\n")

# ================================================================================
# 2. PALABRAS CLAVE BOLIVIANAS (SISTEMA HÍBRIDO - PRIORIDAD MÁXIMA)
# ================================================================================

PALABRAS_NEGATIVAS = {
    'muerte', 'falleció', 'fallecimiento', 'accidente', 'tragedia',
    'bloqueo', 'protesta', 'enfrentamiento', 'represión', 'huelga',
    'inundación', 'desastre', 'crisis', 'delincuencia', 'corrupción',
    'violencia', 'robo', 'asesinato', 'homicidio', 'secuestro',
    'pandemia', 'fallece', 'se accidentó', 'muerto', 'herido',
    'víctima', 'victimas', 'víctimas', 'ataque', 'amenaza', 'denuncia', 'conflicto',
    'feminicidio', 'abuso', 'abuso sexual', 'violencia de género'
}

PALABRAS_POSITIVAS = {
    'ganó', 'triunfo', 'campeón', 'clasificó', 'acuerdo',
    'celebración', 'inauguración', 'construcción', 'crecimiento',
    'paz', 'seguridad', 'desarrollo', 'progreso', 'mejora',
    'éxito', 'victoria', 'inauguró', 'concluyó', 'completó',
    'superó', 'logro', 'récord', 'premio', 'reconocimiento',
    'avance', 'beneficio', 'esperanza', 'solución', 'acuerdo'
}

# Colores para cada sentimiento
COLORES = {
    'Positivo': '#4CAF50',
    'Negativo': '#FF6B6B',
    'Neutral': '#95A5A6'
}

# ================================================================================
# 3. FUNCIÓN PRINCIPAL: analizar_sentimiento_noticia()
# ================================================================================

def analizar_sentimiento_noticia(texto: str) -> Tuple[str, str, str, str]:
    """
    Analiza el sentimiento de una noticia usando sistema híbrido.
    
    PRIORIDAD:
    1. Sistema de palabras clave bolivianas (SOBREESCRIBE BERT)
    2. Modelo BERT multilingual (respaldo)
    
    Args:
        texto: Título + contenido de la noticia
    
    Returns:
        (emocion, color, nivel, descripcion)
        Ejemplos:
        - ("Negativo", "#FF6B6B", "Alto", "5 términos negativos")
        - ("Positivo", "#4CAF50", "Alto", "3 términos positivos")
        - ("Neutral", "#95A5A6", "Medio", "Score BERT: 0.82")
    """
    
    if not texto or not texto.strip():
        return ("Neutral", COLORES['Neutral'], "Bajo", "Sin contenido")
    
    texto_lower = texto.lower()
    
    # ========================================================================
    # PASO 1: SISTEMA DE PALABRAS CLAVE BOLIVIANAS (PRIORIDAD MÁXIMA)
    # ========================================================================
    
    score_negativo = 0
    score_positivo = 0
    
    # Contar palabras negativas
    for palabra in PALABRAS_NEGATIVAS:
        # Usar búsqueda de palabra completa (word boundary)
        if re.search(r'\b' + re.escape(palabra) + r'\b', texto_lower):
            score_negativo += 1
    
    # Contar palabras positivas
    for palabra in PALABRAS_POSITIVAS:
        if re.search(r'\b' + re.escape(palabra) + r'\b', texto_lower):
            score_positivo += 1
    
    # Aplicar reglas del sistema híbrido
    # Priorizar palabras negativas: si se detecta al menos una palabra negativa, clasificar como Negativo.
    if score_negativo > 0:
        return (
            "Negativo",
            COLORES['Negativo'],
            "Alto",
            f"{score_negativo} término{'s' if score_negativo > 1 else ''} negativo{'s' if score_negativo > 1 else ''}"
        )

    # Si no hay palabras negativas pero sí positivas, clasificar como Positivo.
    if score_positivo > 0:
        return (
            "Positivo",
            COLORES['Positivo'],
            "Alto",
            f"{score_positivo} término{'s' if score_positivo > 1 else ''} positivo{'s' if score_positivo > 1 else ''}"
        )
    
    # ========================================================================
    # PASO 2: MODELO BERT MULTILINGUAL (RESPALDO)
    # ========================================================================
    
    try:
        # Limitar texto para no exceder el límite del modelo
        texto_analisis = texto[:512]
        
        resultado = sentiment_pipeline(texto_analisis)[0]
        label = resultado['label']  # Formato: "1 star", "2 stars", etc.
        score = resultado['score']
        
        # Extraer número de estrellas
        estrellas = int(label.split()[0])
        
        # Mapear estrellas a sentimiento
        if estrellas <= 2:
            emocion = "Negativo"
        elif estrellas == 3:
            emocion = "Neutral"
        else:  # 4-5 estrellas
            emocion = "Positivo"
        
        # Determinar nivel según score
        nivel = "Alto" if score > 0.7 else "Medio"
        
        return (
            emocion,
            COLORES[emocion],
            nivel,
            f"BERT: {estrellas}★ (confianza: {score:.2f})"
        )
    
    except Exception as e:
        print(f"⚠️ Error en BERT: {e}")
        return ("Neutral", COLORES['Neutral'], "Bajo", "Error en análisis")


# ================================================================================
# 4. FUNCIÓN: enriquecer_noticias_con_sentimientos()
# ================================================================================

def enriquecer_noticias_con_sentimientos(noticias: List[Dict]) -> List[Dict]:
    """
    Añade campos de sentimiento a cada noticia.
    
    Campos añadidos:
    - sentimiento: str ("Positivo", "Negativo", "Neutral")
    - color_sentimiento: str (código hex)
    - nivel_sentimiento: str ("Alto", "Medio", "Bajo")
    - descripcion_sentimiento: str (explicación del análisis)
    
    Args:
        noticias: Lista de diccionarios con noticias
    
    Returns:
        Lista de noticias enriquecidas con sentimientos
    """
    from config import DATA_STORE
    
    print(f"\n{'='*60}")
    print(f"🎭 ANALIZANDO SENTIMIENTOS DE {len(noticias)} NOTICIAS")
    print(f"{'='*60}\n")
    
    total = len(noticias)
    
    for i, noticia in enumerate(noticias, 1):
        # Combinar título y contenido para análisis más preciso
        texto_completo = f"{noticia.get('titulo', '')} {noticia.get('contenido', '')}"
        
        # Analizar sentimiento
        emocion, color, nivel, descripcion = analizar_sentimiento_noticia(texto_completo)
        
        # Añadir campos a la noticia
        noticia['sentimiento'] = emocion
        noticia['color_sentimiento'] = color
        noticia['nivel_sentimiento'] = nivel
        noticia['descripcion_sentimiento'] = descripcion
        
        # Actualizar contador en DATA_STORE
        DATA_STORE['noticias_analizadas'] = i
        
        # Mostrar progreso cada 50 noticias
        if i % 50 == 0 or i == total:
            print(f"   Procesadas: {i}/{total} noticias ({(i/total)*100:.1f}%)")
    
    print(f"\n✅ Análisis de sentimientos completado\n")
    return noticias


# ================================================================================
# 5. FUNCIÓN: mostrar_estadisticas_sentimientos()
# ================================================================================

def mostrar_estadisticas_sentimientos(noticias: List[Dict]) -> None:
    """
    Muestra estadísticas visuales de sentimientos con barras de progreso.
    
    Args:
        noticias: Lista de noticias con sentimientos analizados
    """
    
    if not noticias:
        print("⚠️ No hay noticias para analizar")
        return
    
    # Contar sentimientos
    conteo = {'Positivo': 0, 'Negativo': 0, 'Neutral': 0}
    
    for noticia in noticias:
        sentimiento = noticia.get('sentimiento', 'Neutral')
        conteo[sentimiento] += 1
    
    total = len(noticias)
    
    # Mostrar estadísticas
    print(f"\n{'='*60}")
    print(f"📊 ESTADÍSTICAS DE SENTIMIENTOS ({total} noticias)")
    print(f"{'='*60}\n")
    
    # Ancho de la barra (50 caracteres)
    ancho_barra = 50
    
    for sentimiento in ['Positivo', 'Neutral', 'Negativo']:
        cantidad = conteo[sentimiento]
        porcentaje = (cantidad / total) * 100 if total > 0 else 0
        
        # Calcular bloques para la barra
        bloques = int((porcentaje / 100) * ancho_barra)
        barra = '█' * bloques + '░' * (ancho_barra - bloques)
        
        # Emoji según sentimiento
        emoji = {'Positivo': '😊', 'Neutral': '😐', 'Negativo': '😞'}[sentimiento]
        
        print(f"{emoji} {sentimiento:10} │ {barra} │ {cantidad:4} ({porcentaje:5.1f}%)")
    
    print(f"{'='*60}\n")


# ================================================================================
# 6. FUNCIONES DE BÚSQUEDA POR SENTIMIENTO
# ================================================================================

def buscar_noticias_positivas(noticias: List[Dict]) -> List[Dict]:
    """Filtra y retorna solo noticias positivas"""
    return [n for n in noticias if n.get('sentimiento') == 'Positivo']


def buscar_noticias_negativas(noticias: List[Dict]) -> List[Dict]:
    """Filtra y retorna solo noticias negativas"""
    return [n for n in noticias if n.get('sentimiento') == 'Negativo']


def buscar_noticias_neutrales(noticias: List[Dict]) -> List[Dict]:
    """Filtra y retorna solo noticias neutrales"""
    return [n for n in noticias if n.get('sentimiento') == 'Neutral']


def mostrar_resumen_sentimientos(noticias: List[Dict]) -> str:
    """
    Genera un resumen textual de los sentimientos.
    
    Returns:
        String con resumen formateado
    """
    
    if not noticias:
        return "No hay noticias para analizar."
    
    conteo = {'Positivo': 0, 'Negativo': 0, 'Neutral': 0}
    
    for noticia in noticias:
        sentimiento = noticia.get('sentimiento', 'Neutral')
        conteo[sentimiento] += 1
    
    total = len(noticias)
    
    resumen = f"📊 **Resumen de Sentimientos** ({total} noticias):\n\n"
    resumen += f"😊 **Positivas:** {conteo['Positivo']} ({(conteo['Positivo']/total)*100:.1f}%)\n"
    resumen += f"😐 **Neutrales:** {conteo['Neutral']} ({(conteo['Neutral']/total)*100:.1f}%)\n"
    resumen += f"😞 **Negativas:** {conteo['Negativo']} ({(conteo['Negativo']/total)*100:.1f}%)\n"
    
    return resumen


# ================================================================================
# 7. FUNCIÓN AUXILIAR: detectar_consulta_sentimiento()
# ================================================================================

def detectar_consulta_sentimiento(pregunta: str) -> str:
    """
    Detecta si el usuario está preguntando por un sentimiento específico.
    
    Returns:
        "positivo", "negativo", "neutral", o "" si no hay match
    """
    
    pregunta_lower = pregunta.lower()
    
    # Patrones de búsqueda
    if any(palabra in pregunta_lower for palabra in ['positiva', 'positivas', 'buena', 'buenas', 'alegre', 'alegres']):
        return "positivo"
    
    if any(palabra in pregunta_lower for palabra in ['negativa', 'negativas', 'mala', 'malas', 'triste', 'tristes']):
        return "negativo"
    
    if any(palabra in pregunta_lower for palabra in ['neutral', 'neutrales', 'normal', 'normales']):
        return "neutral"
    
    return ""


# ================================================================================
# TESTING (solo se ejecuta si se corre este archivo directamente)
# ================================================================================

if __name__ == "__main__":
    # Casos de prueba
    print("\n" + "="*60)
    print("🧪 PRUEBAS DE ANÁLISIS DE SENTIMIENTOS")
    print("="*60 + "\n")
    
    casos_prueba = [
        "Tragedia en La Paz: Accidente de tránsito deja 5 muertos y varios heridos",
        "Bolivia clasificó al mundial tras vencer 3-0 a Argentina en un partido histórico",
        "El gobierno anuncia nuevas medidas económicas para el próximo año",
        "Violentos enfrentamientos en bloqueo de carreteras dejan varios heridos",
        "Inauguración de nuevo hospital en Santa Cruz beneficiará a miles de familias"
    ]
    
    for i, caso in enumerate(casos_prueba, 1):
        print(f"Caso {i}: {caso[:60]}...")
        emocion, color, nivel, desc = analizar_sentimiento_noticia(caso)
        print(f"   → {emocion} ({nivel}) - {desc}")
        print(f"   → Color: {color}\n")
