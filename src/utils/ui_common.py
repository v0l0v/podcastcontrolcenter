
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --g-dark:    #1b5f00;
        --g-mid:     #cef89c;
        --g-light:   #e5fabd;
        --bg:        #e5fabd;
        --surface:   #cef89c;
        --border:    #cef89c;
        --text:      #1a1a1a;
        --muted:     #6b6b6b;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }
    
    .stApp { background-color: var(--bg); }
    [data-testid="stSidebar"] { background-color: var(--surface) !important; border-right: 1px solid var(--border); }
    
    .stButton > button { border-radius: 6px; font-weight: 600; border: 1px solid var(--border); transition: all 0.15s ease; }
    .stButton > button[kind="primary"] { background-color: var(--g-dark) !important; color: #fff !important; }
    
    .pcc-card { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px 20px; margin-bottom: 12px; }
    .pcc-card-title { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--muted); }
    .pcc-card-value { font-size: 1.1rem; font-weight: 700; color: var(--text); }
    
    .pcc-page-title { font-size: 1.6rem; font-weight: 700; color: var(--text); margin-bottom: 24px; }
    .pcc-section-title { font-size: 1rem; font-weight: 700; color: var(--text); margin: 20px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }

    /* Inputs Overrides */
    .stTextInput > div > div > input, .stTextArea > div > textarea, .stSelectbox > div > div {
        background-color: #f0fbd3 !important; border: 1px solid var(--g-dark) !important;
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
