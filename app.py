import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime
import json

# --- 1. CONFIGURACIÓN ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'

st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="centered")

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
        font-size: 20px;
        font-weight: bold;
        padding: 15px;
        border-radius: 10px;
        border: none;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

# --- 3. ENCABEZADO ---
try:
    st.image("logo_resi.png", use_container_width=True)
except:
    st.header("ReSI - Realidad San Isidro")

# --- 4. BOTÓN DE CARGA ---
if st.button("🚨 INICIAR REPORTE"):
    st.session_state.mostrar_form = True

# --- 5. FORMULARIO DE REPORTE ---
if st.session_state.mostrar_form:
    st.write("### 📍 Ubicá el reporte en el mapa")
    m_sel = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    folium.Marker([st.session_state.lat_sel, st.session_state.lon_sel], icon=folium.Icon(color='red')).add_to(m_sel)
    
    out = st_folium(m_sel, width="100%", height=300, key="selector")
    if out and out.get("last_clicked"):
        st.session_state.lat_sel = out["last_clicked"]["lat"]
        st.session_state.lon_sel = out["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        nombre = st.text_input("Nombre (Obligatorio)")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        descripcion = st.text_area("Descripción")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte"):
            if not foto or not nombre:
                st.error("Completá nombre y foto.")
            else:
                try:
                    with st.spinner("Enviando..."):
                        # Foto a ImgBB
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]

                        # Sheets
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                        sheet = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
                        nueva_fila = [datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, "N/A", "N/A", tag, descripcion, url_foto, st.session_state.lat_sel, st.session_state.lon_sel, "Pendiente"]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte cargado!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# --- 6. MAPA PRINCIPAL (PÚBLICO) ---
st.divider()
st.write("### 🌎 Mapa de Realidad Distrital")

m_publico = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client = gspread.authorize(creds_map)
    # Forzamos la lectura limpia de los datos
    datos = client.open_by_key(SPREADSHEET_ID).sheet1.get_all_records()
    df = pd.DataFrame(datos)

    if not df.empty:
        for _, r in df.iterrows():
            # Limpieza y conversión de coordenadas
            try:
                lat, lon = float(r['lat']), float(r['lon'])
                
                # Ícono Verde con R
                icon_html = f"""
                <div style="background-color: #28a745; color: white; border-radius: 50%; width: 35px; height: 35px; 
                display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.3); font-family: sans-serif;">R</div>"""
                
                # Popup con miniatura
                popup_content = f"""
                <div style="width: 200px; font-family: sans-serif;">
                    <h4 style="margin:0; color:#28a745;">{r['Tag']}</h4>
                    <p style="margin:5px 0; font-size:12px;">{r['Descripcion']}</p>
                    <img src="{r['Foto']}" style="width:100%; border-radius:5px; margin-top:5px;">
                    <br><small>Estado: {r['Estado']}</small>
                </div>"""
                
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_content, max_width=250),
                    icon=folium.DivIcon(html=icon_html)
                ).add_to(m_publico)
            except: continue

except Exception as e:
    st.info("Cargando reportes...")

st_folium(m_publico, width="100%", height=500, key="mapa_principal")
