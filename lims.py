import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. CONEXIÓN ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Error de credenciales. Revisa los Secrets en Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title="LIMS RAM Nacional", layout="wide")

# --- 2. LISTAS DE OPCIONES ESTANDARIZADAS ---
provincias = [
    "Azuay", "Bolívar", "Cañar", "Carchi", "Chimborazo", "Cotopaxi", "El Oro", 
    "Esmeraldas", "Galápagos", "Guayas", "Imbabura", "Loja", "Los Ríos", 
    "Manabí", "Morona Santiago", "Napo", "Orellana", "Pastaza", "Pichincha", 
    "Santa Elena", "Santo Domingo de los Tsáchilas", "Sucumbíos", 
    "Tungurahua", "Zamora Chinchipe"
]

origenes = [
    "Granja", "Casa", "Laboratorio", "Mercado al aire libre", 
    "Tienda de mascotas", "Matadero", "Tienda de alimentos, puntos de venta", 
    "Hospital veterinario", "Clínica veterinaria", 
    "Hábitat natural (donde se originó/capturó el pez o el animal)", 
    "Desconocido", "Otro"
]

programas = ["Vigilancia", "Cuarentena", "Cliente Externo"]
especies = ["Aves", "Cerdos", "Bovinos"]
muestras = ["Hisopado", "Heces"]
bacterias = ["E. coli", "Salmonella spp."]
atbs_keys = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

# --- 3. INTERFAZ DE USUARIO ---
st.title("🔬 Sistema de Registro de Resistencia Bacteriana")
st.info("Complete el formulario para registrar los resultados del antibiograma en la nube.")

with st.form("formulario_lims"):
    st.subheader("📋 Información de la Muestra")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        origen_sel = st.selectbox("Origen", options=origenes)
    with col2:
        anio = st.number_input("Año", 2020, 2030, 2026)
    with col3:
        provincia_sel = st.selectbox("Provincia", options=provincias)
    with col4:
        programa_sel = st.selectbox("Programa", options=programas)
        
    col5, col6, col7 = st.columns(3)
    with col5:
        especie_sel = st.selectbox("Especie", options=especies)
    with col6:
        muestra_sel = st.selectbox("Tipo de Muestra", options=muestras)
    with col7:
        bacteria_sel = st.selectbox("Bacteria / Microorganismo", options=bacterias)

    st.markdown("---")
    st.subheader("🧪 Resultados (S / I / R)")
    
    # Cuadrícula para antibióticos
    cols_atb = st.columns(6)
    resultados_usuario = {}
    for i, atb in enumerate(atbs_keys):
        with cols_atb[i % 6]:
            resultados_usuario[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=f"sel_{atb}")

    st.markdown("<br>", unsafe_allow_html=True)
    enviar = st.form_submit_button("💾 GUARDAR REGISTRO EN SUPABASE")

    if enviar:
        # Preparamos los datos para la tabla 'registros_resistencia'
        datos_registro = {
            "origen": origen_sel,
            "año": anio,
            "provincia": provincia_sel,
            "programa": programa_sel,
            "especie": especie_sel,
            "tipo_de_muestra": muestra_sel,
            "bacteria": bacteria_sel,
            **resultados_usuario
        }
        
        try:
            supabase.table("registros_resistencia").insert(datos_registro).execute()
            st.success(f"✅ Registro guardado exitosamente: {bacteria_sel}")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error al conectar o guardar: {e}")

# --- 4. VISUALIZADOR DE DATOS ---
st.markdown("---")
st.subheader("📊 Historial de Registros")
if st.button("🔄 Actualizar Vista"):
    try:
        res = supabase.table("registros_resistencia").select("*").order('fecha_creacion', desc=True).execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        else:
            st.info("Aún no hay datos en la base de datos.")
    except Exception as e:
        st.error(f"No se pudieron cargar los datos: {e}")
