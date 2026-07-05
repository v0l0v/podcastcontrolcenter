
import streamlit as st
import json
import os
import datetime
import glob

CONFIG_FILE = 'podcast_config.json'

def inject_pcc_style():
    """Inyecta el CSS personalizado de Micomicona en la página actual."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Cinzel:wght@500;700&display=swap');
    
    :root {
        --bg:        #F4F6F0; /* Crema sabio claro y limpio */
        --surface:   #FFFFFF; /* Superficie en blanco puro para alto contraste */
        --border:    rgba(18, 24, 16, 0.12); /* Borde suave de alta visibilidad */
        --border-focus: #8E701D; /* Borde dorado antiguo */
        --gold:      #8E701D; /* Dorado antiguo con excelente contraste */
        --gold-light:#FAF3DC; /* Dorado muy suave para fondos */
        --text:      #121810; /* Texto oscuro verde bosque profundo (máxima legibilidad) */
        --muted:     #52604F; /* Texto silenciado de alta visibilidad */
        --sidebar-bg: #EAECE6; /* Fondo de la barra lateral ligeramente gris sabio */
    }
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: var(--text);
    }
    
    h1, h2, h3, .pcc-page-title {
        font-family: 'Cinzel', serif !important;
        color: var(--gold) !important;
        letter-spacing: 0.05em;
    }
    
    .stApp { background-color: var(--bg); }
    [data-testid="stSidebar"] { 
        background-color: var(--sidebar-bg) !important; 
        border-right: 1px solid var(--border); 
    }
    
    /* Buttons */
    .stButton > button { 
        border-radius: 8px; 
        font-weight: 600; 
        border: 1px solid var(--gold); 
        background-color: var(--surface) !important;
        color: var(--gold) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        padding: 0.5rem 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton > button:hover {
        background-color: var(--gold) !important;
        color: var(--surface) !important;
        box-shadow: 0 4px 12px rgba(142, 112, 29, 0.2);
        transform: translateY(-2px);
    }
    .stButton > button[kind="primary"] { 
        background-color: var(--gold) !important; 
        color: var(--surface) !important; 
    }
    .stButton > button[kind="primary"]:hover { 
        background-color: #705814 !important; 
        color: var(--surface) !important; 
        box-shadow: 0 4px 15px rgba(142, 112, 29, 0.35);
    }
    
    /* Cards */
    .pcc-card { 
        background: linear-gradient(135deg, var(--surface) 0%, #FAFBF8 100%); 
        border: 1px solid var(--border); 
        border-radius: 12px; 
        padding: 20px 24px; 
        margin-bottom: 16px; 
        box-shadow: 0 4px 15px rgba(18,24,16,0.04);
        transition: all 0.3s ease;
    }
    .pcc-card:hover {
        border-color: rgba(142, 112, 29, 0.4);
        box-shadow: 0 8px 24px rgba(18,24,16,0.08), 0 0 12px rgba(142, 112, 29, 0.08);
        transform: translateY(-4px);
    }
    .pcc-card-title { 
        font-size: 0.8rem; 
        font-weight: 600; 
        text-transform: uppercase; 
        color: var(--muted); 
        letter-spacing: 0.1em;
        margin-bottom: 6px;
    }
    .pcc-card-value { 
        font-size: 1.4rem; 
        font-weight: 700; 
        color: var(--gold); 
        font-family: 'Cinzel', serif;
    }
    
    .pcc-page-title { 
        font-size: 1.8rem; 
        font-weight: 700; 
        color: var(--gold); 
        margin-bottom: 24px; 
        border-bottom: 2px solid var(--gold);
        padding-bottom: 10px;
    }
    .pcc-section-title { 
        font-size: 1.15rem; 
        font-weight: 700; 
        color: var(--gold); 
        margin: 24px 0 16px; 
        padding-bottom: 8px; 
        border-bottom: 1px solid var(--border); 
        font-family: 'Outfit', sans-serif;
    }

    /* Inputs Overrides */
    .stTextInput > div > div > input, .stTextArea > div > textarea, .stSelectbox > div > div {
        background-color: var(--surface) !important; 
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > textarea:focus, .stSelectbox > div > div:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 10px rgba(142, 112, 29, 0.1) !important;
    }
    
    /* Additional custom elements for a premium feeling */
    div[data-testid="stExpander"] {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    .stProgress > div > div > div > div {
        background-color: var(--gold) !important;
    }
    
    /* Custom divider */
    hr {
        border-color: var(--border) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def init_session_state():
    for key, val in {
        'config_check': False,
        'news_confirmed': False,
        'window_hours_override': None,
        'noticias_editadas_finales': [],
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val

import base64
import streamlit.components.v1 as components

def render_wavesurfer_player(audio_path: str, key: str = None):
    """Renderiza un reproductor interactivo con espectro visual de onda usando wavesurfer.js"""
    if not os.path.exists(audio_path):
        st.warning(f"Archivo de audio no encontrado: {audio_path}")
        return
        
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        audio_data_url = f"data:audio/mp3;base64,{b64_audio}"
        
        # ID limpio sin caracteres especiales
        safe_key = key if key else os.path.basename(audio_path).replace('.', '_').replace('-', '_').replace(' ', '_')
        element_id = f"wavesurfer_{safe_key}"
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Outfit', sans-serif;
                    overflow: hidden;
                }}
                .player-container {{
                    background: #ffffff;
                    border: 1px solid rgba(142, 112, 29, 0.25);
                    border-radius: 12px;
                    padding: 14px 18px;
                    box-sizing: border-box;
                    color: #121810;
                    box-shadow: 0 4px 12px rgba(18,24,16,0.03);
                }}
                .header {{
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    margin-bottom: 12px;
                }}
                .play-btn {{
                    background: #8E701D;
                    border: none;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 10px rgba(142, 112, 29, 0.25);
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    flex-shrink: 0;
                }}
                .play-btn:hover {{
                    background: #705814;
                    transform: scale(1.08);
                    box-shadow: 0 4px 15px rgba(142, 112, 29, 0.4);
                }}
                .play-btn:active {{
                    transform: scale(0.95);
                }}
                .info {{
                    flex-grow: 1;
                    min-width: 0;
                }}
                .title {{
                    font-size: 0.85rem;
                    font-weight: 600;
                    color: #8E701D;
                    margin-bottom: 3px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    letter-spacing: 0.02em;
                }}
                .time-container {{
                    font-size: 0.72rem;
                    color: #52604F;
                    font-weight: 400;
                }}
                #waveform_{element_id} {{
                    width: 100%;
                    cursor: pointer;
                    margin-top: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="player-container">
                <div class="header">
                    <button class="play-btn" id="btn_{element_id}">
                        <svg id="icon_{element_id}" viewBox="0 0 24 24" width="18" height="18" fill="#ffffff" style="margin-left: 2px;">
                            <path id="path_{element_id}" d="M8 5v14l11-7z"/>
                        </svg>
                    </button>
                    <div class="info">
                        <div class="title">{os.path.basename(audio_path)}</div>
                        <div class="time-container">
                            <span id="time_{element_id}">00:00</span> / <span id="duration_{element_id}">--:--</span>
                        </div>
                    </div>
                </div>
                <div id="waveform_{element_id}"></div>
            </div>
            
            <script src="https://unpkg.com/wavesurfer.js@7.7.15/dist/wavesurfer.min.js"></script>
            <script>
                const ws = WaveSurfer.create({{
                    container: '#waveform_{element_id}',
                    waveColor: 'rgba(142, 112, 29, 0.15)',
                    progressColor: '#8E701D',
                    cursorColor: '#52604F',
                    cursorWidth: 2,
                    barWidth: 2,
                    barGap: 2,
                    barRadius: 2,
                    height: 50,
                    responsive: true,
                    backend: 'WebAudio'
                }});
                
                ws.load("{audio_data_url}");
                
                const btn = document.getElementById("btn_{element_id}");
                const iconPath = document.getElementById("path_{element_id}");
                const svgEl = document.getElementById("icon_{element_id}");
                const timeEl = document.getElementById("time_{element_id}");
                const durEl = document.getElementById("duration_{element_id}");
                
                btn.addEventListener("click", () => {{
                    ws.playPause();
                }});
                
                ws.on("play", () => {{
                    // Icono de Pausa
                    iconPath.setAttribute("d", "M6 19h4V5H6v14zm8-14v14h4V5h-4z");
                    svgEl.style.marginLeft = "0px";
                }});
                
                ws.on("pause", () => {{
                    // Icono de Play
                    iconPath.setAttribute("d", "M8 5v14l11-7z");
                    svgEl.style.marginLeft = "2px";
                }});
                
                const formatTime = (secs) => {{
                    const m = Math.floor(secs / 60).toString().padStart(2, '0');
                    const s = Math.floor(secs % 60).toString().padStart(2, '0');
                    return m + ":" + s;
                }};
                
                ws.on("audioprocess", () => {{
                    timeEl.textContent = formatTime(ws.getCurrentTime());
                }});
                
                ws.on("ready", () => {{
                    durEl.textContent = formatTime(ws.getDuration());
                }});
                
                ws.on("seeking", () => {{
                    timeEl.textContent = formatTime(ws.getCurrentTime());
                }});
                
                // Forzar redimensionamiento en iframe de Streamlit
                window.addEventListener('resize', () => {{
                    ws.drawBuffer();
                }});
            </script>
        </body>
        </html>
        """
        
        components.html(html_code, height=140)
    except Exception as e:
        st.error(f"Error cargando reproductor de forma de onda: {e}")
        st.audio(audio_path)
