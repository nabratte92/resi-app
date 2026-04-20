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
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ENCABEZADO (LOGO) ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")

# --- 4. BOTÓN DE CARGA ---
if st.button("🚨 INICIAR REPORTE", type="primary"):
    st.session_state.mostrar_form = True

# --- 5. LÓGICA DEL FORMULARIO ---
if st.session_state.get('mostrar_form', False):
    with st.form("form_reporte", clear_on_submit=True):
        st.write("### Datos del Nuevo Reporte")
        nombre = st.text_input("Nombre")
        email = st.text_input("Email")
        tel = st.text_input("Teléfono")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Inseguridad", "Luminaria", "Basura", "Otro"])
        descripcion = st.text_area("Descripción de la situación")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte a ReSI"):
            if not foto or not nombre or not email:
                st.error("Por favor completá los datos obligatorios y subí una foto.")
            else:
                try:
                    with st.spinner("Conectando con los servidores de Google..."):
                        # Definición de permisos
                        scopes = [
                            'https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive',
                            'https://www.googleapis.com/auth/drive.file'
                        ]
                        
                        # Carga de credenciales desde Secrets
                        json_creds = json.loads(st.secrets["GCP_CREDS"])
                        creds = Credentials.from_service_account_info(json_creds, scopes=scopes)
                        
                        # Construcción de servicios (Bypass de error de API Key)
                        drive_service = build('drive', 'v3', credentials=creds, static_discovery=False)
                        client = gspread.authorize(creds)
                        
                        # 1. Subir Foto
                        file_metadata = {'name': f"ReSI_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 'parents': [FOLDER_ID]}
                        media = MediaIoBaseUpload(io.BytesIO(foto.getvalue()), mimetype=foto.type)
                        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='webViewLink').execute()
                        url_foto = uploaded_file.get('webViewLink')

                        # 2. Guardar en Sheets
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        nueva_fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), 
                            nombre, email, tel, tag, descripcion, url_foto, 
                            -34.4746, -58.5132, "Pendiente"
                        ]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte enviado con éxito! Ya podés verlo en el mapa.")
                        st.session_state.mostrar_form = False
                        st.rerun()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# --- 6. VIDEO TUTORIAL ---
st.divider()
with st.expander("🎥 Ver Tutorial de uso"):
    st.info("El video tutorial se cargará próximamente.")

# --- 7. MAPA DE SITUACIÓN ---
st.write("### Mapa de Realidad Distrital")
m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    json_creds_map = json.loads(st.secrets["GCP_CREDS"])
    creds_map = Credentials.from_service_account_info(json_creds_map, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client_map = gspread.authorize(creds_map)
    data = pd.DataFrame(client_map.open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    
    if not data.empty:
        for _, r in data.iterrows():
            # Ícono circular verde con letra R
            icon_r = folium.DivIcon(html=f"""
                <div style="background-color: #28a745; color: white; border-radius: 50%; width: 30px; height: 30px; 
                display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;">R</div>
            """)
            folium.Marker([r['lat'], r['lon']], popup=f"{r['Tag']}: {r['Estado']}", icon=icon_r).add_to(m)
except:
    pass 

st_folium(m, width="100%", height=450)
