import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. CONEXIÓN ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Error de credenciales.")
    st.stop()

st.set_page_config(page_title="LIMS RAM Nacional", layout="wide")

# --- 2. LISTAS DE OPCIONES ---
provincias = [
    "Azuay", "Bolívar", "Cañar", "Carchi", "Chimborazo", "Cotopaxi", "El Oro", 
    "Esmeraldas", "Galápagos", "Guayas", "Imbabura", "Loja", "Los Ríos", 
    "Manabí", "Morona Santiago", "Napo", "Orellana", "Pastaza", "Pichincha", 
    "Santa Elena", "Santo Domingo de los Tsáchilas", "Sucumbíos", 
    "Tungurahua", "Zamora Chinchipe"
]

especies = ["Aves", "Cerdos", "Bovinos"]
bacterias = ["E. coli", "Salmonella spp."]
atbs_keys = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

# --- 3. INTERFAZ ---
st.title("🔬 Registro de Resistencia Bacteriana")

with st.form("formulario_lims"):
    st.subheader("📋 Datos de Identificación")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        origen = st.text_input("Origen")
    with col2:
        anio = st.number_input("Año", 2020, 2030, 2026)
    with col3:
        # CAMBIO: Ahora es un selector
        provincia = st.selectbox("Provincia", options=provincias)
    with col4:
        programa = st.text_input("Programa")
        
    col5, col6, col7 = st.columns(3)
    with col5:
        # CAMBIO: Ahora es un selector
        especie = st.selectbox("Especie", options=especies)
    with col6:
        tipo_muestra = st.text_input("Tipo de Muestra")
    with col7:
        # CAMBIO: Ahora es un selector
        bacteria = st.selectbox("Bacteria / Microorganismo", options=bacterias)

    st.markdown("---")
    st.subheader("🧪 Resultados (S / I / R)")
    
    cols_atb = st.columns(6)
    resultados_usuario = {}
    for i, atb in enumerate(atbs_keys):
        with cols_atb[i % 6]:
            resultados_usuario[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=f"sel_{atb}")

    enviar = st.form_submit_button("💾 GUARDAR REGISTRO")

    if enviar:
        datos_registro = {
            "origen": origen,
            "año": anio,
            "provincia": provincia,
            "programa": programa,
            "especie": especie,
            "tipo_de_muestra": tipo_muestra,
            "bacteria": bacteria,
            **resultados_usuario
        }
        
        try:
            supabase.table("registros_resistencia").insert(datos_registro).execute()
            st.success(f"✅ Guardado: {bacteria} en {provincia}")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")

# --- 4. VISUALIZACIÓN ---
st.markdown("---")
if st.button("📊 Ver Datos"):
    res = supabase.table("registros_resistencia").select("*").execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data))
