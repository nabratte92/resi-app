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
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicializar estados de sesión para coordenadas
if 'lat_sel' not in st.session_state:
    st.session_state.lat_sel = -34.4746 # Centro de San Isidro por defecto
if 'lon_sel' not in st.session_state:
    st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state:
    st.session_state.mostrar_form = False

# --- 3. ENCABEZADO ---
try:
    st.image("logo_resi.png", use_container_width=True)
except:
    st.header("ReSI - Realidad San Isidro")

# --- 4. BOTÓN DE CARGA ---
if st.button("🚨 INICIAR REPORTE"):
    st.session_state.mostrar_form = True

# --- 5. LÓGICA DEL FORMULARIO CON MAPA INTERACTIVO ---
if st.session_state.mostrar_form:
    st.write("### 📍 Paso 1: Tocá el mapa para ubicar el reporte")
    
    # Mapa para capturar el click
    m_selector = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    # Mostramos un marcador temporal donde el usuario hizo click
    folium.Marker(
        [st.session_state.lat_sel, st.session_state.lon_sel], 
        tooltip="Punto del reporte",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m_selector)
    
    # Capturamos el evento de click
    output = st_folium(m_selector, width="100%", height=300, key="selector_map")
    
    if output and output.get("last_clicked"):
        st.session_state.lat_sel = output["last_clicked"]["lat"]
        st.session_state.lon_sel = output["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        st.write("### 📝 Paso 2: Completá los datos")
        st.info(f"Ubicación seleccionada: {st.session_state.lat_sel:.5f}, {st.session_state.lon_sel:.5f}")
        
        nombre = st.text_input("Nombre (Obligatorio)")
        email = st.text_input("Email (Opcional)")
        tel = st.text_input("Teléfono (Opcional)")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        descripcion = st.text_area("Descripción de la situación")
        foto = st.file_uploader("Subir Foto (Obligatorio)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte"):
            if not foto or not nombre:
                st.error("Por favor, ingresá tu nombre y subí una foto.")
            else:
                try:
                    with st.spinner("Procesando reporte..."):
                        # A. Subir a ImgBB
                        img_key = st.secrets["IMGBB_API_KEY"]
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={img_key}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]

                        # B. Conectar a Google Sheets
                        scopes = ['https://www.googleapis.com/auth/spreadsheets']
                        json_creds = json.loads(st.secrets["GCP_CREDS"])
                        creds = Credentials.from_service_account_info(json_creds, scopes=scopes)
                        client = gspread.authorize(creds)
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        
                        # Guardar los datos exactos del click
                        nueva_fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), 
                            nombre, email if email else "N/A", tel if tel else "N/A", 
                            tag, descripcion, url_foto, 
                            st.session_state.lat_sel, st.session_state.lon_sel, "Pendiente"
                        ]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte geolocalizado con éxito!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al enviar: {e}")

# --- 6. MAPA GENERAL DE REPORTES ---
st.divider()
st.write("### Mapa de Realidad Distrital")
m_gral = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    json_creds_map = json.loads(st.secrets["GCP_CREDS"])
    creds_map = Credentials.from_service_account_info(json_creds_map, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client_map = gspread.authorize(creds_map)
    data = pd.DataFrame(client_map.open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    
    if not data.empty:
        for _, r in data.iterrows():
            # Ícono verde con la letra R blanca
            icon_r = folium.DivIcon(html=f"""
                <div style="
                    background-color: #28a745; color: white; border-radius: 50%; width: 30px; height: 30px; 
                    display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;
                    box-shadow: 0px 0px 5px rgba(0,0,0,0.3);
                ">R</div>
            """)
            folium.Marker(
                [float(r['lat']), float(r['lon'])], 
                popup=f"<b>{r['Tag']}</b><br>{r['Estado']}", 
                icon=icon_r
            ).add_to(m_gral)
except:
    pass

st_folium(m_gral, width="100%", height=450, key="map_principal")
