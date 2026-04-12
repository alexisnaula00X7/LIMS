import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Conexión (Asegúrate de tener estos nombres en tus Secrets de Streamlit)
try:
    url = st.secrets["https://pfdthsxlhpncheutmunm.supabase.co"]
    key = st.secrets["sb_secret_Gp4ZYEnk85--IoTv92ltcw_lmK-4BlX"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error al cargar credenciales. Revisa los Secrets.")
    st.stop()

st.set_page_config(page_title="LIMS RAM Nacional", layout="wide")

# Lista de antibióticos (en minúsculas para la BD)
atbs = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

st.title("🔬 Sistema de Ingreso de Datos de Resistencia")

# 2. El Formulario (Define todas las variables aquí dentro)
with st.form("formulario_ingreso"):
    st.subheader("Información General")
    c1, c2, c3, c4 = st.columns(4)
    origen = c1.text_input("Origen")
    anio = c2.number_input("Año", 2020, 2030, 2026)
    provincia = c3.text_input("Provincia")
    programa = c4.text_input("Programa")
    
    c5, c6, c7 = st.columns(3)
    especie = c5.text_input("Especie")
    muestra = c6.text_input("Tipo de Muestra")
    bacteria = c7.text_input("Bacteria")

    st.subheader("Resultados de Antibióticos (S/I/R)")
    cols = st.columns(6)
    resultados = {}
    for i, atb in enumerate(atbs):
        with cols[i % 6]:
            # Guardamos la elección del usuario en el diccionario
            resultados[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=atb)

    # El botón de enviar debe estar dentro del 'with st.form'
    enviar = st.form_submit_button("💾 Guardar Registro")

    if enviar:
        if not id_muestra and not origen: # Validación simple
            st.warning("⚠️ Por favor rellena al menos el campo Origen.")
        else:
            # 3. Construcción del diccionario (Aquí es donde daba el NameError)
            # Ahora origen, anio, etc., están definidos arriba.
            datos_para_enviar = {
                "origen": origen,
                "año": anio,
                "provincia": provincia,
                "programa": programa,
                "especie": especie,
                "tipo_de_muestra": muestra,
                "bacteria": bacteria,
                **resultados # Esto añade amp, czo, caz... automáticamente
            }
            
            try:
                supabase.table("registros_resistencia").insert(datos_para_enviar).execute()
                st.success("✅ Registro guardado exitosamente en la base de datos.")
            except Exception as e:
                st.error(f"Error al guardar en Supabase: {e}")

# 4. Sección de Consulta
st.markdown("---")
if st.button("📊 Ver Historial de Datos"):
    try:
        response = supabase.table("registros_resistencia").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay datos registrados aún.")
    except Exception as e:
        st.error(f"No se pudo leer la base de datos: {e}")
