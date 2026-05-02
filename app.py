import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN GITHUB (COMPLETÁ CON TUS DATOS) ---
USUARIO_GH = "nabratte92" 
REPO_GH = "resi-app"

# URLs de recursos
URL_BASE = f"https://raw.githubusercontent.com/{USUARIO_GH}/{REPO_GH}/main"
IMG_LOGO_WALLY = f"{URL_BASE}/Logo%20buscando%20ramon.png"
IMG_MAPA_WALLY = f"{URL_BASE}/Mapa%20buscando%20ramon.png"
IMG_AVATAR = f"{URL_BASE}/Avatar%20buscando%20ramon.png"
AUDIO_RISA = f"{URL_BASE}/Risa%20buscando%20ramon.mp3"
IMG_COMUNIDAD = f"{URL_BASE}/Comunidad%20resi.png"

# --- METADATOS PARA WHATSAPP (OPEN GRAPH) ---
URL_PREVIEW = f"{URL_BASE}/preview.png"
st.markdown(
    f"""
    <head>
        <meta property="og:title" content="ReSI - Rescatemos San Isidro">
        <meta property="og:description" content="Plataforma vecinal para reportar baches, luminarias y problemas de infraestructura.">
        <meta property="og:image" content="{URL_PREVIEW}">
        <meta property="og:url" content="https://rescatemossanisidro.com.ar">
        <meta property="og:type" content="website">
        <meta name="twitter:card" content="summary_large_image">
    </head>
    """,
    unsafe_allow_html=True
)

# --- 2. CONEXIÓN A SUPABASE ---
SUPABASE_URL = 'https://iknwswwouxledkavyrwf.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlrbndzd3dvdXhsZWRrYXZ5cndmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2MDE4MTgsImV4cCI6MjA5MzE3NzgxOH0.CnHWCK78FGRASgnRX3dLI6r1Pw0rCEtJhfccCvHTqRI'
ADMIN_PASSWORD = 'resi_admin_2026'

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- 3. CATEGORÍAS Y GRAVEDAD ---
CATS_ROJAS = ["Poste en riesgo de caída", "Hecho de inseguridad", "Riesgo de derrumbe", "Árbol caído", "Abuso de autoridad", "Plagas", "Fuga de gas", "Microbasural clandestino"]
CATS_NARANJAS = ["Contenedor desbordado", "Corte de luz", "Cloaca colapsada", "Zanja tapada", "Pérdida de agua", "Corte de agua", "Parada/Refugio vandalizado"]
CATS_AMARILLAS = ["Bache", "Vereda rota", "Luminaria con problemas", "Auto mal estacionado", "Falta rampa", "Poda mal hecha", "Problemas de tránsito", "Obra mal hecha", "Mobiliario urbano dañado", "Otros"]

todas_las_categorias = CATS_ROJAS + CATS_NARANJAS + CATS_AMARILLAS
todas_las_categorias.remove("Bache")
todas_las_categorias.remove("Otros")
LISTA_CATEGORIAS = ["Bache"] + sorted(todas_las_categorias) + ["Otros"]

st.set_page_config(page_title="ReSI - Rescatemos San Isidro", page_icon="📍", layout="centered")

# --- FUNCIÓN VISTA PREVIA ---
def obtener_vista_previa(url):
    try:
        header = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=header, timeout=5)
        soup = BeautifulSoup(r.content, 'html.parser')
        titulo = soup.find("meta", property="og:title")
        titulo = titulo["content"] if titulo else soup.title.string if soup.title else "Noticia"
        desc = soup.find("meta", property="og:description")
        desc = desc["content"][:150] + "..." if desc else "Hacé clic para ver más."
        img = soup.find("meta", property="og:image")
        img_url = img["content"] if img else None
        return titulo, desc, img_url
    except:
        return None, None, None

