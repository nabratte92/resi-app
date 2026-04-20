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

# --- 2. ESTILOS CSS (BOTÓN VERDE Y DISEÑO) ---
st.markdown("""
    <style>
    /* Forzar botón verde */
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
    div.stButton > button:hover {
        background-color: #218838 !important;
        color: white !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ENCABEZADO ---
try:
    st.image("logo_resi.png", use_container_width=True)
except:
    st.header("ReSI - Realidad San Isidro")

# --- 4. LÓGICA DEL FORMULARIO ---
if st.button("🚨 INICIAR REPORTE"):
    st.session_state.mostrar_form = True

if st.session_state.get('mostrar_form', False):
    with st.form("form_reporte", clear_on_submit=True):
        st.write("### Datos del Nuevo Reporte")
        nombre = st.text_input("Nombre (Obligatorio)")
        email = st.text_input("Email (Opcional)")
        tel = st.text_input("Teléfono (Opcional)")
        ubicacion_manual = st.text_input("Dirección o Referencia (Ej: Av. Centenario 100)")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        descripcion = st.text_area("Descripción de la situación")
        foto = st.file_uploader("Subir Foto (Obligatorio)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte a ReSI"):
            if not foto or not nombre:
                st.error("Por favor, ingresá al menos tu nombre y la foto.")
            else:
                try:
                    with st.spinner("Subiendo reporte..."):
                        # A. Subir a ImgBB
                        img_api_key = st.secrets["IMGBB_API_KEY"]
                        files = {"image": foto.getvalue()}
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={img_api_key}", files=files)
                        url_foto = res.json()["data"]["url"]

                        # B. Guardar en Google Sheet
                        scopes = ['https://www.googleapis.com/auth/spreadsheets']
                        json_creds = json.loads(st.secrets["GCP_CREDS"])
                        creds = Credentials.from_service_account_info(json_creds, scopes=scopes)
                        client = gspread.authorize(creds)
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        
                        # Datos a guardar (Lat/Lon fijos por ahora para que aparezcan en el mapa)
                        nueva_fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), 
                            nombre, 
                            email if email else "No provisto", 
                            tel if tel else "No provisto", 
                            tag, 
                            f"{ubicacion_manual} - {descripcion}", 
                            url_foto, 
                            -34.4746, # Latitud base San Isidro
                            -58.5132, # Longitud base San Isidro
                            "Pendiente"
                        ]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte enviado con éxito!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error técnico: {e}")

# --- 5. MAPA DE SITUACIÓN ---
st.divider()
st.write("### Mapa de Realidad Distrital")

# Coordenadas base (San Isidro)
m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    json_creds_map = json.loads(st.secrets["GCP_CREDS"])
    creds_map = Credentials.from_service_account_info(json_creds_map, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client_map = gspread.authorize(creds_map)
    sheet_data = client_map.open_by_key(SPREADSHEET_ID).sheet1.get_all_records()
    data = pd.DataFrame(sheet_data)
    
    if not data.empty:
        for _, r in data.iterrows():
            # Crear el ícono verde con la letra 'R'
            icon_r = folium.DivIcon(html=f"""
                <div style="
                    background-color: #28a745; 
                    color: white; 
                    border-radius: 50%; 
                    width: 30px; 
                    height: 30px; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    font-weight: bold; 
                    border: 2px solid white;
                    box-shadow: 0px 0px 5px rgba(0,0,0,0.5);
                ">R</div>
            """)
            # Usamos las coordenadas de la planilla
            folium.Marker(
                location=[float(r['lat']), float(r['lon'])], 
                popup=f"<b>{r['Tag']}</b><br>{r['Estado']}", 
                icon=icon_r
            ).add_to(m)
except Exception as e:
    st.warning("El mapa se está actualizando o la planilla está vacía.")

st_folium(m, width="100%", height=450)
