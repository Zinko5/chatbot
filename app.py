# ================================================================================
# app.py - SERVIDOR PRINCIPAL CON CONTROL GROQ (CORREGIDO)
# ================================================================================

from flask import Flask, jsonify, request, render_template_string, send_file
from config import DATA_STORE
from chatbot import bot
from templates import HTML_TEMPLATE
import threading
from telegram_bot import start_telegram_bot
from gtts import gTTS
import edge_tts
import speech_recognition as sr
from pydub import AudioSegment
import io
import os
import uuid
import hashlib
import asyncio
import atexit
import signal
import sys
import subprocess

app = Flask(__name__)
app.secret_key = 'newsbot-2024-secret'
app.config['JSON_AS_ASCII'] = False

# ================================================================================
# RUTAS
# ================================================================================

from weather import get_bolivia_weather

@app.route('/')
def home():
    """Página principal"""
    # Obtener clima actualizado
    weather = get_bolivia_weather()
    if weather:
        DATA_STORE['weather'] = weather
        
    return render_template_string(
        HTML_TEMPLATE,
        headlines=DATA_STORE.get('titulares', [])[:20 ],
        total=len(DATA_STORE.get('titulares', [])),
        groq_enabled=bot.brain.enabled if bot.brain else False,
        groq_available=bot.brain.client is not None if bot.brain else False,
        initialized=bot.initialized,
        weather=weather
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
        
        # Obtener ID de sesión (para mantener conversación)
        session_id = request.headers.get('X-Session-ID') or request.remote_addr or 'default'
        
        # Procesar pregunta
        answer = bot.answer(question, session_id=str(session_id))
        
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

@app.route('/api/tts', methods=['POST'])
def tts():
    """Texto a voz (Optimizado con Edge TTS + Caché)"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # 1. Verificar Caché
        # Creamos un hash del texto para usarlo como nombre de archivo
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_dir = 'audio_cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        filename = f"{cache_dir}/{text_hash}.mp3"
        
        # Si ya existe, lo devolvemos directamente (Instantáneo)
        if os.path.exists(filename):
            return send_file(filename, mimetype='audio/mp3')
            
        # 2. Generar con Edge TTS (Más rápido y natural)
        async def generate_audio():
            communicate = edge_tts.Communicate(text, "es-ES-AlvaroNeural")
            await communicate.save(filename)
            
        asyncio.run(generate_audio())
        
        return send_file(filename, mimetype='audio/mp3')
        
    except Exception as e:
        print(f"❌ Error en TTS: {e}")
        # Fallback a gTTS si falla Edge
        try:
            print("⚠️ Usando Fallback gTTS...")
            tts = gTTS(text=text, lang='es')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return send_file(mp3_fp, mimetype='audio/mp3', download_name='response.mp3')
        except Exception as e2:
            return jsonify({'error': str(e2)}), 500

@app.route('/api/stt', methods=['POST'])
def stt():
    """Voz a texto"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        
        # Guardar temporalmente
        filename = f"temp_{uuid.uuid4()}.webm" # Asumimos webm del navegador
        audio_file.save(filename)
        
        # Convertir a WAV para SpeechRecognition
        try:
            sound = AudioSegment.from_file(filename)
            wav_filename = filename.replace('.webm', '.wav')
            sound.export(wav_filename, format="wav")
            
            # Reconocer
            r = sr.Recognizer()
            with sr.AudioFile(wav_filename) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data, language='es-ES')
                
            # Limpiar
            os.remove(filename)
            os.remove(wav_filename)
            
            return jsonify({'text': text})
            
        except Exception as e:
            if os.path.exists(filename):
                os.remove(filename)
            if 'wav_filename' in locals() and os.path.exists(wav_filename):
                os.remove(wav_filename)
            raise e
            
    except Exception as e:
        print(f"❌ Error en STT: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather', methods=['POST'])
def update_weather():
    """Actualizar clima por ciudad"""
    try:
        data = request.get_json()
        city = data.get('city', 'Santa Cruz')
        print(f"📡 API Weather solicitada para: {city}")
        
        weather = get_bolivia_weather(city)
        if weather:
            DATA_STORE['weather'] = weather
            print(f"✅ Clima actualizado: {weather['city']} {weather['temp']}°C")
            return jsonify({'success': True, 'weather': weather})
        else:
            return jsonify({'success': False, 'message': 'No se pudo obtener el clima'}), 400
            
    except Exception as e:
        print(f"❌ Error actualizando clima: {e}")
        return jsonify({'error': str(e)}), 500

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
    # Iniciar bot de Telegram como proceso independiente con limpieza
    telegram_process = subprocess.Popen([sys.executable, "telegram_bot.py"])

    def cleanup():
        if telegram_process:
            print("\n🛑 Deteniendo bot de Telegram...")
            telegram_process.terminate()
            try:
                telegram_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                telegram_process.kill()
            print("✅ Bot de Telegram detenido.")

    atexit.register(cleanup)
    
    # Manejar Ctrl+C explícitamente para asegurar que atexit corra
    def signal_handler(sig, frame):
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)

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