# ================================================================================
# brain.py - MOTOR DE IA (EMBEDDINGS + GROQ) - FORMATO MEJORADO
# ================================================================================

import numpy as np
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
from config import GROQ_API_KEY, EMBEDDING_MODEL, DATA_STORE


class SemanticSearch:
    """Motor de búsqueda semántica"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if SemanticSearch._model is None:
            print(f"🔄 Cargando modelo de embeddings...")
            SemanticSearch._model = SentenceTransformer(EMBEDDING_MODEL)
            print("✅ Modelo cargado\n")
        
        self.model = SemanticSearch._model
        self.embeddings = None
        self.documents = []
    
    def index_documents(self, documents: List[Dict]):
        """Genera embeddings para las noticias"""
        self.documents = documents
        # Revertimos a texto original (con mayúsculas) para mejor calidad de embeddings
        texts = [f"{doc['titulo']}. {doc.get('resumen', '')}" for doc in documents]
        
        print(f"📊 Generando embeddings para {len(texts)} noticias...")
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        print(f"✅ Embeddings listos\n")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Busca noticias similares (Híbrido: Semántico + Keyword Boosting)"""
        if self.embeddings is None or len(self.documents) == 0:
            return []
        
        # 1. Búsqueda Semántica (Multi-Query)
        queries = [query]
        if query.islower():
            queries.append(query.title()) # 'kast' -> 'Kast'
        
        query_embeddings = self.model.encode(queries)
        all_similarities = cosine_similarity(query_embeddings, self.embeddings)
        similarities = np.max(all_similarities, axis=0)
        
        # 2. Keyword Boosting (Crucial para nombres propios cortos)
        # Si la palabra exacta está en el título/resumen, aumentamos su score
        query_lower = query.lower()
        for idx, doc in enumerate(self.documents):
            content = (doc['titulo'] + " " + doc.get('resumen', '')).lower()
            if query_lower in content:
                # Boost significativo para asegurar que aparezca
                similarities[idx] += 0.3
        
        # 3. Ranking y Filtrado
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.12: # Umbral más permisivo gracias al boost
                results.append({
                    **self.documents[idx],
                    'score': float(similarities[idx])
                })
        return results


