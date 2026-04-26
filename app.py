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

# --- 1. CONFIGURACIÓN Y CATEGORÍAS AMPLIADAS ---
SPREADSHEET_ID = '1fa8cD0HVD0lzoc5aWJzYSFuLJRpKwbsp3azF82hLReo'
ADMIN_PASSWORD = 'resi_admin_2026'

# Gravedad por colores (Nueva escala solicitada)
CATS_ROJAS = ["Poste en riesgo de caída", "Hecho de inseguridad", "Riesgo de derrumbe", "Árbol caído", "Abuso de autoridad", "Plagas", "Fuga de gas", "Microbasural clandestino"]
CATS_NARANJAS = ["Contenedor desbordado", "Corte de luz", "Cloaca colapsada", "Zanja tapada", "Pérdida de agua", "Corte de agua", "Parada/Refugio vandalizado"]
CATS_AMARILLAS = ["Bache", "Vereda rota", "Luminaria con problemas", "Auto mal estacionado", "Falta rampa", "Poda mal hecha", "Problemas de tránsito", "Obra mal hecha", "Mobiliario urbano dañado", "Otros"]

LISTA_CATEGORIAS = sorted(CATS_ROJAS + CATS_NARANJAS + CATS_AMARILLAS)

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
        desc = desc["content"][:150] + "..." if desc else "Hacé clic para ver más detalles."
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
        color: #444; margin-top: -15px; margin-bottom: 10px;
    }
    .synthetic-list {
        text-align: center; font-size: 14px; color: #666; margin-bottom: 25px;
    }
    .comunidad-box {
        text-align: center; background-color: #e9ecef; padding: 30px; 
        border-radius: 15px; margin-top: 40px; border: 2px dashed #28a745;
    }
    .noticia-box {
        background-color: #ffffff; border: 1px solid #ddd;
        padding: 15px; border-radius: 10px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False
if 'mostrar_comunidad' not in st.session_state: st.session_state.mostrar_comunidad = False

try:
    creds = Credentials.from_service_account_info(json.loads(st.secrets["GCP_CREDS"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sh = gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
except:
    st.error("Conexión interrumpida con la base de datos.")

# --- 3. BARRA LATERAL (ADMIN) ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password")
    es_admin = (pwd_input == ADMIN_PASSWORD)

# --- 4. CABECERA, SLOGAN Y BOTÓN ---
col_izq, col_centro, col_der = st.columns([1, 45, 1])
with col_centro:
    try: st.image("logo_resi.png", use_container_width=True)
    except: st.header("ReSI - Realidad San Isidro")
    st.markdown('<p class="slogan">Una herramienta para que el intendente y sus funcionarios se ubiquen en el mapa</p>', unsafe_allow_html=True)
    
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True
    
    st.markdown('<p class="synthetic-list">Podés reportar problemas de: baches, veredas, luminarias, seguridad, higiene urbana, arbolado, tránsito y accesibilidad.</p>', unsafe_allow_html=True)

# --- 5. FORMULARIO DE REPORTE ---
if st.session_state.mostrar_form:
    st.markdown("---")
    st.write("### 📍 Ubicación exacta")
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
        localidad = st.selectbox("Localidad", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        direccion = st.text_input("Dirección (Calle y altura)")
        descripcion = st.text_area("Descripción (Opcional)")
        foto = st.file_uploader("Subir Foto", type=["jpg", "png", "jpeg"])
        if st.form_submit_button("ENVIAR REPORTE"):
            if not foto or not nombre or not direccion:
                st.error("Completá los campos obligatorios.")
            else:
                res = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                url_foto = res.json()["data"]["url"]
                lat_s = str(st.session_state.lat_sel).replace('.', ',')
                lon_s = str(st.session_state.lon_sel).replace('.', ',')
                sh.sheet1.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, "N/A", "N/A", localidad, direccion, tag, descripcion, url_foto, lat_s, lon_s, "Pendiente"])
                st.success("✅ ¡Reporte enviado!")
                st.session_state.mostrar_form = False
                st.rerun()

# --- 6. VIDEO TUTORIAL ---
st.divider()
st.write("### 🎥 Tutorial:")
c1, c2, c3 = st.columns([1, 1.8, 1])
with c2: 
    try: st.video("tutorial.mp4")
    except: pass

# --- 7. MAPA DE REPORTES ---
st.divider()
st.write("### 🌎 Mapa de Reportes")
m_p = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
try:
    rows = sh.sheet1.get_all_values()
    if len(rows) > 1:
        for r in rows[1:]:
            try:
                lt, ln = float(str(r[9]).replace(',', '.')), float(str(r[10]).replace(',', '.'))
                color = "#dc3545" if r[6] in CATS_ROJAS else "#fd7e14" if r[6] in CATS_NARANJAS else "#ffc107"
                txt_c = "white" if r[6] in CATS_ROJAS else "black"
                pop = f"<div style='width:180px;'><h4 style='color:{color}; margin:0;'>{r[6]}</h4><p style='font-size:12px;'>{r[5]}</p><img src='{r[8]}' style='width:100%; border-radius:5px;'></div>"
                icon = f'<div style="background-color:{color}; color:{txt_c}; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid {txt_c};">R</div>'
                folium.Marker([lt, ln], popup=folium.Popup(pop, max_width=250), icon=folium.DivIcon(html=icon)).add_to(m_p)
            except: continue
    st_folium(m_p, width="100%", height=500, key="mapa_final")
except: pass

# --- 8. NOVEDADES Y SOLUCIONES ---
st.divider()
st.write("### 📰 Novedades y Soluciones")
try:
    sheet_nov = sh.worksheet("Novedades")
    nov_data = sheet_nov.get_all_values()
    if len(nov_data) > 1:
        for nov in reversed(nov_data[1:]):
            fecha, titulo, contenido = nov[0], nov[1], nov[2]
            st.markdown(f"**{titulo}** — *{fecha}*")
            if contenido.startswith("http"):
                t, d, i = obtener_vista_previa(contenido)
                if t:
                    st.markdown(f'<a href="{contenido}" target="_blank" style="text-decoration: none; color: black;"><div style="border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background: #fff; margin-bottom: 20px;">' + (f"<img src='{i}' style='width:100%; height:180px; object-fit:cover;'>" if i else "") + f'<div style="padding: 10px;"><h5 style="margin:0; color:#28a745;">{t}</h5><p style="font-size:13px; color:#555; margin:5px 0;">{d}</p></div></div></a>', unsafe_allow_html=True)
                else: st.link_button("Ver publicación", contenido)
            else: st.info(contenido)
except: pass

# --- 9. SECCIÓN COMUNIDAD ReSI ---
st.markdown("""
    <div class="comunidad-box">
        <h3 style="color: #28a745; margin-bottom: 10px;">SUMATE A LA COMUNIDAD ReSI</h3>
        <p style="font-size: 16px; color: #444;">PARA RECIBIR INFORMACIÓN IMPORTANTE PARA QUE RESCATEMOS SAN ISIDRO</p>
    </div>
""", unsafe_allow_html=True)

c_com, c_btn, c_com2 = st.columns([1, 1.5, 1])
with c_btn:
    if st.button("SUSCRIBIRME", use_container_width=True):
        st.session_state.mostrar_comunidad = not st.session_state.mostrar_comunidad

if st.session_state.mostrar_comunidad:
    with st.form("form_comunidad", clear_on_submit=True):
        st.write("### 📋 Datos de suscripción (Opcionales)")
        c_nom = st.text_input("Nombre")
        c_loc = st.selectbox("Localidad", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        c_fec = st.text_input("Fecha de Nacimiento (DD/MM/AAAA)")
        c_mail = st.text_input("Email")
        c_tel = st.text_input("Teléfono")
        if st.form_submit_button("UNIRME A LA COMUNIDAD"):
            try:
                sheet_com = sh.worksheet("Comunidad")
                sheet_com.append_row([c_nom, c_loc, c_fec, c_mail, c_tel, datetime.now().strftime("%d/%m/%Y %H:%M")])
                st.success("¡Gracias por sumarte, Nico! Tus datos fueron registrados.")
                st.session_state.mostrar_comunidad = False
            except:
                st.error("Error: Asegurate de tener una pestaña llamada 'Comunidad' en tu Excel.")

# --- 10. PANEL DE ADMINISTRADOR (ESTADÍSTICAS RESTAURADAS) ---
if es_admin:
    st.divider()
    st.header("📊 Tablero de Gestión ReSI")
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df.columns = [c.strip() for c in df.columns]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 Total Reportes", len(df))
    if 'Nombre' in df.columns: c2.metric("👥 Vecinos", df['Nombre'].nunique())
    if 'Estado' in df.columns: c3.metric("⏳ Pendientes", len(df[df['Estado'] == 'Pendiente']))
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Categorías")
        if 'Tag' in df.columns: st.bar_chart(df['Tag'].value_counts())
    with col_b:
        st.subheader("Localidades")
        if 'Localidad' in df.columns: st.bar_chart(df['Localidad'].value_counts())

    st.subheader("Gravedad por Color")
    def asignar_color_est(t):
        if t in CATS_ROJAS: return "1. 🔴 Crítico"
        if t in CATS_NARANJAS: return "2. 🟠 Alto"
        if t in CATS_AMARILLAS: return "3. 🟡 Moderado"
        return "4. 🟢 Otros"
    df['Gravedad'] = df['Tag'].apply(asignar_color_est)
    st.bar_chart(df['Gravedad'].value_counts().sort_index())

    st.subheader("📝 Publicar Novedad")
    with st.form("form_nov_v28"):
        t_n = st.text_input("Título")
        c_n = st.text_area("Contenido o Link")
        if st.form_submit_button("Publicar"):
            sh.worksheet("Novedades").append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), t_n, c_n])
            st.success("¡Publicado!")
            st.rerun()
