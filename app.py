import streamlit as st
import folium
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import pandas as pd

# --- 1. CONFIGURACIÓN Y CONSTANTES ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
ADMIN_PASSWORD = 'resi_admin_2026'

CATS_ROJAS = ["Poste en riesgo de caída", "Hecho de inseguridad", "Riesgo de derrumbe", "Árbol caído", "Abuso de autoridad", "Plagas", "Fuga de gas"]
CATS_NARANJAS = ["Contenedor desbordado", "Corte de luz", "Cloaca colapsada", "Zanja tapada", "Pérdida de agua", "Corte de agua"]
CATS_AMARILLAS = ["Bache", "Vereda rota", "Luminaria con problemas", "Auto mal estacionado", "Falta rampa", "Poda mal hecha", "Problemas de tránsito", "Obra mal hecha", "Otros"]

LISTA_CATEGORIAS = [
    "Bache", "Vereda rota", "Luminaria con problemas", "Poste en riesgo de caída",
    "Contenedor desbordado", "Pérdida de agua", "Hecho de inseguridad",
    "Riesgo de derrumbe", "Zanja tapada", "Árbol caído", "Auto mal estacionado",
    "Falta rampa", "Poda mal hecha", "Abuso de autoridad", "Cloaca colapsada",
    "Corte de luz", "Problemas de tránsito", "Obra mal hecha", "Plagas",
    "Corte de agua", "Fuga de gas", "Otros"
]

st.set_page_config(page_title="ReSI - Realidad San Isidro", layout="centered")

