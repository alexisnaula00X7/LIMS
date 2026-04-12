import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. CONEXIÓN (FORMA CORRECTA Y SEGURA) ---
try:
    # st.secrets busca la ETIQUETA, no el enlace.
    # El enlace real lo pondrás en el panel de Streamlit Cloud.
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Error de credenciales: No se encuentran las etiquetas SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

st.set_page_config(page_title="LIMS RAM", layout="wide")

# Lista de antibióticos para las columnas de la BD
atbs = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

st.title("🔬 Registro de Resistencia")

with st.form("formulario_registro"):
    col1, col2, col3 = st.columns(3)
    origen = col1.text_input("Origen")
    anio = col2.number_input("Año", 2020, 2030, 2026)
    provincia = col3.text_input("Provincia")
    
    col4, col5, col6 = st.columns(3)
    programa = col4.text_input("Programa")
    especie = col5.text_input("Especie")
    muestra = col6.text_input("Tipo de Muestra")
    
    bacteria = st.text_input("Bacteria")

    st.write("---")
    cols = st.columns(6)
    resultados = {}
    for i, atb in enumerate(atbs):
        with cols[i % 6]:
            resultados[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=atb)

    if st.form_submit_button("💾 Guardar en Supabase"):
        datos = {
            "origen": origen, "año": anio, "provincia": provincia,
            "programa": programa, "especie": especie, "tipo_de_muestra": muestra,
            "bacteria": bacteria, **resultados
        }
        try:
            # Debe ser exactamente igual al que creaste en SQL
            supabase.table("registros_resistencia").insert(datos).execute()
            st.success("✅ ¡Datos guardados correctamente!")
        except Exception as e:
            st.error(f"Error al insertar: {e}")
