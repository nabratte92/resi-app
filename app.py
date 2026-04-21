import streamlit as st
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime
import json

# --- CONFIGURACIÓN ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'

st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="centered")

# --- ESTILOS CSS ---
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

# --- ENCABEZADO Y BOTÓN (CENTRADO PERFECTO) ---
col_izq, col_centro, col_der = st.columns([1, 2.5, 1])
with col_centro:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")
    
    st.write("") 
    
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True

# --- FORMULARIO DE CARGA ---
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
        localidad = st.selectbox("Localidad (Obligatorio)", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        direccion_exacta = st.text_input("Dirección del reporte (Calle y altura o esquina - Obligatorio)")
        tag = st.selectbox("Categoría (Obligatorio)", ["Bache", "Vereda rota", "Luminaria", "Basura", "Inseguridad", "Otro"])
        descripcion = st.text_area("Descripción adicional (Opcional)")
        foto = st.file_uploader("Subir Foto (Obligatorio)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("ENVIAR REPORTE", use_container_width=True):
            if not foto or not nombre or not localidad or not direccion_exacta:
                st.error("Por favor completá los campos obligatorios.")
            else:
                try:
                    with st.spinner("Cargando reporte en la red..."):
                        res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                        url_foto = res.json()["data"]["url"]

                        creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                        sheet = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
                        
                        # Guardamos en el orden exacto de las columnas
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

# --- VIDEO TUTORIAL ---
st.divider()
with st.expander("🎥 Ver Tutorial de uso"):
    st.info("Espacio reservado para el video tutorial.")

# --- MAPA DE REALIDAD DISTRITAL (PÚBLICO) ---
st.write("### 🌎 Mapa de Realidad Distrital")

m_publico = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    creds_map = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheet_obj = gspread.authorize(creds_map).open_by_key(SPREADSHEET_ID).sheet1
    
    # get_all_values() trae todo como una lista pura, ignorando los nombres de los títulos
    filas = sheet_obj.get_all_values()
    errores = []
    puntos_dibujados = 0

    if len(filas) > 1:
        # Salteamos la fila 0 porque son los títulos (Fecha, Nombre, etc.)
        for i, fila in enumerate(filas[1:], start=2):
            try:
                # Nos aseguramos que la fila tenga al menos 11 datos para no romper
                if len(fila) < 11:
                    errores.append(f"Fila {i}: Faltan columnas en el Sheets.")
                    continue
                
                # Leemos la Latitud en la columna J (índice 9) y Longitud en K (índice 10)
                lat_raw = str(fila[9]).strip().replace(',', '.')
                lon_raw = str(fila[10]).strip().replace(',', '.')
                
                if lat_raw == "" or lon_raw == "":
                    errores.append(f"Fila {i}: Coordenadas en blanco.")
                    continue
                
                lat = float(lat_raw)
                lon = float(lon_raw)
                
                # Asignamos el resto leyendo sus posiciones
                fecha_rep = fila[0]
                dir_rep = fila[5]
                tag_rep = fila[6]
                desc_rep = fila[7]
                foto_rep = fila[8]
                estado_rep = fila[11] if len(fila) > 11 else "Pendiente"
                
                img_html = f'<img src="{foto_rep}" style="width:100%; border-radius:8px; margin-top:8px; box-shadow: 0px 1px 3px gray;">' if foto_rep and "http" in foto_rep else ''

                icon_html = f"""
                <div style="background-color: #28a745; color: white; border-radius: 50%; width: 35px; height: 35px; 
                display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.5); font-family: Arial;">R</div>"""
                
                popup_html = f"""
                <div style="width: 220px; font-family: sans-serif;">
                    <h4 style="margin:0; color:#28a745;">{tag_rep}</h4>
                    <p style="font-size:12px; margin:5px 0;"><b>Ubicación:</b> {dir_rep}</p>
                    <p style="font-size:12px; margin:5px 0;"><b>Detalle:</b> {desc_rep[:100]}</p>
                    <p style="font-size:11px; margin:2px 0;"><b>Fecha:</b> {fecha_rep}</p>
                    <p style="font-size:11px; margin:2px 0;"><b>Estado:</b> <span style="color:blue; font-weight:bold;">{estado_rep}</span></p>
                    {img_html}
                </div>"""
                
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=280),
                    icon=folium.DivIcon(html=icon_html)
                ).add_to(m_publico)
                
                puntos_dibujados += 1
                
            except Exception as e:
                errores.append(f"Fila {i}: Error técnico - {e}")

    # ========================================================
    # 🛠️ PANEL DE DIAGNÓSTICO RESTAURADO
    # ========================================================
    with st.expander("🛠️ DIAGNÓSTICO DEL MAPA (Ver Errores)"):
        st.write(f"✅ **Puntos dibujados exitosamente:** {puntos_dibujados}")
        st.write(f"⚠️ **Filas ignoradas con problemas:** {len(errores)}")
        if errores:
            for err in errores:
                st.error(err)
        st.write("---")
        st.write("**Lectura cruda del Excel (Primeras 5 filas):**")
        st.write(filas[:6])

except Exception as e:
    st.error(f"Error fatal conectando a Google Sheets: {e}")

st_folium(m_publico, width="100%", height=550, key="mapa_final_resi")