# --- FUNCIÓN PARA VISTA PREVIA DE LINKS ---
def obtener_vista_previa(url):
    try:
        header = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=header, timeout=5)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        titulo = soup.find("meta", property="og:title")
        titulo = titulo["content"] if titulo else soup.title.string if soup.title else "Noticia / Publicación"
        
        desc = soup.find("meta", property="og:description")
        desc = desc["content"][:150] + "..." if desc else "Hacé clic para ver más detalles en la fuente original."
        
        img = soup.find("meta", property="og:image")
        img_url = img["content"] if img else None
        
        return titulo, desc, img_url
    except:
        return None, None, None

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-size: 22px;
        font-weight: bold;
        padding: 15px; border-radius: 10px; border: none;
        display: block; margin: 0 auto;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    .slogan {
        text-align: center; font-size: 19px; font-style: italic;
        color: #444; margin-top: -15px; margin-bottom: 25px;
    }
    .noticia-box {
        background-color: #ffffff; border: 1px solid #ddd;
        padding: 15px; border-radius: 10px; margin-bottom: 20px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .link-card {
        border: 1px solid #eee; border-radius: 8px; overflow: hidden;
        margin-top: 10px; background: #fafafa; text-decoration: none; color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False

try:
    creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sh = gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
except:
    st.error("Error de conexión.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password")
    es_admin = (pwd_input == ADMIN_PASSWORD)

# --- 4. CABECERA ---
col_izq, col_centro, col_der = st.columns([1, 35, 1])
with col_centro:
    try: st.image("logo_resi.png", use_container_width=True)
    except: st.header("ReSI - Realidad San Isidro")
    st.markdown('<p class="slogan">Una herramienta para que el intendente y sus funcionarios se ubiquen en el mapa</p>', unsafe_allow_html=True)
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True

# --- 5. FORMULARIO ---
if st.session_state.mostrar_form:
    st.markdown("---")
    m_sel = folium.Map(location=[st.session_state.lat_sel, st.session_state.lon_sel], zoom_start=15)
    folium.Marker([st.session_state.lat_sel, st.session_state.lon_sel], icon=folium.Icon(color='red')).add_to(m_sel)
    out = st_folium(m_sel, width="100%", height=300, key="selector")
    if out and out.get("last_clicked"):
        st.session_state.lat_sel = out["last_clicked"]["lat"]
        st.session_state.lon_sel = out["last_clicked"]["lng"]
        st.rerun()

    with st.form("form_reporte", clear_on_submit=True):
        nombre = st.text_input("Nombre Completo (Obligatorio)")
        tag = st.selectbox("Categoría (Obligatorio)", LISTA_CATEGORIAS)
        localidad = st.selectbox("Localidad (Obligatorio)", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        direccion_exacta = st.text_input("Dirección (Calle y altura - Obligatorio)")
        descripcion = st.text_area("Descripción (Opcional)")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        if st.form_submit_button("ENVIAR REPORTE"):
            if not foto or not nombre or not localidad or not direccion_exacta:
                st.error("Faltan datos.")
            else:
                res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                url_foto = res.json()["data"]["url"]
                sh.sheet1.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, "N/A", "N/A", localidad, direccion_exacta, tag, descripcion, url_foto, str(st.session_state.lat_sel).replace('.', ','), str(st.session_state.lon_sel).replace('.', ','), "Pendiente"])
                st.success("✅ ¡Enviado!")
                st.session_state.mostrar_form = False
                st.rerun()

# --- 6. VIDEO ---
st.divider()
c1, c2, c3 = st.columns([1, 1.8, 1])
with c2: 
    try: st.video("tutorial.mp4")
    except: pass

# --- 7. MAPA PRINCIPAL (AHORA ARRIBA DE NOVEDADES) ---
st.divider()
st.write("### 🌎 Mapa de Realidad Distrital")
m_p = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
try:
    rows = sh.sheet1.get_all_values()
    if len(rows) > 1:
        for r in rows[1:]:
            try:
                lt = float(str(r[9]).replace(',', '.'))
                ln = float(str(r[10]).replace(',', '.'))
                tag_rep = r[6]
                color = "#dc3545" if tag_rep in CATS_ROJAS else "#fd7e14" if tag_rep in CATS_NARANJAS else "#ffc107"
                txt_c = "white" if tag_rep in CATS_ROJAS else "black"
                pop = f"<div style='width:180px;'><h4 style='color:{color}; margin:0;'>{tag_rep}</h4><p style='font-size:12px;'>{r[5]}</p><img src='{r[8]}' style='width:100%; border-radius:5px;'></div>"
                icon = f'<div style="background-color:{color}; color:{txt_c}; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid {txt_c};">R</div>'
                folium.Marker([lt, ln], popup=folium.Popup(pop, max_width=250), icon=folium.DivIcon(html=icon)).add_to(m_p)
            except: continue
    st_folium(m_p, width="100%", height=500, key="mapa_final")
except: pass

# --- 8. NOVEDADES DE GESTIÓN (AHORA ABAJO DEL MAPA CON LINKS INTELIGENTES) ---
st.divider()
st.write("### 📰 Novedades y Soluciones")
try:
    sheet_nov = sh.worksheet("Novedades")
    novedades_data = sheet_nov.get_all_values()
    if len(novedades_data) > 1:
        for nov in reversed(novedades_data[1:]):
            fecha, titulo, contenido = nov[0], nov[1], nov[2]
            st.markdown(f"**{titulo}** — *{fecha}*")
            
            # Detectar si es un link
            if contenido.startswith("http"):
                t, d, i = obtener_vista_previa(contenido)
                if t:
                    with st.container():
                        st.markdown(f"""
                        <a href="{contenido}" target="_blank" style="text-decoration: none;">
                            <div style="border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background: #fff;">
                                {"<img src='"+i+"' style='width:100%; height:200px; object-fit:cover;'>" if i else ""}
                                <div style="padding: 10px;">
                                    <h5 style="margin:0; color:#28a745;">{t}</h5>
                                    <p style="font-size:13px; color:#555; margin:5px 0;">{d}</p>
                                    <small style="color:blue;">Ver publicación original ↗</small>
                                </div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)
                else:
                    st.link_button("Ver publicación externa", contenido)
            else:
                st.info(contenido)
            st.write("")
except: st.info("Próximamente novedades.")

# --- 9. PANEL DE CONTROL (ADMIN) ---
if es_admin:
    st.divider()
    st.header("📊 Panel de Gestión")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Vecinos", df['Nombre'].nunique())
    
    st.subheader("📝 Publicar Novedad Inteligente")
    with st.form("form_nov"):
        t_n = st.text_input("Título")
        c_n = st.text_area("Contenido (Texto o Link de Instagram/Noticia)")
        if st.form_submit_button("Publicar"):
            sh.worksheet("Novedades").append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), t_n, c_n])
            st.success("¡Publicado!")
            st.rerun()
