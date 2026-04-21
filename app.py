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

st.set_page_config(page_title="ReSI - San Isidro", layout="centered")

# --- 2. ESTILOS CSS (DISEÑO REFORZADO) ---
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
    }
    div.stButton > button:hover {
        background-color: #218838 !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

# --- 3. BARRA LATERAL (GESTIÓN DE ADMINISTRADOR) ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password", placeholder="Ingresá la clave...")
    es_admin = (pwd_input == ADMIN_PASSWORD)
    
    if es_admin:
        st.success("Modo Administrador Activo")
        st.divider()
        st.write("Bienvenido, Nico.")

# --- 4. ENCABEZADO Y BOTÓN (CENTRADO PERFECTO) ---
col_izq, col_centro, col_der = st.columns([1, 2.5, 1])
with col_centro:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")
    
    st.write("") 
    
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True

# --- 5. FORMULARIO DE REPORTE (PÚBLICO) ---
if st.session_state.mostrar_form:
    st.markdown("---")
    st.write("### 📍 1. Seleccioná el punto exacto en el mapa")
    
    m_sel = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    folium.Marker([st.session_state.lat_sel, st.session_state.lon_sel], icon=folium.Icon(color='red')).add_to(m_sel)
    
    out = st_folium(m_sel, width="100%", height=300, key="selector")
    if out and out.get("last_clicked"):
        st.session_state.lat_sel = out["last_clicked"]["lat"]
        st.session_state.lon_sel = out["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        st.write("### 📝 2. Datos del Reporte")
        nombre = st.text_input("Nombre Completo (Obligatorio)")
        email = st.text_input("Email (Opcional)")
        tel = st.text_input("Teléfono (Opcional)")
        tag = st.selectbox("Categoría (Obligatorio)", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        localidad = st.selectbox("Localidad (Obligatorio)", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        direccion_exacta = st.text_input("Dirección del reporte (Calle y altura - Obligatorio)")
        descripcion = st.text_area("Descripción adicional (Opcional)")
        foto = st.file_uploader("Subir Foto (Obligatorio)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("ENVIAR REPORTE", use_container_width=True):
            if not foto or not nombre or not localidad or not direccion_exacta:
                st.error("Por favor completá los campos obligatorios.")
            else:
                try:
                    with st.spinner("Cargando reporte en la red ReSI..."):
                        # Subida a ImgBB
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]

                        # Guardado en Google Sheets
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                        sheet = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
                        
                        nueva_fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, email if email else "N/A", tel if tel else "N/A", 
                            localidad, direccion_exacta, tag, descripcion, url_foto, 
                            st.session_state.lat_sel, st.session_state.lon_sel, "Pendiente"
                        ]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte enviado con éxito!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al enviar: {e}")

# --- 6. VIDEO TUTORIAL ---
st.divider()
with st.expander("🎥 Ver Tutorial de uso"):
    st.info("Espacio reservado para el video tutorial de ReSI.")

# --- 7. MAPA DE REALIDAD DISTRITAL (PÚBLICO) ---
st.write("### 🌎 Mapa de Realidad Distrital")
m_publico = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

# Cargamos los datos una sola vez para usarlos en el mapa y en estadísticas
try:
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheet_obj = gspread.authorize(creds_map).open_by_key(SPREADSHEET_ID).sheet1
    filas = sheet_obj.get_all_values()
    
    if len(filas) > 1:
        for i, fila in enumerate(filas[1:], start=2):
            try:
                # Lectura de coordenadas (asegurando formato punto)
                lat = float(str(fila[9]).strip().replace(',', '.'))
                lon = float(str(fila[10]).strip().replace(',', '.'))
                
                fecha_rep, tag_rep, dir_rep, desc_rep, foto_rep = fila[0], fila[6], fila[5], fila[7], fila[8]
                estado_rep = fila[11] if len(fila) > 11 else "Pendiente"
                
                # Ventana del Marcador
                popup_html = f"""
                <div style="width: 220px; font-family: sans-serif;">
                    <h4 style="margin:0; color:#28a745;">{tag_rep}</h4>
                    <p style="font-size:12px; margin:5px 0;"><b>Ubicación:</b> {dir_rep}</p>
                    <p style="font-size:12px; margin:5px 0;"><b>Detalle:</b> {desc_rep[:100]}</p>
                    <p style="font-size:11px; margin:2px 0;"><b>Fecha:</b> {fecha_rep}</p>
                    <p style="font-size:11px; margin:2px 0;"><b>Estado:</b> <span style="color:blue;">{estado_rep}</span></p>
                    <img src="{foto_rep}" style="width:100%; border-radius:8px; margin-top:8px;">
                </div>"""
                
                icon_html = f'<div style="background-color: #28a745; color: white; border-radius: 50%; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white; box-shadow: 0px 2px 4px rgba(0,0,0,0.5);">R</div>'
                
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=280),
                    icon=folium.DivIcon(html=icon_html)
                ).add_to(m_publico)
            except: continue

    st_folium(m_publico, width="100%", height=550, key="mapa_final_resi")

    # --- 8. HERRAMIENTAS EXCLUSIVAS DE ADMINISTRADOR ---
    if es_admin:
        st.divider()
        st.header("📊 Panel de Análisis y Estadísticas (Privado)")
        
        # Convertimos a DataFrame para analizar rápido
        df = pd.DataFrame(filas[1:], columns=filas[0])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Reportes", len(df))
        col2.metric("Pendientes", len(df[df['Estado'] == 'Pendiente']) if 'Estado' in df.columns else 0)
        col3.metric("Localidades Activas", df['Localidad'].nunique() if 'Localidad' in df.columns else 0)
        
        st.subheader("Distribución por Categoría")
        if 'Tag' in df.columns:
            st.bar_chart(df['Tag'].value_counts())
            
        with st.expander("🛠️ DIAGNÓSTICO TÉCNICO DEL MAPA"):
            st.write("Datos crudos del Sheets:")
            st.dataframe(df)

except Exception as e:
    st.error("Conectando con la base de datos distrital...")
