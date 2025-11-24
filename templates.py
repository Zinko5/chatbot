# ================================================================================
# templates.py - MODERN UI WITH LOADING ANIMATIONS
# ================================================================================

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>El Deber News Bot AI 🇧🇴</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #ec4899;
            --bg-dark: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.7);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #22c55e;
            --warning: #eab308;
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(236, 72, 153, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(34, 197, 94, 0.1) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            height: 100vh; /* Fallback */
            height: 100dvh; /* Dynamic viewport height */
            overflow: hidden; /* Prevent body scroll */
        }

        /* --- LOADING OVERLAY --- */
        #loadingOverlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: opacity 0.5s ease;
        }
        
        #loadingOverlay.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .loader-content {
            text-align: center;
            max-width: 400px;
            padding: 20px;
        }

        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(99, 102, 241, 0.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s ease-in-out infinite;
            margin: 0 auto 20px;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .loading-text {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(to right, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .loading-subtext {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 20px;
        }

        .progress-container {
            background: rgba(255, 255, 255, 0.1);
            height: 6px;
            width: 100%;
            border-radius: 3px;
            overflow: hidden;
            position: relative;
        }

        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            width: 0%;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
        }

        .news-counter {
            margin-top: 15px;
            font-family: monospace;
            color: var(--success);
            font-size: 1.1rem;
        }

        /* --- MAIN LAYOUT --- */
        .app-container {
            max-width: 1600px;
            margin: 0 auto;
            height: 100%;
            display: grid;
            grid-template-columns: 280px 1fr 320px;
            grid-template-rows: 1fr; /* Force single row filling height */
            gap: 20px;
            padding: 20px;
            overflow: hidden;
        }

        /* --- SIDEBARS --- */
        .sidebar, .news-sidebar {
            display: flex;
            flex-direction: column;
            height: 100%;
            min-height: 0; /* Allow shrinking */
            overflow: hidden;
        }

        .glass-panel {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            height: 100%; /* Fill parent */
            overflow: hidden; /* Contain children */
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--glass-border);
            flex-shrink: 0;
        }

        .brand-icon {
            font-size: 2rem;
            filter: drop-shadow(0 0 10px rgba(236, 72, 153, 0.5));
        }

        .brand-text h1 {
            font-size: 1.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text p {
            font-size: 0.75rem;
            color: var(--text-muted);
            letter-spacing: 1px;
        }

        .stats {
            flex-shrink: 0;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            font-size: 0.9rem;
        }

        .stat-label { color: var(--text-muted); display: flex; align-items: center; gap: 8px; }
        .stat-value { font-weight: 600; color: var(--text-main); }
        .stat-value.active { color: var(--success); text-shadow: 0 0 10px rgba(34, 197, 94, 0.4); }
        .stat-value.inactive { color: var(--warning); }

        .groq-control {
            margin-top: auto;
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 15px;
            flex-shrink: 0;
        }

        .toggle-btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--bg-dark), #1e293b);
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            font-weight: 600;
            border: 1px solid var(--glass-border);
        }

        .toggle-btn.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            border: none;
        }
        
        .toggle-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            filter: grayscale(1);
        }

        /* --- CHAT AREA --- */
        .chat-container {
            grid-column: 2;
            display: flex;
            flex-direction: column;
            height: 100%;
            min-height: 0;
            overflow: hidden;
        }

        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
            min-height: 0; /* Important for flex scrolling */
        }
        
        .messages-area::-webkit-scrollbar { width: 6px; }
        .messages-area::-webkit-scrollbar-track { background: transparent; }
        .messages-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }

        .msg {
            max-width: 85%;
            padding: 18px 24px;
            border-radius: 20px;
            line-height: 1.6;
            font-size: 0.95rem;
            position: relative;
            animation: messageSlide 0.3s ease-out;
            word-wrap: break-word;
        }

        @keyframes messageSlide {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .msg.user {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            color: white;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        }

        .msg.bot {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            border-bottom-left-radius: 4px;
            color: var(--text-main);
        }
        
        .msg.bot strong { color: var(--secondary); font-weight: 600; }
        .msg.bot a { color: #60a5fa; text-decoration: none; border-bottom: 1px dotted #60a5fa; transition: all 0.2s; }
        .msg.bot a:hover { color: #93c5fd; border-bottom-style: solid; }

        .input-area {
            padding: 20px;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(10px);
            border-top: 1px solid var(--glass-border);
            display: flex;
            gap: 15px;
            border-radius: 0 0 20px 20px;
            flex-shrink: 0;
        }

        #questionInput {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            padding: 16px 24px;
            border-radius: 30px;
            color: white;
            font-size: 1rem;
            font-family: inherit;
            transition: all 0.3s;
        }

        #questionInput:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        #sendBtn {
            width: 55px;
            height: 55px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, var(--success), #16a34a);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
            flex-shrink: 0;
        }

        #sendBtn:hover { transform: scale(1.1); box-shadow: 0 6px 16px rgba(34, 197, 94, 0.4); }
        #sendBtn:active { transform: scale(0.95); }
        #sendBtn svg { width: 24px; height: 24px; fill: currentColor; transform: translateX(2px); }

        /* --- RIGHT SIDEBAR (NEWS) --- */
        .news-list {
            list-style: none;
            overflow-y: auto;
            flex: 1;
            padding-right: 5px;
            min-height: 0;
        }

        .news-item {
            padding: 12px 15px;
            margin-bottom: 10px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .news-item:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--primary);
            color: white;
            transform: translateX(-5px);
        }

        .typing-indicator {
            display: flex;
            gap: 6px;
            padding: 10px;
        }
        .typing-dot {
            width: 8px; height: 8px;
            background: var(--text-muted);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

        /* Responsive */
        @media (max-width: 1200px) {
            .app-container { grid-template-columns: 240px 1fr; }
            .news-sidebar { display: none; }
        }
        @media (max-width: 768px) {
            .app-container { 
                grid-template-columns: 1fr; 
                grid-template-rows: 1fr;
                padding: 0;
                gap: 0;
            }
            .sidebar { display: none; }
            .glass-panel {
                border-radius: 0;
                border: none;
                background: transparent;
            }
            .input-area {
                border-radius: 0;
                padding: 15px;
            }
            .messages-area {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <!-- LOADING OVERLAY -->
    <div id="loadingOverlay" class="{{ 'hidden' if initialized else '' }}">
        <div class="loader-content">
            <div class="spinner"></div>
            <h2 class="loading-text">Inicializando IA</h2>
            <p class="loading-subtext">Analizando noticias y generando embeddings...</p>
            
            <div class="progress-container">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            
            <div class="news-counter">
                <span id="loadingCount">{{ total }}</span> noticias procesadas
            </div>
        </div>
    </div>

    <div class="app-container">
        <!-- LEFT SIDEBAR -->
        <aside class="sidebar">
            <div class="glass-panel" style="height: 100%;">
                <div class="brand">
                    <div class="brand-icon">🇧🇴</div>
                    <div class="brand-text">
                        <h1>El Deber Bot</h1>
                        <p>AI NEWS ASSISTANT</p>
                    </div>
                </div>

                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">📡 Estado</span>
                        <span class="stat-value active" id="botStatusText">En línea</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">📰 Noticias</span>
                        <span class="stat-value" id="totalNews">{{ total }}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">🧠 Modelo</span>
                        <span class="stat-value">MiniLM-L12</span>
                    </div>
                </div>

                <div style="flex:1"></div>

                <div class="groq-control">
                    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:10px;">MOTOR DE GENERACIÓN</p>
                    <button id="groqToggle" class="toggle-btn {{ 'active' if groq_enabled else '' }}" {{ 'disabled' if not groq_available else '' }}>
                        <span id="groqIcon">🤖</span>
                        <span id="groqText">{{ 'Groq AI: ACTIVADO' if groq_enabled else 'Groq AI: DESACTIVADO' }}</span>
                    </button>
                    <p style="font-size:0.7rem; color:var(--text-muted); margin-top:8px; text-align:center;">
                        {{ 'Potenciado por LLaMA 3' if groq_available else 'API Key no configurada' }}
                    </p>
                </div>
                
                <!-- SUGGESTIONS -->
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--glass-border);">
                    <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:10px;">SUGERENCIAS</p>
                    <div style="display:flex; flex-direction:column; gap:8px;">
                        <button class="news-item" onclick="askAbout('economía boliviana')" style="text-align:left; width:100%;">💰 ¿Cómo va la economía?</button>
                        <button class="news-item" onclick="askAbout('política actual')" style="text-align:left; width:100%;">🏛️ Resumen político</button>
                        <button class="news-item" onclick="askAbout('deportes')" style="text-align:left; width:100%;">⚽ Deportes destacados</button>
                    </div>
                </div>
            </div>
        </aside>

        <!-- CHAT AREA -->
        <main class="chat-container glass-panel">
            <div class="messages-area" id="messages">
                <div class="msg bot">
                    👋 <strong>¡Hola! Soy tu asistente de noticias.</strong><br><br>
                    He leído y analizado <strong>{{ total }} noticias</strong> de El Deber para responder tus preguntas.<br><br>
                    ✨ <em>Prueba preguntando:</em><br>
                    • "¿Qué pasó con el censo?"<br>
                    • "Noticias sobre economía"<br>
                    • "¿Qué dijo el presidente?"
                </div>
            </div>

            <div class="input-area">
                <input type="text" id="questionInput" placeholder="Escribe tu pregunta aquí..." autocomplete="off">
                <button id="sendBtn">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path></svg>
                </button>
            </div>
        </main>

        <!-- RIGHT SIDEBAR -->
        <aside class="news-sidebar glass-panel">
            <h3 style="margin-bottom:15px; font-size:1rem; color:var(--text-main);">🔥 Titulares Recientes</h3>
            <ul class="news-list" id="newsList">
                {% for h in headlines %}
                <li class="news-item" onclick="askAbout('{{ h.titulo|replace("'", "\\'") }}')">
                    {{ h.titulo }}
                </li>
                {% endfor %}
            </ul>
        </aside>
    </div>

    <script>
        // Variables de estado
        let isProcessing = false;
        let groqEnabled = {{ 'true' if groq_enabled else 'false' }};
        let initialized = {{ 'true' if initialized else 'false' }};
        let uiRefreshed = false;
        
        // Elementos DOM
        const els = {
            overlay: document.getElementById('loadingOverlay'),
            loadingCount: document.getElementById('loadingCount'),
            progressBar: document.getElementById('progressBar'),
            messages: document.getElementById('messages'),
            input: document.getElementById('questionInput'),
            btn: document.getElementById('sendBtn'),
            groqBtn: document.getElementById('groqToggle'),
            groqText: document.getElementById('groqText'),
            totalNews: document.getElementById('totalNews'),
            newsList: document.getElementById('newsList'),
            botStatusText: document.getElementById('botStatusText')
        };

        // --- FUNCIONES DE CHAT ---
        function scrollToBottom() {
            els.messages.scrollTop = els.messages.scrollHeight;
        }

        function addMessage(html, type) {
            const div = document.createElement('div');
            div.className = `msg ${type}`;
            div.innerHTML = html;
            els.messages.appendChild(div);
            scrollToBottom();
            return div;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'msg bot typing-indicator';
            div.id = 'typing';
            div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
            els.messages.appendChild(div);
            scrollToBottom();
            return div;
        }

        async function sendMessage() {
            const text = els.input.value.trim();
            if (!text || isProcessing) return;

            isProcessing = true;
            els.input.value = '';
            els.input.disabled = true;
            
            addMessage(text, 'user');
            const typing = showTyping();

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: text})
                });
                const data = await res.json();
                
                typing.remove();
                
                // Formatear respuesta (links y negritas)
                let formatted = data.answer
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
                
                addMessage(formatted, 'bot');

            } catch (e) {
                typing.remove();
                addMessage('❌ Error de conexión. Intenta de nuevo.', 'bot');
            } finally {
                isProcessing = false;
                els.input.disabled = false;
                els.input.focus();
            }
        }

        // --- EVENT LISTENERS ---
        els.btn.addEventListener('click', sendMessage);
        els.input.addEventListener('keydown', e => {
            if (e.key === 'Enter') sendMessage();
        });

        window.askAbout = function(title) {
            els.input.value = `¿Qué noticias hay sobre: ${title}?`;
            sendMessage();
        };

        // --- GROQ TOGGLE ---
        els.groqBtn.addEventListener('click', async () => {
            if (els.groqBtn.disabled) return;
            
            try {
                const res = await fetch('/api/toggle-groq', {method: 'POST'});
                const data = await res.json();
                
                if (data.success) {
                    groqEnabled = data.enabled;
                    updateGroqUI();
                }
            } catch (e) {
                console.error(e);
            }
        });

        function updateGroqUI() {
            if (groqEnabled) {
                els.groqBtn.classList.add('active');
                els.groqText.textContent = 'Groq AI: ACTIVADO';
            } else {
                els.groqBtn.classList.remove('active');
                els.groqText.textContent = 'Groq AI: DESACTIVADO';
            }
        }
        
        async function refreshHeadlines() {
            try {
                const res = await fetch('/api/headlines');
                const data = await res.json();
                
                els.newsList.innerHTML = '';
                data.headlines.forEach(h => {
                    const li = document.createElement('li');
                    li.className = 'news-item';
                    li.textContent = h.titulo;
                    li.onclick = () => askAbout(h.titulo.replace(/'/g, "\\'"));
                    els.newsList.appendChild(li);
                });
            } catch(e) {
                console.error("Error refreshing headlines:", e);
            }
        }

        // --- POLLING DE ESTADO Y CARGA ---
        const pollInterval = setInterval(async () => {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                // Actualizar contadores
                els.loadingCount.textContent = data.news_count;
                els.totalNews.textContent = data.news_count;
                
                // Actualizar texto de acción actual
                if (data.current_action) {
                    document.querySelector('.loading-subtext').textContent = data.current_action;
                }

                // Animación de barra de progreso real desde el backend
                if (!data.initialized) {
                    // Usar el progreso reportado por el backend
                    let progress = data.progress || 0;
                    // Asegurar que siempre se vea algo de progreso si hay noticias
                    if (progress < 5 && data.news_count > 0) progress = 5;
                    
                    els.progressBar.style.width = `${progress}%`;
                    els.botStatusText.textContent = "Cargando...";
                } else {
                    els.progressBar.style.width = '100%';
                    els.botStatusText.textContent = "En línea ✅";
                }

                // Manejar transición de carga
                if (data.initialized && !initialized) {
                    initialized = true;
                    setTimeout(() => {
                        els.overlay.classList.add('hidden');
                    }, 800);
                }
                
                // Refrescar UI una vez cuando termina de cargar
                if (data.initialized && !uiRefreshed) {
                    uiRefreshed = true;
                    refreshHeadlines();
                    
                    // Actualizar estado de Groq
                    groqEnabled = data.groq_enabled;
                    if (data.groq_available) {
                        els.groqBtn.disabled = false;
                        updateGroqUI();
                    }
                }

                // Sincronizar estado Groq si cambia externamente
                if (data.groq_enabled !== groqEnabled) {
                    groqEnabled = data.groq_enabled;
                    updateGroqUI();
                }

            } catch (e) {
                console.error('Polling error', e);
            }
        }, 1000);

    </script>
</body>
</html>
"""