import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN Y CONEXIÓN A SUPABASE ---
SUPABASE_URL = 'https://iknwswwouxledkavyrwf.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlrbndzd3dvdXhsZWRrYXZ5cndmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2MDE4MTgsImV4cCI6MjA5MzE3NzgxOH0.CnHWCK78FGRASgnRX3dLI6r1Pw0rCEtJhfccCvHTqRI'
ADMIN_PASSWORD = 'resi_admin_2026'

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 2. CATEGORÍAS Y GRAVEDAD ---
CATS_ROJAS = ["Poste en riesgo de caída", "Hecho de inseguridad", "Riesgo de derrumbe", "Árbol caído", "Abuso de autoridad", "Plagas", "Fuga de gas", "Microbasural clandestino"]
CATS_NARANJAS = ["Contenedor desbordado", "Corte de luz", "Cloaca colapsada", "Zanja tapada", "Pérdida de agua", "Corte de agua", "Parada/Refugio vandalizado"]
CATS_AMARILLAS = ["Bache", "Vereda rota", "Luminaria con problemas", "Auto mal estacionado", "Falta rampa", "Poda mal hecha", "Problemas de tránsito", "Obra mal hecha", "Mobiliario urbano dañado", "Otros"]

todas_las_categorias = CATS_ROJAS + CATS_NARANJAS + CATS_AMARILLAS
todas_las_categorias.remove("Bache")
todas_las_categorias.remove("Otros")
LISTA_CATEGORIAS = ["Bache"] + sorted(todas_las_categorias) + ["Otros"]

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

# --- 3. ESTILOS CSS ---
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
    </style>
