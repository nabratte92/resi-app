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

# --- CONFIGURACIÓN DE APIS Y GOOGLE ---
# Reemplazá esto con tus IDs reales
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
FOLDER_ID = '1q8KiQfMgKVr0wPFe1aEDo5I-8-A82D_C'
ADMIN_PASSWORD = 'resi_admin_2026' # Podés cambiar tu contraseña acá

# Autenticación
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
service_account_info = json.loads(st.secrets["GCP_CREDS"])
creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

# --- FUNCIONES DE BACKEND ---
def subir_foto_drive(file):
    file_metadata = {'name': file.name, 'parents': [FOLDER_ID]}
    media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype=file.type)
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    return uploaded_file.get('webViewLink')

def guardar_reporte_sheets(datos):
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    sheet.append_row(datos)

# --- INTERFAZ DE USUARIO (UI) ---
st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="wide")

# 1. LOGO Y TÍTULO
st.markdown("<h1 style='text-align: center;'>ReSI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Realidad San Isidro</h3>", unsafe_allow_html=True)
try:
    st.image("logo_resi.png", width=300) # Asegurate de que el archivo se llame así
except:
    st.info("Pincha aquí para ver el logo una vez cargado el archivo logo_resi.png")

# 2. BOTÓN PRINCIPAL DE CARGA
if st.button("🚨 CARGAR REPORTE", use_container_width=True, type="primary"):
    with st.form("form_reporte", clear_on_submit=True):
        st.subheader("Nuevo Reporte de Incidente")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nombre = st.text_input("Nombre completo")
            email = st.text_input("Email")
            tel = st.text_input("Teléfono")
        with col_f2:
            tag = st.selectbox("Tipo de problema", ["Bache", "Vereda rota", "Fuga Agua/Gas", "Inseguridad", "Accidente", "Tránsito", "Basura", "Otro"])
            foto = st.file_uploader("Subir foto", type=["jpg", "jpeg", "png"])
            descripcion = st.text_area("Descripción de la situación")

        st.info("Seleccioná la ubicación en el mapa de abajo (Simulado por ahora)")
        lat, lon = -34.4746, -58.5132 # Centro de San Isidro por defecto
        
        submit = st.form_submit_button("Enviar Reporte a ReSI")
        
        if submit:
            if foto and nombre:
                link_foto = subir_foto_drive(foto)
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Armamos la fila para Google Sheets
                nueva_fila = [fecha_actual, nombre, email, tel, tag, descripcion, link_foto, lat, lon, "Alerta"]
                guardar_reporte_sheets(nueva_fila)
                st.success("✅ Reporte enviado con éxito. El municipio y la comunidad ya pueden verlo.")
            else:
                st.error("Por favor, completá tu nombre y subí una foto.")

# 3. VIDEO EXPLICATIVO
st.divider()
with st.expander("📖 ¿Cómo funciona ReSI? Ver Tutorial"):
    st.video("tutorial_resi.mp4") # Asegurate de subirlo a GitHub con este nombre

# 4. MAPA INTERACTIVO
st.subheader("📍 Mapa de Realidad Distrital")
# Aquí leemos la planilla para mostrar los puntos reales
try:
    sheet_data = pd.DataFrame(client.open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
    
    for _, row in sheet_data.iterrows():
        # Lógica del pin verde con la letra R
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"<b>{row['tag']}</b><br>Estado: {row['Estado']}<br><a href='{row['Foto']}'>Ver Foto</a>",
            icon=folium.DivIcon(html=f"""<div style="font-family: Arial; color: white; background-color: green; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;">R</div>""")
        ).add_to(m)
    st_folium(m, width="100%", height=500)
except:
    st.warning("El mapa se activará cuando haya reportes cargados en la planilla.")

# --- SECCIÓN ADMINISTRADOR (OCULTA) ---
st.sidebar.divider()
with st.sidebar.expander("🔒 Panel de Control ReSI"):
    pass_input = st.text_input("Contraseña Admin", type="password")
    if pass_input == ADMIN_PASSWORD:
        st.success("Acceso Concedido")
        st.subheader("Estadísticas de Gestión")
        # Aquí irían los gráficos semanales/mensuales
        st.write("Próximamente: Gráficos de rendimiento y exportación de datos.")
