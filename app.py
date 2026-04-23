import streamlit as st
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime
import json
import pandas as pd

# --- 1. CONFIGURACIÓN ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
ADMIN_PASSWORD = 'resi_admin_2026'

st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="centered")

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-size: 22px;
        font-weight: bold;
        padding: 15px;
        border-radius: 10px;
        border: none;
        display: block;
        margin: 0 auto;
    }
    div.stButton > button:hover {
        background-color: #218838 !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .slogan {
        text-align: center;
        font-size: 19px;
        font-style: italic;
        color: #444;
        margin-top: -15px;
        margin-bottom: 25px;
        font-family: 'Arial', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

# --- 3. BARRA LATERAL (GESTIÓN) ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password", placeholder="Clave...")
    es_admin = (pwd_input == ADMIN_PASSWORD)
    if es_admin:
        st.success("Modo Administrador Activo")

# --- 4. CABECERA (LOGO, SLOGAN Y BOTÓN) ---
col_izq, col_centro, col_der = st.columns([1, 3, 1])
with col_centro:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")
    
    # Slogan centrado
    st.markdown('<p class="slogan">Una herramienta para que el intendente y sus funcionarios se ubiquen en el mapa</p>', unsafe_allow_html=True)
    
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True

# --- 5. FORMULARIO DE REPORTE ---
if st.session_state.mostrar_form:
    st.markdown("---")
    st.write("### 📍 1. Ubicación exacta")
    m_sel = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    folium.Marker([st.session_state.lat_sel, st.session_state.lon_sel], icon=folium.Icon(color='red')).add_to(m_sel)
    out = st_folium(m_sel, width="100%", height=300, key="selector")
    if out and out.get("last_clicked"):
        st.session_state.lat_sel = out["last_clicked"]["lat"]
        st.session_state.lon_sel = out["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        nombre = st.text_input("Nombre Completo (Obligatorio)")
        email = st.text_input("Email (Opcional)")
        tel = st.text_input("Teléfono (Opcional)")
        tag = st.selectbox("Categoría (Obligatorio)", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        localidad = st.selectbox("Localidad (Obligatorio)", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        direccion_exacta = st.text_input("Dirección (Calle y altura - Obligatorio)")
        descripcion = st.text_area("Descripción adicional (Opcional)")
        foto = st.file_uploader("Subir Foto (Obligatorio)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("ENVIAR REPORTE", use_container_width=True):
            if not foto or not nombre or not localidad or not direccion_exacta:
                st.error("Completá los campos obligatorios.")
            else:
                try:
                    with st.spinner("Cargando..."):
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                        sheet = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
                        nueva_fila = [datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, email if email else "N/A", tel if tel else "N/A", localidad, direccion_exacta, tag, descripcion, url_foto, str(st.session_state.lat_sel).replace('.', ','), str(st.session_state.lon_sel).replace('.', ','), "Pendiente"]
                        sheet.append_row(nueva_fila)
                        st.success("✅ ¡Enviado!")
                        st.session_state.mostrar_form = False
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# --- 6. VIDEO TUTORIAL (CENTRADO Y CHICO) ---
st.divider()
st.write("### 🎥 Tutorial de Uso")
c1, c2, c3 = st.columns([1, 1.8, 1])
with c2:
    try:
        st.video("tutorial.mp4")
    except:
        st.info("Video no encontrado en el repositorio.")

# --- 7. MAPA PRINCIPAL ---
st.divider()
st.write("### 🌎 Mapa de Realidad Distrital")
m_p = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sh = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
    rows = sh.get_all_values()
    if len(rows) > 1:
        for r in rows[1:]:
            try:
                lt = float(str(r[9]).replace(',', '.'))
                ln = float(str(r[10]).replace(',', '.'))
                pop = f"""<div style='width:200px; font-family:sans-serif;'>
                <h4 style='color:#28a745; margin:0;'>{r[6]}</h4>
                <p style='font-size:12px; margin:5px 0;'><b>Ubicación:</b> {r[5]}</p>
                <p style='font-size:11px; margin:2px 0;'><b>Fecha:</b> {r[0]}</p>
                <img src='{r[8]}' style='width:100%; border-radius:5px;'></div>"""
                icon = f'<div style="background-color:#28a745; color:white; border-radius:50%; width:35px; height:35px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white;">R</div>'
                folium.Marker([lt, ln], popup=folium.Popup(pop, max_width=250), icon=folium.DivIcon(html=icon)).add_to(m_p)
            except: continue
    st_folium(m_p, width="100%", height=500, key="mapa_final")

    # --- 8. ESTADÍSTICAS ADMIN ---
    if es_admin:
        st.divider()
        st.header("📊 Estadísticas de Gestión")
        df = pd.DataFrame(rows[1:], columns=rows[0])
        # Limpieza de nombres de columnas por si acaso
        df.columns = [c.strip() for c in df.columns]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reportes", len(df))
        if 'Nombre' in df.columns: c2.metric("Aportantes Únicos", df['Nombre'].nunique())
        if 'Estado' in df.columns: c3.metric("Pendientes", len(df[df['Estado'] == 'Pendiente']))

        st.subheader("Reportes por Categoría")
        if 'Tag' in df.columns: st.bar_chart(df['Tag'].value_counts())
        
        st.subheader("Reportes por Localidad")
        if 'Localidad' in df.columns: st.bar_chart(df['Localidad'].value_counts())

        st.subheader("Evolución Temporal")
        if 'Fecha' in df.columns:
            df['f'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y %H:%M', errors='coerce')
            st.line_chart(df['f'].dt.to_period('M').astype(str).value_counts().sort_index())

except Exception as e: st.error("Error al cargar datos.")
