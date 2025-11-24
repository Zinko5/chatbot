# ================================================================================
# chatbot.py - CLASE PRINCIPAL DEL BOT
# ================================================================================

import threading
from typing import List, Dict
from config import DATA_STORE
from scraper import extraer_todas_las_noticias
from brain import SemanticSearch, GroqBrain


class NewsChatBot:
    """Chatbot principal que integra todos los componentes"""
    
    def __init__(self):
        self.search_engine = None
        self.brain = None
        self.noticias = []
        self.initialized = False
        self.initializing = False
    
    def initialize_async(self):
        """Inicializa el bot en un thread separado (no bloquea el servidor)"""
        if self.initializing:
            return
        
        self.initializing = True
        thread = threading.Thread(target=self._do_initialize)
        thread.daemon = True
        thread.start()
    
    def _do_initialize(self):
        """Proceso de inicialización real"""
        print("\n" + "=" * 60)
        print("🚀 INICIALIZANDO NEWS CHATBOT (en background)")
        print("=" * 60 + "\n")
        
        try:
            # 1. Scraping
            DATA_STORE['titulares'] = [] # Limpiar antes de empezar
            DATA_STORE['progress'] = 0
            self.noticias = extraer_todas_las_noticias()
            
            # 2. Cargar modelos de IA
            DATA_STORE['current_action'] = "Cargando modelos de IA..."
            DATA_STORE['progress'] = 85
            self.search_engine = SemanticSearch()
            self.brain = GroqBrain()
            
            # 3. Indexar noticias
            if self.noticias:
                DATA_STORE['current_action'] = f"Generando embeddings para {len(self.noticias)} noticias..."
                DATA_STORE['progress'] = 90
                self.search_engine.index_documents(self.noticias)
            
            DATA_STORE['current_action'] = "Finalizando..."
            DATA_STORE['progress'] = 100
            self.initialized = True
            DATA_STORE['initialized'] = True
            
            print("=" * 60)
            print("✅ BOT LISTO PARA RESPONDER")
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
        finally:
            self.initializing = False
    
    def answer(self, question: str) -> str:
        """Procesa una pregunta y devuelve respuesta"""
        
        # Verificar estado
        if not self.initialized:
            if self.initializing:
                return "⏳ El bot se está inicializando, por favor espera unos segundos y vuelve a preguntar..."
            else:
                return "❌ El bot no está inicializado. Recarga la página."
        
        if not question or not question.strip():
            return "Por favor, escribe una pregunta."
        
        question = question.strip()
        print(f"\n💬 Pregunta: {question[:50]}...")
        
        try:
            # 1. Buscar noticias relevantes
            relevant = self.search_engine.search(question, top_k=5)
            
            if not relevant:
                return ("🔍 No encontré noticias relacionadas con tu pregunta.\n\n"
                       "💡 **Sugerencias:**\n"
                       "• Usa palabras clave más específicas\n"
                       "• Pregunta sobre temas de actualidad boliviana")
            
            # 2. Generar respuesta
            response = self.brain.generate(question, relevant)
            
            # 3. Agregar fuentes
            sources = "\n\n---\n📚 **Fuentes:**\n"
            for n in relevant[:3]:
                titulo = n['titulo'][:50] + "..." if len(n['titulo']) > 50 else n['titulo']
                sources += f"• [{titulo}]({n['url']})\n"
            
            return response + sources
            
        except Exception as e:
            print(f"❌ Error procesando pregunta: {e}")
            return f"❌ Error al procesar la pregunta: {str(e)}"


# Instancia global del bot
bot = NewsChatBot()