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

st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="centered")

# --- 2. ESTILOS CSS (DISEÑO Y BOTÓN VERDE) ---
st.markdown("""
    <style>
    /* Centrar logo y botones */
    .stApp {
        align-items: center;
    }
    div.stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
        max-width: 500px;
        margin: 0 auto;
        display: block;
        font-size: 22px;
        font-weight: bold;
        padding: 18px;
        border-radius: 12px;
        border: none;
    }
    /* Estilo para los campos del formulario */
    .stTextInput, .stSelectbox, .stTextArea {
        max-width: 500px;
        margin: 0 auto;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

# --- 3. ENCABEZADO (LOGO GRANDE) ---
# Usamos una columna ancha para que el logo no se achique
col_img = st.columns([1, 6, 1])
with col_img[1]:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")

st.write("") # Espacio

# --- 4. BOTÓN DE INICIO CENTRADO ---
col_btn = st.columns([1, 4, 1])
with col_btn[1]:
    if st.button("🚨 INICIAR REPORTE"):
        st.session_state.mostrar_form = True

# --- 5. FORMULARIO DE CARGA ---
if st.session_state.mostrar_form:
    st.markdown("---")
    st.write("### 📍 1. Marcá la ubicación en el mapa")
    
    # Mapa selector
    m_sel = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    folium.Marker([st.session_state.lat_sel, st.session_state.lon_sel], icon=folium.Icon(color='red')).add_to(m_sel)
    
    out = st_folium(m_sel, width="100%", height=300, key="selector")
    if out and out.get("last_clicked"):
        st.session_state.lat_sel = out["last_clicked"]["lat"]
        st.session_state.lon_sel = out["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        st.write("### 📝 2. Completá los datos")
        nombre = st.text_input("Nombre (Obligatorio)")
        email = st.text_input("Email (Opcional)")
        tel = st.text_input("Teléfono (Opcional)")
        tag = st.selectbox("Categoría", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        descripcion = st.text_area("Descripción")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("ENVIAR REPORTE"):
            if not foto or not nombre:
                st.error("Nombre y Foto son obligatorios.")
            else:
                try:
                    with st.spinner("Subiendo reporte..."):
                        # Foto a ImgBB
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]

                        # Guardar en Google Sheets
                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                        client = gspread.authorize(creds)
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        
                        nueva_fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), 
                            nombre, email if email else "N/A", tel if tel else "N/A", 
                            tag, descripcion, url_foto, 
                            st.session_state.lat_sel, st.session_state.lon_sel, "Pendiente"
                        ]
                        sheet.append_row(nueva_fila)
                        
                        st.success("✅ ¡Reporte cargado con éxito!")
                        st.session_state.mostrar_form = False
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 6. MAPA PRINCIPAL DE REPORTES (EL QUE VE EL PÚBLICO) ---
st.write("---")
st.write("### 🌎 Mapa de Realidad Distrital")

# Mapa base
m_publico = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    # Conectamos para leer los puntos
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client_map = gspread.authorize(creds_map)
    # Obtenemos todos los registros
    datos = client_map.open_by_key(SPREADSHEET_ID).sheet1.get_all_records()
    df = pd.DataFrame(datos)

    if not df.empty:
        for _, r in df.iterrows():
            try:
                # Limpiamos coordenadas (por si tienen comas)
                lat = float(str(r['lat']).replace(',', '.'))
                lon = float(str(r['lon']).replace(',', '.'))
                
                # Definimos el ícono circular verde con la R
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
                
                # Contenido del Popup (Miniatura de foto incluida)
                popup_text = f"""
                <div style="width: 180px; font-family: sans-serif;">
                    <h4 style="margin:0; color:#28a745;">{r['Tag']}</h4>
                    <p style="font-size:11px; margin:5px 0;">{r['Descripcion']}</p>
                    <img src="{r['Foto']}" style="width:100%; border-radius:5px; margin-top:5px;">
                    <br><small style="color:gray;">Estado: {r['Estado']}</small>
                </div>"""
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=250),
                    icon=folium.DivIcon(html=icon_html)
                ).add_to(m_publico)
            except:
                continue
except:
    st.info("Cargando puntos en el mapa...")

# Renderizar el mapa final
st_folium(m_publico, width="100%", height=500, key="mapa_final_resi")