""", unsafe_allow_html=True)

# Estados de sesión
if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False
if 'mostrar_comunidad' not in st.session_state: st.session_state.mostrar_comunidad = False

# --- 4. BARRA LATERAL (ADMIN) ---
with st.sidebar:
    st.title("🛠️ Gestión ReSI")
    pwd_input = st.text_input("Acceso Administrador", type="password")
    es_admin = (pwd_input == ADMIN_PASSWORD)

# --- 5. CABECERA, SLOGAN Y BOTÓN ---
col_izq, col_centro, col_der = st.columns([1, 5, 1])
with col_centro:
    try: st.image("logo_resi.png", use_container_width=True)
    except: st.header("ReSI - Realidad San Isidro")
    st.markdown('<p class="slogan">Una herramienta para que el intendente y sus funcionarios se ubiquen en el mapa</p>', unsafe_allow_html=True)
    
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True
    
    st.markdown('<p class="synthetic-list">Podés reportar problemas de: baches, veredas, luminarias, seguridad, higiene urbana, arbolado, tránsito y accesibilidad.</p>', unsafe_allow_html=True)

# --- 6. FORMULARIO DE REPORTE ---
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
                try:
                    res_img = requests.post(f"https://api.imgbb.com/1/upload?key={st.secrets['IMGBB_API_KEY']}", files={"image": foto.getvalue()})
                    url_foto = res_img.json()["data"]["url"]
                    lat_s = str(st.session_state.lat_sel).replace('.', ',')
                    lon_s = str(st.session_state.lon_sel).replace('.', ',')
                    
                    # Envío a Supabase
                    nuevo_reporte = {
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "nombre": nombre, "email": "N/A", "tel": "N/A",
                        "localidad": localidad, "direccion_exacta": direccion,
                        "tag": tag, "descripcion": descripcion, "url_foto": url_foto,
                        "lat": lat_s, "lon": lon_s, "estado": "Pendiente"
                    }
                    supabase.table("reportes").insert(nuevo_reporte).execute()
                    
                    st.success("✅ ¡Reporte enviado!")
                    st.session_state.mostrar_form = False
                    st.rerun()
                except Exception as e:
                    st.error("Error al enviar el reporte. Por favor intentá de nuevo.")

# --- 7. VIDEO TUTORIAL ---
st.divider()
st.write("### 🎥 Tutorial:")
c1, c2, c3 = st.columns([1, 1.8, 1])
with c2: 
    try: st.video("tutorial.mp4")
    except: pass

# EXTRAER DATOS DE REPORTES PARA MAPA Y PANEL
reportes_data = []
try:
    res_reportes = supabase.table("reportes").select("*").execute()
    reportes_data = res_reportes.data
except:
    pass

# --- 8. MAPA DE REPORTES ---
st.divider()
st.write("### 🌎 Mapa de Reportes")
m_p = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
if reportes_data:
    for r in reportes_data:
        try:
            lt, ln = float(str(r['lat']).replace(',', '.')), float(str(r['lon']).replace(',', '.'))
            tag_rep = r['tag']
            color = "#dc3545" if tag_rep in CATS_ROJAS else "#fd7e14" if tag_rep in CATS_NARANJAS else "#ffc107"
            txt_c = "white" if tag_rep in CATS_ROJAS else "black"
            pop = f"<div style='width:180px;'><h4 style='color:{color}; margin:0;'>{tag_rep}</h4><p style='font-size:12px;'>{r['direccion_exacta']}</p><img src='{r['url_foto']}' style='width:100%; border-radius:5px;'></div>"
            icon = f'<div style="background-color:{color}; color:{txt_c}; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid {txt_c};">R</div>'
            folium.Marker([lt, ln], popup=folium.Popup(pop, max_width=250), icon=folium.DivIcon(html=icon)).add_to(m_p)
        except: continue
st_folium(m_p, width="100%", height=500, key="mapa_final")

# --- 9. NOVEDADES Y SOLUCIONES ---
st.divider()
st.write("### 📰 Novedades y Soluciones")
try:
    res_nov = supabase.table("novedades").select("*").order("id", desc=True).execute()
    if res_nov.data:
        for nov in res_nov.data:
            fecha, titulo, contenido = nov['fecha'], nov['titulo'], nov['contenido']
            st.markdown(f"**{titulo}** — *{fecha}*")
            if contenido.startswith("http"):
                t, d, i = obtener_vista_previa(contenido)
                if t:
                    st.markdown(f'<a href="{contenido}" target="_blank" style="text-decoration: none; color: black;"><div style="border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background: #fff; margin-bottom: 20px;">' + (f"<img src='{i}' style='width:100%; height:auto; display:block;'>" if i else "") + f'<div style="padding: 10px;"><h5 style="margin:0; color:#28a745;">{t}</h5><p style="font-size:13px; color:#555; margin:5px 0;">{d}</p></div></div></a>', unsafe_allow_html=True)
                else: st.link_button("Ver publicación", contenido)
            else: st.info(contenido)
    else:
        st.info("Próximamente novedades de gestión.")
except: pass

# --- 10. SECCIÓN COMUNIDAD ReSI ---
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
                nueva_suscripcion = {
                    "nombre": c_nom, "localidad": c_loc, "fecha_nacimiento": c_fec,
                    "email": c_mail, "telefono": c_tel,
                    "fecha_suscripcion": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                supabase.table("comunidad").insert(nueva_suscripcion).execute()
                st.success("¡Gracias por sumarte! Tus datos fueron registrados.")
                st.session_state.mostrar_comunidad = False
            except:
                st.error("Error al procesar la suscripción.")

# --- 11. PANEL DE ADMINISTRADOR (ESTADÍSTICAS) ---
if es_admin:
    st.divider()
    st.header("📊 Tablero de Gestión ReSI")
    
    if reportes_data:
        df = pd.DataFrame(reportes_data)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📌 Total Reportes", len(df))
        if 'nombre' in df.columns: c2.metric("👥 Vecinos", df['nombre'].nunique())
        if 'estado' in df.columns: c3.metric("⏳ Pendientes", len(df[df['estado'] == 'Pendiente']))
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Categorías")
            if 'tag' in df.columns: st.bar_chart(df['tag'].value_counts())
        with col_b:
            st.subheader("Localidades")
            if 'localidad' in df.columns: st.bar_chart(df['localidad'].value_counts())

        st.subheader("Gravedad por Color")
        def asignar_color_est(t):
            if t in CATS_ROJAS: return "1. 🔴 Crítico"
            if t in CATS_NARANJAS: return "2. 🟠 Alto"
            if t in CATS_AMARILLAS: return "3. 🟡 Moderado"
            return "4. 🟢 Otros"
        if 'tag' in df.columns:
            df['Gravedad'] = df['tag'].apply(asignar_color_est)
            st.bar_chart(df['Gravedad'].value_counts().sort_index())
    else:
        st.info("Aún no hay reportes para analizar.")

    st.subheader("📝 Publicar Novedad")
    with st.form("form_nov"):
        t_n = st.text_input("Título")
        c_n = st.text_area("Contenido o Link")
        if st.form_submit_button("Publicar"):
            try:
                supabase.table("novedades").insert({
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "titulo": t_n, "contenido": c_n
                }).execute()
                st.success("¡Publicado!")
                st.rerun()
            except:
                st.error("Error al publicar la novedad.")