# --- 4. ESTILOS CSS ---
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
    .slogan { text-align: center; font-size: 19px; font-style: italic; color: #444; margin-top: -15px; margin-bottom: 10px; }
    .synthetic-list { text-align: center; font-size: 14px; color: #666; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

if 'lat_sel' not in st.session_state: st.session_state.lat_sel = -34.4746
if 'lon_sel' not in st.session_state: st.session_state.lon_sel = -58.5132
if 'mostrar_form' not in st.session_state: st.session_state.mostrar_form = False
if 'mostrar_comunidad' not in st.session_state: st.session_state.mostrar_comunidad = False

# --- 5. CABECERA Y BOTÓN DE INICIO ---
col_izq, col_centro, col_der = st.columns([1, 65, 1])
with col_centro:
    try: st.image("logo_resi.png", use_container_width=True)
    except: st.header("ReSI - Realidad San Isidro")
    st.markdown('<p class="slogan">Una herramienta para que el intendente y sus funcionarios se ubiquen en el mapa</p>', unsafe_allow_html=True)
    if st.button("🚨 INICIAR REPORTE", use_container_width=True):
        st.session_state.mostrar_form = True
    st.markdown('<p class="synthetic-list">Baches, veredas, luminarias, seguridad, higiene, arbolado y tránsito.</p>', unsafe_allow_html=True)

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
        email_rep = st.text_input("Email (Opcional)")
        tel_rep = st.text_input("Teléfono (Opcional)")
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
                    
                    nuevo_reporte = {
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "nombre": nombre, "email": email_rep, "tel": tel_rep,
                        "localidad": localidad, "direccion_exacta": direccion,
                        "tag": tag, "descripcion": descripcion, "url_foto": url_foto,
                        "lat": lat_s, "lon": lon_s, "estado": "Pendiente"
                    }
                    supabase.table("reportes").insert(nuevo_reporte).execute()
                    st.success("✅ ¡Reporte enviado!")
                    st.session_state.mostrar_form = False
                    st.rerun()
                except: st.error("Error al enviar.")

# --- 7. VIDEO TUTORIAL ---
st.divider()
st.write("### 🎥 Tutorial:")
c1, c2, c3 = st.columns([1, 1.8, 1])
with c2: 
    try: st.video("tutorial.mp4")
    except: pass

# --- 8. MAPA DE REPORTES Y LÓGICA DE ADHESIONES ---
st.divider()
st.write("### 🌎 Mapa de Reportes")
reportes_data = []
try:
    res_reportes = supabase.table("reportes").select("*").execute()
    reportes_data = res_reportes.data
except: pass

m_p = folium.Map(location=[-34.4746, -58.5132], zoom_start=13)
df_todos = pd.DataFrame()
df_para_el_mapa = pd.DataFrame()

if reportes_data:
    df_todos = pd.DataFrame(reportes_data)
    
    if 'id_reporte_original' not in df_todos.columns:
        df_todos['id_reporte_original'] = None
        
    df_para_el_mapa = df_todos[df_todos['id_reporte_original'].isnull()].copy()

    # Preparamos las coordenadas para la lógica de clics (Infalible)
    df_para_el_mapa['lat_float'] = df_para_el_mapa['lat'].astype(str).str.replace(',', '.').astype(float).round(4)
    df_para_el_mapa['lon_float'] = df_para_el_mapa['lon'].astype(str).str.replace(',', '.').astype(float).round(4)

    for index, r in df_para_el_mapa.iterrows():
        try:
            lt, ln = float(str(r['lat']).replace(',', '.')), float(str(r['lon']).replace(',', '.'))
            color = "#dc3545" if r['tag'] in CATS_ROJAS else "#fd7e14" if r['tag'] in CATS_NARANJAS else "#ffc107"
            txt_c = "white" if r['tag'] in CATS_ROJAS else "black"
            
            # Calculamos cuántas personas apoyaron
            adherentes_locales = df_todos[df_todos['id_reporte_original'] == r['id']]
            total_v = 1 + len(adherentes_locales)
            
            # LÓGICA GRAMATICAL: "vecino" vs "vecinos"
            palabra_vecino = "vecino" if total_v == 1 else "vecinos"
            texto_vecinos = f"Esto fue reportado por: {total_v} {palabra_vecino}"
            
            pop_html = f"""
            <div style='width:180px;'>
                <h4 style='color:{color}; margin:0;'>{r['tag']}</h4>
                <p style='font-size:12px; margin:2px 0 5px 0;'>{r['direccion_exacta']}</p>
                <p style='font-size:12px; margin-top:0px; font-weight:bold; color:#0056b3;'>{texto_vecinos}</p>
                <img src='{r['url_foto']}' style='width:100%; border-radius:5px;'>
            </div>
            """
            
            icon = f'<div style="background-color:{color}; color:{txt_c}; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid {txt_c};">R</div>'
            
            folium.Marker(
                [lt, ln], 
                popup=folium.Popup(pop_html, max_width=250), 
                icon=folium.DivIcon(html=icon)
            ).add_to(m_p)
        except: continue

out_mapa = st_folium(m_p, width="100%", height=500, key="mapa_final")

# --- LÓGICA DE ADHESIÓN (POR COORDENADAS) ---
if 'modo_adhesion' not in st.session_state: 
    st.session_state.modo_adhesion = False

clicked_obj = out_mapa.get("last_object_clicked") if out_mapa else None

if clicked_obj:
    # Capturamos la coordenada exacta que tocó el usuario y la redondeamos a 4 decimales
    lat_c = round(float(clicked_obj["lat"]), 4)
    lon_c = round(float(clicked_obj["lng"]), 4)
    
    # Buscamos qué reporte original coincide con esas coordenadas exactas
    padres_match = df_para_el_mapa[
        (df_para_el_mapa['lat_float'] == lat_c) & 
        (df_para_el_mapa['lon_float'] == lon_c)
    ]
    
    if not padres_match.empty:
        reporte_padre = padres_match.iloc[0]
        
        st.markdown("---")
        
        if not st.session_state.modo_adhesion:
            st.info(f"📍 **Reporte seleccionado:** {reporte_padre.get('tag', '')} en {reporte_padre.get('direccion_exacta', '')}")
            
            if st.button("🙋‍♂️ Yo también reclamo soluciones para esto", use_container_width=True):
                st.session_state.modo_adhesion = True
                st.rerun()
        else:
            st.write(f"#### ➕ Sumar mi reclamo")
            st.warning("Dejanos tus datos para respaldar este pedido. No tenés que volver a cargar foto ni ubicación.")
            
            with st.form("form_nueva_fila_adhesion"):
                nombre_adh = st.text_input("Nombre Completo (Obligatorio)")
                email_adh = st.text_input("Email (Opcional)")
                tel_adh = st.text_input("Teléfono (Opcional)")
                descripcion_adh = st.text_area("Comentario adicional (Opcional)")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_adh = st.form_submit_button("Confirmar mi apoyo")
                with col_btn2:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.modo_adhesion = False
                        st.rerun()
                
                if submit_adh:
                    if not nombre_adh:
                        st.error("Por favor, completá tu nombre.")
                    else:
                        nueva_adhesion = {
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "nombre": nombre_adh,
                            "email": email_adh,
                            "tel": tel_adh,
                            "descripcion": descripcion_adh,
                            "tag": reporte_padre.get('tag', ''),
                            "direccion_exacta": reporte_padre.get('direccion_exacta', ''),
                            "localidad": reporte_padre.get('localidad', ''),
                            "lat": reporte_padre.get('lat', ''),
                            "lon": reporte_padre.get('lon', ''),
                            "url_foto": reporte_padre.get('url_foto', ''),
                            "estado": "Pendiente",
                            "id_reporte_original": int(reporte_padre['id'])
                        }
                        try:
                            supabase.table("reportes").insert(nueva_adhesion).execute()
                            st.session_state.modo_adhesion = False
                            st.success("¡Te sumaste al reclamo con éxito! Actualizando mapa...")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Hubo un error al registrar: {e}")
else:
    st.session_state.modo_adhesion = False

# --- 9. NOVEDADES ---
st.divider()
st.write("### 📰 Novedades y Soluciones")
try:
    res_nov = supabase.table("novedades").select("*").order("id", desc=True).execute()
    if res_nov.data:
        for nov in res_nov.data:
            st.markdown(f"**{nov['titulo']}** — *{nov['fecha']}*")
            if nov['contenido'].startswith("http"):
                t, d, i = obtener_vista_previa(nov['contenido'])
                if t:
                    st.markdown(f'<a href="{nov["contenido"]}" target="_blank" style="text-decoration: none; color: black;"><div style="border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background: #fff; margin-bottom: 20px;">' + (f"<img src='{i}' style='width:100%; height:auto; display:block;'>" if i else "") + f'<div style="padding: 10px;"><h5 style="margin:0; color:#28a745;">{t}</h5><p style="font-size:13px; color:#555; margin:5px 0;">{d}</p></div></div></a>', unsafe_allow_html=True)
                else: st.link_button("Ver publicación", nov['contenido'])
            else: st.info(nov['contenido'])
except: pass

# --- 10. COMUNIDAD ---
st.markdown(f"""
    <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
        <img src="{IMG_COMUNIDAD}" style="max-width: 100%; height: auto; border-radius: 15px;" alt="Comunidad ReSI">
    </div>
""", unsafe_allow_html=True)

c_com, c_btn, c_com2 = st.columns([1, 1.5, 1])
with c_btn:
    if st.button("SUSCRIBIRME", use_container_width=True):
        st.session_state.mostrar_comunidad = not st.session_state.mostrar_comunidad

if st.session_state.mostrar_comunidad:
    with st.form("form_comunidad", clear_on_submit=True):
        c_nom = st.text_input("Nombre")
        c_loc = st.selectbox("Localidad", ["San Isidro", "Acassuso", "Beccar", "Boulogne", "Martínez", "Villa Adelina"])
        c_fec = st.text_input("Fecha de Nacimiento (DD/MM/AAAA)")
        c_mail = st.text_input("Email")
        c_tel = st.text_input("Teléfono")
        if st.form_submit_button("UNIRME A LA COMUNIDAD"):
            try:
                supabase.table("comunidad").insert({
                    "nombre": c_nom, 
                    "localidad": c_loc, 
                    "fecha_nacimiento": c_fec, 
                    "email": c_mail, 
                    "telefono": c_tel, 
                    "fecha_suscripcion": datetime.now().strftime("%d/%m/%Y %H:%M")
                }).execute()
                st.success("¡Gracias por sumarte!")
                st.session_state.mostrar_comunidad = False
                st.rerun()
            except: 
                st.error("Error al suscribirse.")

# --- 11. BUSCANDO A RAMÓN ---
st.divider()

st.write("### Busquemos a Ramón, si lo encontrás clickeá sobre él para ver qué hace: ¿Se pondrá a trabajar?")

codigo_minijuego = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    .contenedor-juego {{ position: relative; width: 100%; max-width: 800px; margin: 0 auto; border: 5px solid #28a745; border-radius: 15px; overflow: hidden; background-color: #fff; }}
    .logo-wally {{ width: 100%; display: block; border-bottom: 3px solid #28a745; }}
    .mapa-fondo {{ width: 100%; display: block; }}
    #ramon-avatar {{ position: absolute; top: 75%; left: 22%; width: 22px; cursor: pointer; z-index: 10; filter: brightness(0.9); transition: all 0.5s ease; }}
</style>
</head>
<body>
<div class="contenedor-juego">
    <img src="{IMG_LOGO_WALLY}" class="logo-wally">
    <div style="position: relative;">
        <img src="{IMG_MAPA_WALLY}" class="mapa-fondo">
        <img id="ramon-avatar" src="{IMG_AVATAR}" onclick="reir()">
    </div>
    <audio id="sonido-risa" src="{AUDIO_RISA}"></audio>
</div>
<script>
    function reir() {{
        var audio = document.getElementById("sonido-risa");
        audio.play();
        var avatar = document.getElementById("ramon-avatar");
        avatar.style.width = "180px"; 
        avatar.style.top = "50%"; 
        avatar.style.left = "50%"; 
        avatar.style.transform = "translate(-50%, -50%)"; 
        avatar.style.zIndex = "100"; 
        avatar.style.filter = "brightness(1.0)"; 
        avatar.style.backgroundColor = "transparent";
        avatar.style.border = "none";
        avatar.style.boxShadow = "none";
    }}
</script>
</body>
</html>
"""
components.html(codigo_minijuego, height=650)

# --- 12. ADMIN SECRETO ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
col_admin1, col_admin2, col_admin3 = st.columns([4, 1, 4])
with col_admin2:
    # La casilla de verificación secreta al fondo
    mostrar_admin = st.checkbox("v1.0", value=False)

if mostrar_admin:
    st.divider()
    pwd_input = st.text_input("Clave de acceso", type="password")
    es_admin = (pwd_input == ADMIN_PASSWORD)

    if es_admin:
        st.header("📊 Tablero de Gestión")
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
                
        st.subheader("📝 Publicar Novedad")
        with st.form("form_nov"):
            t_n = st.text_input("Título")
            c_n = st.text_area("Contenido/Link")
            if st.form_submit_button("Publicar"):
                try:
                    supabase.table("novedades").insert({"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "titulo": t_n, "contenido": c_n}).execute()
                    st.success("Publicado")
                    st.rerun()
                except: st.error("Error")
