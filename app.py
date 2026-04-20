import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime
import json

# --- 1. CONFIGURACIÓN (REEMPLAZÁ CON TUS IDs) ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
FOLDER_ID = '1q8KiQfMgKVr0wPFe1aEDo5I-8-A82D_C'
ADMIN_PASSWORD = 'resi_admin_2026'

# --- 2. DISEÑO Y ESTILOS ---
st.set_page_config(page_title="ReSI - San Isidro", layout="centered")

st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
        font-size: 22px;
        font-weight: bold;
        padding: 20px;
        border-radius: 10px;
        border: none;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ENCABEZADO (SOLO LOGO) ---
col_l, col_c, col_r = st.columns([1, 3, 1])
with col_c:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.subheader("ReSI - Realidad San Isidro")

# --- 4. BOTÓN DE CARGA ---
if st.button("🚨 INICIAR REPORTE", type="primary"):
    st.session_state.mostrar_form = True

# --- 5. LÓGICA DEL FORMULARIO ---
if st.session_state.get('mostrar_form', False):
    with st.form("form_reporte", clear_on_submit=True):
        st.write("### Nuevo Reporte")
        nombre = st.text_input("Nombre")
        email = st.text_input("Email")
        tel = st.text_input("Teléfono")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Otro"])
        descripcion = st.text_area("Descripción/Ubicación")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte"):
            if not foto or not nombre:
                st.error("Por favor completá los datos y subí una foto.")
            else:
                try:
                    with st.spinner("Guardando en la base de datos..."):
                        # Conexión
                        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=scope)
                        drive_service = build('drive', 'v3', credentials=creds)
                        client = gspread.authorize(creds)
                        
                        # Subir Foto (SOLO SUBIDA, SIN PERMISOS EXTRA PARA EVITAR ERRORES)
                        file_metadata = {'name': f"ReSI_{datetime.now().strftime('%Y%m%d')}", 'parents': [FOLDER_ID]}
                        media = MediaIoBaseUpload(io.BytesIO(foto.getvalue()), mimetype=foto.type)
                        file = drive_service.files().create(body=file_metadata, media_body=media, fields='webViewLink').execute()
                        url_foto = file.get('webViewLink')

                        # Guardar en Sheet
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        nueva_fila = [datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, email, tel, tag, descripcion, url_foto, -34.4746, -58.5132, "Pendiente"]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte enviado con éxito!")
                        st.session_state.mostrar_form = False
                        st.rerun()
                except Exception as e:
                    st.error(f"Error técnico: {e}")

# --- 6. VIDEO (PRÓXIMAMENTE) ---
st.divider()
with st.expander("🎥 Ver Tutorial de uso"):
    st.info("El video tutorial se cargará próximamente.")

# --- 7. MAPA SIEMPRE VISIBLE ---
st.write("### Mapa de Realidad Distrital")
m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

# Intentar cargar puntos del mapa
try:
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client_map = gspread.authorize(creds_map)
    data = pd.DataFrame(client_map.open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    
    if not data.empty:
        for _, r in data.iterrows():
            # Ícono circular verde con letra R
            icon_r = folium.DivIcon(html=f"""
                <div style="background-color: #28a745; color: white; border-radius: 50%; width: 30px; height: 30px; 
                display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;">R</div>
            """)
            folium.Marker([r['lat'], r['lon']], popup=r['Tag'], icon=icon_r).add_to(m)
except:
    pass # Si falla o está vacío, el mapa se muestra igual pero sin pines

st_folium(m, width="100%", height=450)
