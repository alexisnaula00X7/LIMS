import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
# Se usan etiquetas. Los valores reales van en el panel "Secrets" de Streamlit Cloud.
try:
    url = st.secrets["https://pfdthsxlhpncheutmunm.supabase.co"]
    key = st.secrets["sb_secret_x8LVUmKOYhbwOAVxHOv5fg_2rjQABR4"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Error: No se encontraron las credenciales en los Secrets de Streamlit.")
    st.info("Asegúrate de haber configurado SUPABASE_URL y SUPABASE_KEY en el panel de Settings.")
    st.stop()

st.set_page_config(page_title="LIMS RAM Nacional", layout="wide")

# Lista de antibióticos para el formulario (en minúsculas para la base de datos)
atbs_keys = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

# --- 2. INTERFAZ DE USUARIO ---
st.title("🔬 Sistema de Registro de Resistencia Bacteriana")
st.markdown("---")

with st.form("formulario_lims"):
    st.subheader("📋 Datos Generales de la Muestra")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        origen = st.text_input("Origen")
    with col2:
        anio = st.number_input("Año", min_value=2020, max_value=2030, value=2026)
    with col3:
        provincia = st.text_input("Provincia")
    with col4:
        programa = st.text_input("Programa")
        
    col5, col6, col7 = st.columns(3)
    with col5:
        especie = st.text_input("Especie")
    with col6:
        tipo_muestra = st.text_input("Tipo de Muestra")
    with col7:
        bacteria = st.text_input("Bacteria / Microorganismo")

    st.markdown("---")
    st.subheader("🧪 Resultados de Antibiograma (S / I / R)")
    
    # Generar columnas para los selectores de antibióticos
    cols_atb = st.columns(6)
    resultados_usuario = {}
    
    for i, atb in enumerate(atbs_keys):
        with cols_atb[i % 6]:
            # Guardamos la selección usando la clave en minúsculas
            resultados_usuario[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=f"sel_{atb}")

    st.markdown("<br>", unsafe_allow_html=True)
    enviar = st.form_submit_button("💾 GUARDAR REGISTRO EN LA NUBE")

    if enviar:
        # Validación básica de campos obligatorios
        if not origen or not bacteria:
            st.error("❌ Por favor, completa al menos los campos 'Origen' y 'Bacteria'.")
        else:
            # Construcción del objeto de datos
            # IMPORTANTE: Los nombres de las llaves deben ser iguales a las columnas de tu tabla SQL
            datos_registro = {
                "origen": origen,
                "año": anio,
                "provincia": provincia,
                "programa": programa,
                "especie": especie,
                "tipo_de_muestra": tipo_muestra,
                "bacteria": bacteria,
                **resultados_usuario # Esto expande amp, czo, caz...
            }
            
            try:
                # Inserción en la tabla de Supabase
                response = supabase.table("registros_resistencia").insert(datos_registro).execute()
                st.success(f"✅ Registro guardado exitosamente para la bacteria: {bacteria}")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error al guardar en la base de datos: {e}")

# --- 3. VISUALIZACIÓN DE DATOS ---
st.markdown("---")
st.subheader("📊 Historial de Registros")

if st.button("🔄 Actualizar Tabla de Datos"):
    try:
        res = supabase.table("registros_resistencia").select("*").order('fecha_creacion', desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # Reordenar para ver primero los datos generales
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aún no hay registros en la base de datos.")
    except Exception as e:
        st.error(f"No se pudieron cargar los datos: {e}")
