# El Deber Bot - Chatbot de noticias de El Deber (Bolivia)

Proyecto universitario para crear un chatbot que responde preguntas sobre noticias recientes de [eldeber.com.bo](https://eldeber.com.bo), usando RAG + Groq (Llama3).

## 🚀 Cómo ponerlo en marcha (pasos exactos)

1. Clonar el repositorio
```bash
git clone git@github.com:Zinko5/chatbot.git
cd chatbot
```

2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate    # En Windows: venv\Scripts\activate
```

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

4. Crear tu archivo .env (importante)
```bash
cp .env.example .env
```

Luego abre `.env` y pega tu propia API key de Groq y el token de Telegram.

5. Ejecutar el bot
```bash
python3 app.py
```

6. Abrir en el navegador: http://127.0.0.1:5000

## 🤖 Cómo ejecutar el Bot de Telegram

1. Asegúrate de haber configurado el `TELEGRAM_BOT_TOKEN` en tu archivo `.env`.
   - Puedes obtener un token creando un bot con [@BotFather](https://t.me/BotFather) en Telegram.

2. Ejecutar el script del bot:
```bash
python telegram_bot.py
```

3. Busca tu bot en Telegram y presiona "Iniciar" (o envía `/start`). ¡Ya puedes chatear con él!
