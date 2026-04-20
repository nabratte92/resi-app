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

st.set_page_config(page_title="ReSI - San Isidro", layout="centered")

# --- 2. ENCABEZADO ---
try:
    st.image("logo_resi.png", use_container_width=True)
except:
    st.header("ReSI - Realidad San Isidro")

# --- 3. LÓGICA DEL FORMULARIO ---
if st.button("🚨 INICIAR REPORTE", type="primary", use_container_width=True):
    st.session_state.mostrar_form = True

if st.session_state.get('mostrar_form', False):
    with st.form("form_reporte"):
        nombre = st.text_input("Tu Nombre")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Otro"])
        descripcion = st.text_area("Breve descripción")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte"):
            if not foto or not nombre:
                st.error("Completá tu nombre y subí una foto.")
            else:
                try:
                    with st.spinner("Enviando reporte..."):
                        # A. Subir a ImgBB
                        img_api_key = st.secrets["IMGBB_API_KEY"]
                        files = {"image": foto.getvalue()}
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={img_api_key}", files=files)
                        url_foto = res.json()["data"]["url"]

                        # B. Guardar en Google Sheet
                        scopes = ['https://www.googleapis.com/auth/spreadsheets']
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=scopes)
                        client = gspread.authorize(creds)
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        
                        nueva_fila = [datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, "N/A", "N/A", tag, descripcion, url_foto, -34.4746, -58.5132, "Pendiente"]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte enviado con éxito!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                except Exception as e:
                    st.error(f"Error técnico: {e}")

# --- 4. MAPA ---
st.write("### Mapa de Reportes")
m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
try:
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    data = pd.DataFrame(gspread.authorize(creds_map).open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    for _, r in data.iterrows():
        folium.Marker([r['lat'], r['lon']], popup=r['Tag']).add_to(m)
except: pass
st_folium(m, width="100%", height=400)