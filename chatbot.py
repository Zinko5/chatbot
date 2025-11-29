# ================================================================================
# chatbot.py - CLASE PRINCIPAL DEL BOT
# ================================================================================

import threading
import re
from typing import List, Dict
from config import DATA_STORE
from scraper import extraer_todas_las_noticias
from brain import SemanticSearch, GroqBrain
from sentiment import (
    enriquecer_noticias_con_sentimientos,
    mostrar_estadisticas_sentimientos,
    detectar_consulta_sentimiento,
    buscar_noticias_positivas,
    buscar_noticias_negativas,
    buscar_noticias_neutrales,
    mostrar_resumen_sentimientos
)


class NewsChatBot:
    """Chatbot principal que integra todos los componentes"""
    
    def __init__(self):
        self.search_engine = None
        self.brain = None
        self.noticias = []
        self.initialized = False
        self.initializing = False
        self.histories = {} # Memoria de conversación por sesión: {session_id: [msgs]}
    
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
            DATA_STORE['noticias_analizadas'] = 0  # Contador de análisis
            self.noticias = extraer_todas_las_noticias()
            
            # 2. Análisis de sentimientos (NUEVO)
            if self.noticias:
                DATA_STORE['current_action'] = "Analizando sentimientos de las noticias..."
                DATA_STORE['progress'] = 65
                self.noticias = enriquecer_noticias_con_sentimientos(self.noticias)
                mostrar_estadisticas_sentimientos(self.noticias)
                # Actualizar titulares con sentimientos
                DATA_STORE['titulares'] = self.noticias
            
            # 3. Cargar modelos de IA
            DATA_STORE['current_action'] = "Cargando modelos de IA..."
            DATA_STORE['progress'] = 78
            self.search_engine = SemanticSearch()
            self.brain = GroqBrain()
            
            # 4. Indexar noticias
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
    
    def _is_follow_up(self, text: str) -> bool:
        """Detecta si la pregunta es un seguimiento de la anterior"""
        text = text.lower()
        patterns = [
            r"(sobre|en|de) la (\d+|uno|dos|tres|primera|segunda|tercera)",
            r"(noticia|nota|artículo|articulo) (\d+|uno|dos|tres|primera|segunda|tercera)",
            r"\b(profundiza|profundizar|amplia|ampliar|detalles|más sobre|mas sobre|cuéntame más|cuentame mas)\b",
            r"\b(qué pasó con|que paso con|y la|y el)\b"
        ]
        return any(re.search(p, text) for p in patterns)

    def answer(self, question: str, session_id: str = 'default') -> str:
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
        print(f"\n💬 Pregunta ({session_id}): {question[:50]}...")
        
        try:
            # ====================================================================
            # DETECCIÓN DE CONSULTAS POR SENTIMIENTO
            # ====================================================================
            
            tipo_sentimiento = detectar_consulta_sentimiento(question)
            
            if tipo_sentimiento:
                # Filtrar noticias por sentimiento
                if tipo_sentimiento == "positivo":
                    noticias_filtradas = buscar_noticias_positivas(self.noticias)
                    emoji = "😊"
                    titulo = "Noticias Positivas"
                elif tipo_sentimiento == "negativo":
                    noticias_filtradas = buscar_noticias_negativas(self.noticias)
                    emoji = "😞"
                    titulo = "Noticias Negativas"
                else:  # neutral
                    noticias_filtradas = buscar_noticias_neutrales(self.noticias)
                    emoji = "😐"
                    titulo = "Noticias Neutrales"
                
                if not noticias_filtradas:
                    return f"{emoji} No encontré noticias con sentimiento {tipo_sentimiento}."
                
                # Mostrar resumen + primeras noticias
                total = len(noticias_filtradas)
                respuesta = f"{emoji} **{titulo}** (Total: {total})\n\n"
                
                # Mostrar las primeras 5
                for i, noticia in enumerate(noticias_filtradas[:5], 1):
                    titulo_corto = noticia['titulo'][:60] + "..." if len(noticia['titulo']) > 60 else noticia['titulo']
                    respuesta += f"{i}. [{titulo_corto}]({noticia['url']})\n"
                    respuesta += f"   *{noticia['descripcion_sentimiento']}*\n\n"
                
                if total > 5:
                    respuesta += f"\n💡 *Hay {total - 5} noticias más con este sentimiento.*"
                
                return respuesta
            
            # ====================================================================
            # BÚSQUEDA SEMÁNTICA CON MEMORIA DE CONTEXTO
            # ====================================================================
            
            # Obtener estado de la sesión
            session_state = self.histories.get(session_id, {'history': [], 'last_context': []})
            session_history = session_state['history']
            last_context = session_state.get('last_context', [])
            
            relevant = []
            using_stored_context = False
            
            # 1. Verificar si es una pregunta de seguimiento (para usar contexto anterior)
            if last_context and self._is_follow_up(question):
                print("🧠 Detectado seguimiento: Usando contexto anterior.")
                relevant = last_context
                using_stored_context = True
            else:
                # 2. Si no es seguimiento, buscar noticias nuevas
                relevant = self.search_engine.search(question, top_k=3)
            
            # --- TRUCO: INYECTAR CLIMA COMO NOTICIA ---
            # Si la pregunta es sobre clima, agregamos una "noticia falsa" con el dato real
            # Esto obliga al LLM a leerlo como parte del contexto
            keywords_clima = ['clima', 'tiempo', 'temperatura', 'calor', 'frío', 'lluvia', 'pronóstico']
            if any(k in question.lower() for k in keywords_clima):
                weather = DATA_STORE.get('weather')
                print(f"🤖 Chatbot viendo clima: {weather}") # DEBUG
                if weather:
                    print("🌤️ Inyectando contexto de clima...")
                    # Creamos una "noticia" sintética
                    weather_news = {
                        'titulo': f"Reporte del Clima Actual en {weather['city']}",
                        'url': 'https://www.accuweather.com/es/bo/bolivia-weather',
                        'resumen': f"El clima actual en {weather['city']} presenta una temperatura de {weather['temp']}°C. La condición es {weather['condition']} {weather['emoji']}.",
                        'contenido': f"Informe meteorológico en tiempo real para {weather['city']}. Temperatura actual: {weather['temp']} grados Celsius. Condición del cielo: {weather['condition']}. Se recomienda tomar previsiones según este reporte actualizado.",
                        'sentimiento': 'Neutral',
                        'score': 0.99 # Score alto para que aparezca primero
                    }
                    # Insertamos al principio
                    relevant.insert(0, weather_news)
            
            if not relevant:
                return ("🔍 No encontré noticias relacionadas con tu pregunta.\n\n"
                       "💡 **Sugerencias:**\n"
                       "• Usa palabras clave más específicas\n"
                       "• Pregunta sobre temas de actualidad boliviana\n"
                       "• Prueba buscar por sentimiento: 'noticias positivas', 'noticias negativas'")
            
            # Obtener estado de la sesión (ya lo tenemos arriba, pero necesitamos actualizarlo)
            # session_history y last_context ya fueron extraídos
            
            # 2. Generar respuesta con IA
            # Si usamos el contexto guardado, lo pasamos como 'context' (actual) para que el prompt lo entienda como foco principal.
            # No es necesario pasar 'previous_context' si ya estamos forzando el foco.
            response = self.brain.generate(question, relevant, session_history, previous_context=last_context if not using_stored_context else None)
            
            # Actualizar historial
            session_history.append({"role": "user", "content": question})
            session_history.append({"role": "assistant", "content": response})
            
            # Limitar historial (últimos 10 mensajes)
            if len(session_history) > 10:
                session_history = session_history[-10:]
            
            # Guardar estado actualizado
            # Si usamos contexto guardado, lo mantenemos. Si buscamos nuevo, guardamos el nuevo.
            new_context_to_save = relevant if relevant else last_context
            
            self.histories[session_id] = {
                'history': session_history,
                'last_context': new_context_to_save
            }
            
            # 3. Agregar fuentes CON SENTIMIENTOS
            sources = "\n\n---\n📚 **Fuentes:**\n"
            for n in relevant[:3]:
                titulo = n['titulo'][:50] + "..." if len(n['titulo']) > 50 else n['titulo']
                
                # Emoji según sentimiento
                emoji_sent = {
                    'Positivo': '😊',
                    'Negativo': '😞',
                    'Neutral': '😐'
                }.get(n.get('sentimiento', 'Neutral'), '😐')
                
                sentimiento_info = f"{emoji_sent} {n.get('sentimiento', 'Neutral')}"
                nivel = n.get('nivel_sentimiento', '')
                if nivel:
                    sentimiento_info += f" ({nivel})"
                
                sources += f"• [{titulo}]({n['url']}) - {sentimiento_info}\n"
            
            return response + sources
            
        except Exception as e:
            print(f"❌ Error procesando pregunta: {e}")
            return f"❌ Error al procesar la pregunta: {str(e)}"


# Instancia global del bot
bot = NewsChatBot()