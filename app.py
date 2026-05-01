import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN GITHUB (COMPLETÁ ESTO) ---
USUARIO_GH = "nabratte92"  # Poné tu nombre de usuario de GitHub
REPO_GH = "resi-app"        # Poné el nombre de tu repositorio

# --- URLS DE RECURSOS ---
URL_BASE = f"https://raw.githubusercontent.com/{USUARIO_GH}/{REPO_GH}/main"
IMG_LOGO_WALLY = f"{URL_BASE}/Logo%20buscando%20ramon.png"
IMG_MAPA_WALLY = f"{URL_BASE}/Mapa%20buscando%20ramon.png"
IMG_AVATAR = f"{URL_BASE}/Avatar%20buscando%20ramon.png"
AUDIO_RISA = f"{URL_BASE}/Risa%20buscando%20ramon.mp3"

# --- 2. CONEXIÓN A SUPABASE ---
SUPABASE_URL = 'https://iknwswwouxledkavyrwf.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlrbndzd3dvdXhsZWRrYXZ5cndmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2MDE4MTgsImV4cCI6MjA5MzE3NzgxOH0.CnHWCK78FGRASgnRX3dLI6r1Pw0rCEtJhfccCvHTqRI'
ADMIN_PASSWORD = 'resi_admin_2026'

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 3. CATEGORÍAS Y GRAVEDAD ---
CATS_ROJAS = ["Poste en riesgo de caída", "Hecho de inseguridad", "Riesgo de derrumbe", "Árbol caído", "Abuso de autoridad", "Plagas", "Fuga de gas", "Microbasural clandestino"]
CATS_NARANJAS = ["Contenedor desbordado", "Corte de luz", "Cloaca colapsada", "Zanja tapada", "Pérdida de agua", "Corte de agua", "Parada/Refugio vandalizado"]
CATS_AMARILLAS = ["Bache", "Vereda rota", "Luminaria con problemas", "Auto mal estacionado", "Falta rampa", "Poda mal hecha", "Problemas de tránsito", "Obra mal hecha", "Mobiliario urbano dañado", "Otros"]

todas_las_categorias = CATS_ROJAS + CATS_NARANJAS + CATS_AMARILLAS
todas_las_categorias.remove("Bache")
todas_las_categorias.remove("Otros")
LISTA_CATEGORIAS = ["Bache"] + sorted(todas_las_categorias) + ["Otros"]

st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="centered")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-size: 22px;
        font-weight: bold;
        padding: 15px; border-radius: 10px; border: none;
        display: block; margin: 0 auto;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    .slogan {
        text-align: center; font-size: 19px; font-style: italic;
        color: #444; margin-top: -15px; margin-bottom: 10px;
    }
    .synthetic-list {
        text-align: center; font-size: 14px; color: #666; margin-bottom: 25px;
    }
    .comunidad-box {
        text-align: center; background-color: #e9ecef; padding: 30px; 
        border-radius: 15px; margin-top: 40px; border: 2px dashed #28a745;
    }
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False
if 'mostrar_comunidad' not in st.session_state: st.session_state.mostrar_comunidad = False

# --- 4. BARRA LATERAL (ADMIN) ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password")
    es_admin = (pwd_input == ADMIN_PASSWORD)

# --- 5. CABECERA Y BOTÓN REPORTE ---
col_izq, col_centro, col_der = st.columns([1, 35, 1])
with col_centro:
    try: st.image("logo_resi.png", use_container_width=True)
    except: st.header("ReSI - Realidad San Isidro")
    st.markdown('<p class="slogan">Una herramienta para que el intendente y sus funcionarios se ubiquen en el mapa</p>', unsafe_allow_html=True)
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True
    st.markdown('<p class="synthetic-list">Podés reportar problemas de: baches, veredas, luminarias, seguridad, higiene urbana, arbolado, tránsito y accesibilidad.</p>', unsafe_allow_html=True)

# (Lógica de Formulario, Video, Mapa de Reportes y Novedades igual a la V31...)
# [Se asume que mantenés el código intermedio de la V31 aquí]

# --- 12. SECCIÓN INTERACTIVA: BUSCANDO A RAMÓN ---
st.divider()

# Inyectamos el minijuego
codigo_minijuego = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    .contenedor-juego {{
        position: relative;
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
        border: 5px solid #28a745;
        border-radius: 15px;
        overflow: hidden;
        background-color: #fff;
    }}
    .logo-wally {{
        width: 100%;
        display: block;
        border-bottom: 3px solid #28a745;
    }}
    .mapa-fondo {{
        width: 100%;
        display: block;
    }}
    #ramon-avatar {{
        position: absolute;
        top: 72%; /* AJUSTÁ ESTO PARA ESCONDERLO */
        left: 15%; /* AJUSTÁ ESTO PARA ESCONDERLO */
        width: 22px;
        cursor: pointer;
        z-index: 10;
        filter: brightness(0.9); /* Para que se camufle un poco más */
    }}
</style>
</head>
<body>

<div class="contenedor-juego">
    <img src="{IMG_LOGO_WALLY}" class="logo-wally">
    
    <div style="position: relative;">
        <img src="{IMG_MAPA_WALLY}" class="mapa-fondo">
        <img id="ramon-avatar" src="{IMG_AVATAR}" onclick="reir()">
    </div>
    
    <audio id="sonido-risa" src="{AUDIO_RISA}"></audio>
</div>

<script>
    function reir() {{
        var audio = document.getElementById("sonido-risa");
        audio.play();
        
        // Pequeño efecto visual al encontrarlo
        var avatar = document.getElementById("ramon-avatar");
        avatar.style.width = "60px";
        avatar.style.filter = "brightness(1.2)";
        avatar.style.transition = "all 0.3s ease";
    }}
</script>

</body>
</html>
"""

components.html(codigo_minijuego, height=650)

# --- 13. SECCIÓN COMUNIDAD ---
st.markdown("""
    <div class="comunidad-box">
        <h3 style="color: #28a745; margin-bottom: 10px;">SUMATE A LA COMUNIDAD ReSI</h3>
        <p style="font-size: 16px; color: #444;">PARA RECIBIR INFORMACIÓN IMPORTANTE PARA QUE RESCATEMOS SAN ISIDRO</p>
    </div>
""", unsafe_allow_html=True)
# [Resto del código de comunidad y Admin...]
