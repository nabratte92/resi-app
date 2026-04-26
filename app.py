import streamlit as st
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime
import json
import pandas as pd

# --- 1. CONFIGURACIÓN Y CONSTANTES ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
ADMIN_PASSWORD = 'resi_admin_2026'

# Listas de categorías según NUEVA gravedad (Rojo, Naranja, Amarillo)
CATS_ROJAS = ["Poste en riesgo de caída", "Hecho de inseguridad", "Riesgo de derrumbe", "Árbol caído", "Abuso de autoridad", "Plagas", "Fuga de gas"]
CATS_NARANJAS = ["Contenedor desbordado", "Corte de luz", "Cloaca colapsada", "Zanja tapada", "Pérdida de agua", "Corte de agua"]
CATS_AMARILLAS = ["Bache", "Vereda rota", "Luminaria con problemas", "Auto mal estacionado", "Falta rampa", "Poda mal hecha", "Problemas de tránsito", "Obra mal hecha", "Otros"]

# Lista combinada en el orden para el desplegable
LISTA_CATEGORIAS = [
    "Bache", "Vereda rota", "Luminaria con problemas", "Poste en riesgo de caída",
    "Contenedor desbordado", "Pérdida de agua", "Hecho de inseguridad",
    "Riesgo de derrumbe", "Zanja tapada", "Árbol caído", "Auto mal estacionado",
    "Falta rampa", "Poda mal hecha", "Abuso de autoridad", "Cloaca colapsada",
    "Corte de luz", "Problemas de tránsito", "Obra mal hecha", "Plagas",
    "Corte de agua", "Fuga de gas", "Otros"
]

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
    .noticia-box {
        background-color: #f8f9fa;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

# Autorización general de Google Sheets
try:
    creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sh = gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
except Exception as e:
    st.error("Error conectando a la base de datos principal.")

# --- 3. BARRA LATERAL (GESTIÓN) ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password", placeholder="Clave...")
    es_admin = (pwd_input == ADMIN_PASSWORD)
    if es_admin:
        st.success("Modo Administrador Activo")

# --- 4. CABECERA (LOGO, SLOGAN Y BOTÓN) ---
col_izq, col_centro, col_der = st.columns([1, 5, 1])
with col_centro:
    try:
        st.image("logo_resi.png", use_container_width=True)
    except:
        st.header("ReSI - Realidad San Isidro")
    
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
        tag = st.selectbox("Categoría (Obligatorio)", LISTA_CATEGORIAS)
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
                        sheet_reportes = sh.sheet1
                        nueva_fila = [datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, email if email else "N/A", tel if tel else "N/A", localidad, direccion_exacta, tag, descripcion, url_foto, str(st.session_state.lat_sel).replace('.', ','), str(st.session_state.lon_sel).replace('.', ','), "Pendiente"]
                        sheet_reportes.append_row(nueva_fila)
                        st.success("✅ ¡Enviado!")
                        st.session_state.mostrar_form = False
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")

# --- 6. VIDEO TUTORIAL ---
st.divider()
st.write("### 🎥 Tutorial de Uso")
c1, c2, c3 = st.columns([1, 1.8, 1])
with c2:
    try:
        st.video("tutorial.mp4")
    except:
        st.info("Video no encontrado en el repositorio.")

# --- 7. NOVEDADES DE GESTIÓN (PÚBLICO) ---
st.divider()
st.write("### 📰 Novedades y Soluciones")
try:
    sheet_nov = sh.worksheet("Novedades")
    novedades_data = sheet_nov.get_all_values()
    
    if len(novedades_data) > 1:
        # Mostramos las últimas 5 noticias (leemos la lista al revés)
        for nov in reversed(novedades_data[1:]):
            if len(nov) >= 3:
                fecha_nov, titulo_nov, texto_nov = nov[0], nov[1], nov[2]
                st.markdown(f"""
                <div class="noticia-box">
                    <h4 style='margin-bottom: 0px; color: #333;'>{titulo_nov}</h4>
                    <p style='font-size: 12px; color: gray; margin-top: 0px;'>🗓️ {fecha_nov}</p>
                    <p style='margin-bottom: 0px;'>{texto_nov}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Próximamente estaremos compartiendo proyectos de ordenanza y soluciones para San Isidro.")
except Exception as e:
    st.info("Sección de Novedades en construcción.")


# --- 8. MAPA PRINCIPAL CON SEMÁFORO DE GRAVEDAD ---
st.divider()
st.write("### 🌎 Mapa de Realidad Distrital")
m_p = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)

try:
    rows = sh.sheet1.get_all_values()
    if len(rows) > 1:
        for r in rows[1:]:
            try:
                if len(r) < 11:
                    continue
                lt = float(str(r[9]).replace(',', '.'))
                ln = float(str(r[10]).replace(',', '.'))
                tag_rep = r[6]
                
                if tag_rep in CATS_ROJAS:
                    bg_color, text_color = "#dc3545", "white" # Rojo
                elif tag_rep in CATS_NARANJAS:
                    bg_color, text_color = "#fd7e14", "black" # Naranja
                elif tag_rep in CATS_AMARILLAS:
                    bg_color, text_color = "#ffc107", "black" # Amarillo
                else:
                    bg_color, text_color = "#28a745", "white" # Verde por defecto
                
                pop = f"""<div style='width:200px; font-family:sans-serif;'>
                <h4 style='color:{bg_color}; margin:0;'>{tag_rep}</h4>
                <p style='font-size:12px; margin:5px 0;'><b>Ubicación:</b> {r[5]}</p>
                <p style='font-size:11px; margin:2px 0;'><b>Fecha:</b> {r[0]}</p>
                <img src='{r[8]}' style='width:100%; border-radius:5px;'></div>"""
                
                icon = f'<div style="background-color:{bg_color}; color:{text_color}; border-radius:50%; width:35px; height:35px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid {text_color}; box-shadow: 0px 2px 4px rgba(0,0,0,0.5);">R</div>'
                folium.Marker([lt, ln], popup=folium.Popup(pop, max_width=250), icon=folium.DivIcon(html=icon)).add_to(m_p)
            except: continue
    st_folium(m_p, width="100%", height=500, key="mapa_final")

    # --- 9. PANEL DE CONTROL EXCLUSIVO (ESTADÍSTICAS Y EDITOR) ---
    if es_admin:
        st.divider()
        st.header("📊 Panel de Control: Estadísticas")
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.columns = [c.strip() for c in df.columns]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reportes", len(df))
        if 'Nombre' in df.columns: c2.metric("Aportantes Únicos", df['Nombre'].nunique())
        if 'Estado' in df.columns: c3.metric("Pendientes", len(df[df['Estado'] == 'Pendiente']))

        if 'Tag' in df.columns:
            def asignar_gravedad(tag):
                if tag in CATS_ROJAS: return "1. 🔴 Extrema (Rojo)"
                if tag in CATS_NARANJAS: return "2. 🟠 Alta (Naranja)"
                if tag in CATS_AMARILLAS: return "3. 🟡 Moderada (Amarillo)"
                return "4. 🟢 Otros"
            
            df['Gravedad'] = df['Tag'].apply(asignar_gravedad)
            
            st.subheader("Reportes discriminados por Gravedad (Color)")
            st.bar_chart(df['Gravedad'].value_counts().sort_index())

            st.subheader("Reportes por Categoría Específica")
            st.bar_chart(df['Tag'].value_counts())
        
        st.subheader("Reportes por Localidad")
        if 'Localidad' in df.columns: st.bar_chart(df['Localidad'].value_counts())

        # --- REDACTOR DE NOVEDADES ---
        st.divider()
        st.header("📝 Publicar Nueva Noticia")
        with st.form("form_novedad", clear_on_submit=True):
            tit_nov = st.text_input("Título de la Novedad / Proyecto")
            cont_nov = st.text_area("Cuerpo del anuncio")
            
            if st.form_submit_button("Publicar Noticia en la App"):
                if tit_nov and cont_nov:
                    try:
                        sheet_nov = sh.worksheet("Novedades")
                        sheet_nov.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), tit_nov, cont_nov])
                        st.success("✅ ¡Noticia publicada con éxito! Refrescá la página para verla.")
                    except Exception as e:
                        st.error("Error: Asegurate de haber creado la pestaña 'Novedades' en tu Google Sheets.")
                else:
                    st.warning("Completá el título y el contenido antes de publicar.")

except Exception as e: st.error("Error al cargar datos del mapa.")
