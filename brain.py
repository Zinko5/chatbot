# ================================================================================
# brain.py - MOTOR DE IA (EMBEDDINGS + GROQ) - FORMATO MEJORADO
# ================================================================================

import numpy as np
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
from config import GROQ_API_KEY, EMBEDDING_MODEL


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
    
    def generate(self, question: str, context: List[Dict]) -> str:
        """Genera respuesta basada en contexto"""
        
        if not self.enabled:
            return self._basic_response(context)
        
        context_text = ""
        for i, n in enumerate(context[:3], 1):
            context_text += f"\nNOTICIA {i}:\n"
            context_text += f"Título: {n['titulo']}\n"
            context_text += f"Contenido: {n.get('contenido', '')[:500]}\n"
        
        system = """Eres un asistente de noticias bolivianas.
Reglas:
- Responde SOLO con información de las noticias proporcionadas
- NO inventes datos
- MANTÉN los nombres propios exactos (ej: 'Edmand' no es 'Edmundo')
- Sé conciso
- Responde en español"""

        user = f"""NOTICIAS:
{context_text}

PREGUNTA: {question}

Responde basándote solo en las noticias. Respeta los nombres propios y no inventes datos."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.3,
                max_tokens=500
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