class GroqBrain:
    """Cerebro con Groq AI"""
    
    def __init__(self):
        if GROQ_API_KEY and len(GROQ_API_KEY) > 20 and "PEGA" not in GROQ_API_KEY:
            self.client = Groq(api_key=GROQ_API_KEY)
            self.enabled = True
            print("✅ Groq AI conectado\n")
        else:
            self.client = None
            self.enabled = False
            print("⚠️ Groq AI no configurado (modo básico)\n")
        
        self.model = "llama-3.1-8b-instant"
    
    def generate(self, question: str, context: List[Dict], history: List[Dict] = None, previous_context: List[Dict] = None, global_stats: Dict = None) -> str:
        """Genera respuesta basada en contexto y memoria de conversación"""
        
        if not self.enabled:
            return self._basic_response(context)
        
        # Formatear contexto actual
        current_context_text = ""
        if context:
            current_context_text = "--- RESULTADOS DE BÚSQUEDA ACTUAL ---\n"
            for i, n in enumerate(context[:3], 1):
                current_context_text += f"NOTICIA ACTUAL {i}:\n"
                current_context_text += f"Título: {n['titulo']}\n"
                current_context_text += f"Contenido: {n.get('contenido', '')[:800]}\n\n"
        else:
            current_context_text = "--- NO SE ENCONTRARON NOTICIAS NUEVAS RELEVANTES ---\n"

        # Formatear contexto anterior (si existe)
        prev_context_text = ""
        if previous_context:
            prev_context_text = "--- NOTICIAS VISTAS ANTERIORMENTE (Contexto de la conversación) ---\n"
            for i, n in enumerate(previous_context[:3], 1):
                prev_context_text += f"NOTICIA PREVIA {i}:\n"
                prev_context_text += f"Título: {n['titulo']}\n"
                prev_context_text += f"Contenido: {n.get('contenido', '')[:800]}\n\n"

        system = """Eres un asistente de noticias bolivianas inteligente y servicial.
Reglas:
1. Tienes acceso a DOS fuentes de información:
   - RESULTADOS DE BÚSQUEDA ACTUAL: Noticias encontradas para la pregunta actual.
   - NOTICIAS VISTAS ANTERIORMENTE: Noticias de las que estabas hablando antes.
2. Si el usuario pregunta "qué pasó con la noticia 2" o "profundiza en la primera", REFIÉRETE a las "NOTICIAS VISTAS ANTERIORMENTE".
3. Si el usuario cambia de tema, usa los "RESULTADOS DE BÚSQUEDA ACTUAL".
4. Responde SOLO con información proporcionada.
5. EXCEPCIÓN: Si te preguntan por el clima, USA la información del clima.
6. MANTÉN los nombres propios exactos.
7. Sé conversacional y fluido.
8. Al final, pregunta si desea profundizar.
9. Responde en español."""

        # Inyectar estadísticas globales si existen
        if global_stats:
            system += "\n\n--- PANORAMA GENERAL DE NOTICIAS (ESTADÍSTICAS) ---\n"
            system += f"Total noticias analizadas: {global_stats['total']}\n"
            system += "Distribución de sentimientos:\n"
            for sent, pct in global_stats['porcentajes'].items():
                emoji = {'Positivo': '😊', 'Neutral': '😐', 'Negativo': '😞'}.get(sent, '')
                system += f"- {sent} {emoji}: {pct:.1f}% ({global_stats['conteo'][sent]} noticias)\n"
            system += "Usa esta información si el usuario pregunta por el 'panorama', 'porcentajes' o 'cómo se ven las noticias en general'.\n"
            system += "---------------------------------------------------\n"

        # Inyectar clima si existe
        weather = DATA_STORE.get('weather')
        if weather:
            system += f"\n\n--- INFORMACIÓN DEL CLIMA ACTUAL ---\n"
            system += f"Ciudad: {weather['city']}\n"
            system += f"Temperatura: {weather['temp']}°C\n"
            system += f"Condición: {weather['condition']} {weather['emoji']}\n"
            system += "------------------------------------\n"

        # Construir mensajes con historial
        messages = [{"role": "system", "content": system}]
        
        # Agregar historial (últimos 4 mensajes para contexto inmediato)
        if history:
            for msg in history[-4:]:
                messages.append(msg)

        # Mensaje actual con contexto
        user_content = f"""{prev_context_text}

{current_context_text}

PREGUNTA DEL USUARIO: {question}

Instrucción: Analiza si la pregunta se refiere a las noticias anteriores o a las nuevas. Responde acorde."""

        messages.append({"role": "user", "content": user_content})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=800 # Aumentamos tokens para respuestas profundas
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Error Groq: {e}")
            return self._basic_response(context)
    
    def _basic_response(self, context: List[Dict]) -> str:
        """Respuesta sin IA - FORMATO MEJORADO"""
        if not context:
            return "🔍 No encontré noticias relacionadas con tu pregunta.\n\n💡 Intenta usar otras palabras clave o pregunta sobre temas de actualidad boliviana."
        
        # Encabezado
        num_noticias = len(context[:3])
        resp = f"📰 Encontré {num_noticias} noticia{'s' if num_noticias > 1 else ''} relevante{'s' if num_noticias > 1 else ''}:\n\n"
        
        # Listado de noticias con formato limpio
        for i, n in enumerate(context[:3], 1):
            titulo = n['titulo']
            score = n.get('score', 0)
            url = n['url']
            resumen = n.get('resumen', '')
            
            # Barra de relevancia visual
            relevancia_porcentaje = int(score * 100)
            barras = '█' * (relevancia_porcentaje // 20)
            
            resp += f"{'─' * 60}\n"
            resp += f"📌 {i}. {titulo}\n\n"
            
            # Relevancia
            resp += f"   📊 Relevancia: {barras} {relevancia_porcentaje}%\n"
            
            # Resumen si existe
            if resumen and len(resumen) > 50:
                resumen_corto = resumen[:150] + "..." if len(resumen) > 150 else resumen
                resp += f"   📝 {resumen_corto}\n"
            
            # Link
            resp += f"   🔗 {url}\n\n"
        
        # Footer con tip
        resp += f"{'─' * 60}\n"
        resp += "💡 Activa Groq AI para obtener respuestas más elaboradas y contextualizadas."
        
        return resp