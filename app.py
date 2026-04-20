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

# --- 2. ESTILOS CSS (BOTÓN VERDE Y CENTRADO) ---
st.markdown("""
    <style>
    /* Botón verde y grande */
    div.stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
        font-size: 20px;
        font-weight: bold;
        padding: 15px;
        border-radius: 10px;
        border: none;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

# --- 3. ENCABEZADO Y BOTÓN CENTRADO ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")
    
    # Botón centrado debajo del logo
    if st.button("🚨 INICIAR REPORTE"):
        st.session_state.mostrar_form = True

# --- 4. FORMULARIO DE REPORTE ---
if st.session_state.mostrar_form:
    st.write("---")
    st.write("### 📍 Ubicá el reporte en el mapa")
    m_sel = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    folium.Marker([st.session_state.lat_sel, st.session_state.lon_sel], icon=folium.Icon(color='red')).add_to(m_sel)
    
    out = st_folium(m_sel, width="100%", height=300, key="selector")
    if out and out.get("last_clicked"):
        st.session_state.lat_sel = out["last_clicked"]["lat"]
        st.session_state.lon_sel = out["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        st.write("### 📝 Datos del Reporte")
        nombre = st.text_input("Nombre (Obligatorio)")
        email = st.text_input("Email (Opcional)")
        tel = st.text_input("Teléfono (Opcional)")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        descripcion = st.text_area("Descripción de la situación")
        foto = st.file_uploader("Subir Foto (Obligatorio)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Enviar Reporte Definitivo"):
            if not foto or not nombre:
                st.error("Por favor, cargá tu nombre y una foto.")
            else:
                try:
                    with st.spinner("Cargando reporte en la red ReSI..."):
                        # 1. Foto a ImgBB
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]

                        # 2. Guardar en Sheets
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                        client = gspread.authorize(creds)
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        
                        nueva_fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), 
                            nombre, 
                            email if email else "N/A", 
                            tel if tel else "N/A", 
                            tag, 
                            descripcion, 
                            url_foto, 
                            st.session_state.lat_sel, 
                            st.session_state.lon_sel, 
                            "Pendiente"
                        ]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte enviado con éxito!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# --- 5. MAPA PRINCIPAL DE REALIDAD DISTRITAL ---
st.divider()
st.write("### 🌎 Mapa de Realidad Distrital")

# Centrado en San Isidro
m_publico = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    # Conexión para leer puntos
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client = gspread.authorize(creds_map)
    datos = client.open_by_key(SPREADSHEET_ID).sheet1.get_all_records()
    df = pd.DataFrame(datos)

    if not df.empty:
        for _, r in df.iterrows():
            try:
                # Convertir coordenadas a número (limpia comas o textos)
                lat = float(str(r['lat']).replace(',', '.'))
                lon = float(str(r['lon']).replace(',', '.'))
                
                # Ícono Verde con R (Tu marca)
                icon_html = f"""
                <div style="
                    background-color: #28a745; 
                    color: white; 
                    border-radius: 50%; 
                    width: 32px; 
                    height: 32px; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    font-weight: bold; 
                    border: 2px solid white;
                    box-shadow: 0px 2px 4px rgba(0,0,0,0.4);
                ">R</div>"""
                
                # Popup con miniatura de la foto
                popup_html = f"""
                <div style="width: 200px; font-family: Arial, sans-serif;">
                    <h4 style="margin:0; color:#28a745;">{r['Tag']}</h4>
                    <p style="margin:5px 0; font-size:12px;">{r['Descripcion']}</p>
                    <img src="{r['Foto']}" style="width:100%; border-radius:5px; margin-top:8px;">
                    <p style="margin-top:5px; font-size:10px; color:gray;">Estado: {r['Estado']}</p>
                </div>"""
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.DivIcon(html=icon_html)
                ).add_to(m_publico)
            except:
                continue # Si hay una fila con error, la ignora y sigue con el resto

except Exception as e:
    st.info("Actualizando mapa de reportes...")

# Mostrar el mapa principal
st_folium(m_publico, width="100%", height=500, key="mapa_principal_resi")
