# ================================================================================
# app.py - SERVIDOR PRINCIPAL CON CONTROL GROQ (CORREGIDO)
# ================================================================================

from flask import Flask, jsonify, request, render_template_string
from config import DATA_STORE
from chatbot import bot
from templates import HTML_TEMPLATE
import threading
from telegram_bot import start_telegram_bot

app = Flask(__name__)
app.secret_key = 'newsbot-2024-secret'
app.config['JSON_AS_ASCII'] = False

# ================================================================================
# RUTAS
# ================================================================================

@app.route('/')
def home():
    """Página principal"""
    return render_template_string(
        HTML_TEMPLATE,
        headlines=DATA_STORE.get('titulares', [])[:20 ],
        total=len(DATA_STORE.get('titulares', [])),
        groq_enabled=bot.brain.enabled if bot.brain else False,
        groq_available=bot.brain.client is not None if bot.brain else False,
        initialized=bot.initialized
    )

@app.route('/api/chat', methods=['POST'])
def chat():
    """API para procesar preguntas"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'answer': 'Error: No se recibieron datos'})
        
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'answer': 'Por favor, escribe una pregunta.'})
        
        # Procesar pregunta
        answer = bot.answer(question)
        
        return jsonify({'answer': answer})
    
    except Exception as e:
        print(f"❌ Error en /api/chat: {e}")
        return jsonify({'answer': f'Error interno: {str(e)}'})

@app.route('/api/status')
def status():
    """Estado del sistema"""
    return jsonify({
        'initialized': bot.initialized,
        'initializing': bot.initializing,
        'news_count': len(DATA_STORE.get('titulares', [])),
        'news_analyzed': DATA_STORE.get('noticias_analizadas', 0),
        'current_action': DATA_STORE.get('current_action', 'Iniciando...'),
        'progress': DATA_STORE.get('progress', 0),
        'groq_enabled': bot.brain.enabled if bot.brain else False,
        'groq_available': bot.brain.client is not None if bot.brain else False
    })

@app.route('/api/headlines')
def get_headlines():
    """Obtener titulares actuales"""
    headlines = DATA_STORE.get('titulares', [])
    # Devolvemos solo títulos para aligerar la carga
    return jsonify({
        'headlines': [{'titulo': h['titulo']} for h in headlines]
    })

# RUTA CORREGIDA: Toggle Groq
@app.route('/api/toggle-groq', methods=['POST'])
def toggle_groq():
    """Activar/desactivar Groq AI"""
    try:
        # Verificar que el bot esté inicializado
        if not bot.brain:
            return jsonify({
                'success': False,
                'enabled': False,
                'message': '⏳ El bot aún se está inicializando. Espera unos segundos...'
            }), 400
        
        # Verificar que Groq esté configurado
        if not bot.brain.client:
            return jsonify({
                'success': False,
                'enabled': False,
                'message': '❌ Groq no está configurado. Necesitas una API key válida en config.py'
            }), 400
        
        # Cambiar estado
        bot.brain.enabled = not bot.brain.enabled
        
        print(f"🔄 Groq {'ACTIVADO' if bot.brain.enabled else 'DESACTIVADO'}")
        
        return jsonify({
            'success': True,
            'enabled': bot.brain.enabled,
            'message': f"✅ Groq {'activado' if bot.brain.enabled else 'desactivado'}"
        })
    
    except Exception as e:
        print(f"❌ Error en toggle-groq: {e}")
        return jsonify({
            'success': False,
            'enabled': False,
            'message': f'❌ Error: {str(e)}'
        }), 500

@app.route('/api/refresh', methods=['POST'])
def refresh():
    """Recargar noticias"""
    bot.initialize_async()
    return jsonify({'status': 'ok', 'message': 'Recargando noticias...'})

# ================================================================================
# PUNTO DE ENTRADA
# ================================================================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║        🇧🇴 EL DEBER NEWS BOT                                   ║
    ║        Flask + Embeddings + Groq AI                            ║
    ║        NUEVA FUNCIÓN: Toggle Groq On/Off 🤖                    ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("🔄 Iniciando carga del bot en segundo plano...")
    print("   El servidor estará disponible inmediatamente.")
    print("   Las noticias se cargarán mientras usas el chat.\n")
    
    bot.initialize_async()
    # Iniciar bot de Telegram como proceso independiente
    import subprocess, sys
    subprocess.Popen([sys.executable, "telegram_bot.py"])

    print("=" * 60)
    print("🌐 SERVIDOR INICIADO")
    print("=" * 60)
    print("   📍 URL: http://localhost:5000")
    print("   🤖 Groq: Click en el botón para activar/desactivar")
    print("   🛑 Presiona Ctrl+C para detener")
    print("=" * 60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )