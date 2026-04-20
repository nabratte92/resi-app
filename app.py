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

# --- CONFIGURACIÓN DE APIS Y GOOGLE ---
# Reemplazá esto con tus IDs reales (No borres las comillas simples)
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbs_p3azF82hLReo'
FOLDER_ID = '1q8KiQfMgKVr0wPFe1aEDo5I-8-A82D_C'
ADMIN_PASSWORD = 'resi_admin_2026'

# --- PERSONALIZACIÓN VISUAL (CSS Hack) ---
# Usamos CSS para centrar el logo y dar un color verde brillante al botón
st.markdown("""
    <style>
    /* Estilo para el botón principal (Verde brillante y ancho) */
    div.stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
        font-weight: bold;
        width: 100%;
        font-size: 20px;
        padding: 15px;
        display: block;
        margin: auto;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #218838 !important; /* Verde más oscuro al pasar el mouse */
        border-color: #218838 !important;
    }
    /* Estilo para ocultar leyendas automáticas de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# --- INICIO DE LA PÁGINA ---

# 1. ENCABEZADO CON LOGO (Centrado y grande)
# Usamos columnas laterales vacías para centrar la imagen en la del medio
col1_logo, col2_logo, col3_logo = st.columns([1, 2, 1])
with col2_logo:
    try:
        # Asegurate de que el archivo se llame exactamente logo_resi.png en GitHub
        st.image("logo_resi.png", use_container_width=True)
    except Exception:
        # Mensaje temporal si no se encuentra el logo
        st.info("🚧 Logo temporal (Esperando logo_resi.png)")

# 2. BOTÓN PRINCIPAL (Prominente, verde, wide)
# Usamos query params para controlar la apertura del formulario
if st.button("🚨 INICIAR REPORTE", type="primary", use_container_width=True):
    st.query_params["form"] = "abierto"

# --- LÓGICA DEL FORMULARIO DE CARGA ---

# Verificamos si se tocó el botón (query param "form" es "abierto")
if st.query_params.get("form") == "abierto":
    # Formulario con validaciones robustas
    with st.form("form_incidente", clear_on_submit=False):
        st.subheader("Datos Personales (Requeridos para el reporte)")
        colA, colB, colC = st.columns(3)
        with colA:
            nombre = st.text_input("Nombre completo")
        with colB:
            email = st.text_input("Email")
        with colC:
            tel = st.text_input("Teléfono")
            
        st.divider()
        st.subheader("Detalles del Incidente")
        tag = st.selectbox("Tipo de problema", ["Bache", "Vereda rota", "Fuga Agua/Gas", "Inseguridad", "Accidente", "Tránsito", "Basura", "Otro"])
        foto = st.file_uploader("Subir foto del problema", type=["jpg", "png", "jpeg"])
        descripcion = st.text_area("Breve descripción de la situación o dirección exacta")
        
        st.info("⚠️ NOTA: Al enviar, se guardarán tus datos de contacto y la ubicación simulada (San Isidro Centro) junto con el reporte.")

        btn_enviar = st.form_submit_button("Enviar Reporte Definitivo")
        
        # Procesar el envío
        if btn_enviar:
            if not all([foto, nombre, email, tel]):
                st.error("❌ Por favor, subí una foto y completá todos tus datos personales (Nombre, Email, Teléfono).")
            else:
                try:
                    with st.spinner("Conectando de forma segura con Google..."):
                        # --- BACKEND INTERNO: Autenticación segura ---
                        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                        service_account_info = json.loads(st.secrets["GCP_CREDS"])
                        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
                        client = gspread.authorize(creds)
                        drive_service = build('drive', 'v3', credentials=creds)
                        
                        # --- PROCESO: Guardar en Drive y Sheets ---
                        
                        # 1. Subir Foto a Google Drive
                        file_metadata = {'name': f"ReSI_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 'parents': [FOLDER_ID]}
                        media = MediaIoBaseUpload(io.BytesIO(foto.getvalue()), mimetype=foto.type)
                        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                        link_foto = uploaded_file.get('webViewLink')

                        # 2. Guardar Datos Completos en Google Sheets
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        lat, lon = -34.4746, -58.5132 # Centro de San Isidro por defecto
                        
                        nueva_fila = [fecha_actual, nombre, email, tel, tag, descripcion, link_foto, lat, lon, "Alerta"]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte guardado! Ya podés verlo en el mapa.")
                        st.query_params["form"] = "cerrado" # Cerramos el formulario al tener éxito

                except Exception as e:
                    # Mensaje de error detallado para diagnosticar la conexión
                    st.error(f"❌ Hubo un problema al guardar. El error reportado por Google es: {e}")
                    if "invalid_grant" in str(e).lower():
                        st.error("💡 EXPLICACIÓN: El error 'invalid_grant' significa que los secretos que pegaste en el panel de Streamlit no son válidos. Por favor, revisá que copiaste TODO el JSON (empezando con '{' y terminando con '}'), que incluiste `GCP_CREDS = '''` al principio y `'''` al final, y que no te falten caracteres al pegar.")

# 3. VIDEO TUTORIAL (Reserve Space)
st.divider()
with st.expander("🎥 ¿Cómo funciona ReSI? Ver Tutorial (Próximamente)", expanded=True):
     # st.video("tutorial_resi.mp4") # Asegurate de subirlo a GitHub con este nombre
     st.info("🚧 El video tutorial estará disponible pronto. Estamos trabajando en su producción.")

# 4. MAPA DE SITUACIÓN (Visible siempre, se actualiza al cargar)
st.subheader("Mapa de situación en San Isidro")

# Instanciamos el mapa (OpenStreetMap por defecto)
m = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

# Lógica robusta para intentar leer la planilla y poblar el mapa
try:
    # Autenticación segura también para el mapa (copiada de arriba para que sea independiente)
    scope_map = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    service_account_info_map = json.loads(st.secrets["GCP_CREDS"])
    creds_map = Credentials.from_service_account_info(service_account_info_map, scopes=scope_map)
    client_map = gspread.authorize(creds_map)
    
    sheet_data = pd.DataFrame(client_map.open_by_key(SPREADSHEET_ID).sheet1.get_all_records())
    
    if not sheet_data.empty:
        # Dibujamos los pines customizados si hay reportes
        for _, row in sheet_data.iterrows():
            # Lógica del pin custom: círculo verde con la letra R blanca
            icon_html = f"""
                <div style="
                    font-family: Arial;
                    color: white;
                    background-color: green;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    border: 2px solid white;
                    ">R</div>
            """
            
            folium.Marker(
                [row['lat'], row['lon']],
                popup=f"<b>{row['tag']}</b><br>Estado: {row['Estado']}<br><a href='{row['Foto']}'>Ver Foto</a>",
                tooltip=row['tag'],
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)
            
except Exception as sheet_error:
    # Mostramos consejos útiles si la planilla está vacía o no tiene permisos, pero no ocultamos el mapa
    if "spreadsheet not found" in str(sheet_error).lower() or "permission denied" in str(sheet_error).lower():
         st.warning(f"💡 El mapa no pudo cargar datos de la planilla. Error: {sheet_error}. Asegurate de compartir la planilla como Editor con el mail de la Cuenta de Servicio y que el SPREADSHEET_ID sea correcto.")
    elif "not found" in str(sheet_error).lower() or "spreadsheet" in str(sheet_error).lower():
        st.info("El mapa aparecerá con puntos cuando se registre el primer reporte con éxito.")

# Dibujamos el mapa definitivo (vacío o con puntos)
st_folium(m, width="100%", height=500)

# --- PANEL DE ADMINISTRADOR (OCULTO) ---
st.divider()
if st.checkbox("🔒 Ver Informe Estadístico (Solo Administradores)"):
    pass_input = st.text_input("Contraseña Admin", type="password")
    if pass_input == ADMIN_PASSWORD:
        st.success("Acceso Concedido")
        st.write("Próximamente: Gráficos de rendimiento semanal/mensual.")
