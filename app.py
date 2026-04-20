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

# --- CONFIGURACIÓN ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
FOLDER_ID = '1q8KiQfMgKVr0wPFe1aEDo5I-8-A82D_C'
ADMIN_PASSWORD = 'resi_admin_2026'

# Inicializar estado para que el formulario no desaparezca
if 'formulario_abierto' not in st.session_state:
    st.session_state.formulario_abierto = False

# Autenticación segura
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
try:
    service_account_info = json.loads(st.secrets["GCP_CREDS"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
    client = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
except Exception as e:
    st.error(f"Error de autenticación: {e}")

# --- INTERFAZ ---
st.title("ReSI - Realidad San Isidro")

if st.button("🚨 CARGAR NUEVO REPORTE"):
    st.session_state.formulario_abierto = True

if st.session_state.formulario_abierto:
    with st.form("form_resi"):
        nombre = st.text_input("Nombre completo")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Inseguridad", "Basura", "Otro"])
        foto = st.file_uploader("Subir foto", type=["jpg", "png", "jpeg"])
        descripcion = st.text_area("Descripción")
        
        btn_enviar = st.form_submit_button("Enviar Reporte Definitivo")
        
        if btn_enviar:
            try:
                with st.spinner("Subiendo reporte a la base de datos..."):
                    # 1. Subir a Drive
                    file_metadata = {'name': f"ReSI_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 'parents': [FOLDER_ID]}
                    media = MediaIoBaseUpload(io.BytesIO(foto.getvalue()), mimetype=foto.type)
                    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='webViewLink').execute()
                    link_foto = uploaded_file.get('webViewLink')

                    # 2. Guardar en Sheets
                    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                    nueva_fila = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nombre, tag, descripcion, link_foto, -34.4746, -58.5132, "Alerta"]
                    sheet.append_row(nueva_fila)
                    
                    st.success("✅ ¡Reporte guardado! Ya podés verlo en el mapa.")
                    st.session_state.formulario_abierto = False # Cerramos el formulario
            except Exception as e:
                st.error(f"Hubo un problema al guardar: {e}")

# --- MAPA (Solo se muestra si hay datos) ---
st.subheader("Mapa de situación")
try:
    data = pd.DataFrame(client.open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    if not data.empty:
        m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
        for _, row in data.iterrows():
            folium.Marker([row['lat'], row['lon']], popup=row['Tag']).add_to(m)
        st_folium(m, width="100%", height=400)
except Exception:
    st.info("El mapa aparecerá cuando se registre el primer reporte con éxito.")
        st.subheader("Estadísticas de Gestión")
        # Aquí irían los gráficos semanales/mensuales
        st.write("Próximamente: Gráficos de rendimiento y exportación de datos.")
