import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

# --- 1. CONEXIÓN (Usa tus credenciales) ---
SUPABASE_URL = st.secrets["https://xbqwxdcelgjwpancjjlj.supabase.co"]
SUPABASE_KEY = st.secrets["sb_publishable_nfgyivDM0dpr_xD16EZ5RQ_LBXjXzwI"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="LIMS Profesional RAM", layout="wide")

# --- 2. FUNCIONES DE CARGA DE DATOS ---
@st.cache_data
def obtener_catalogos():
    # Traemos microorganismos
    m_query = supabase.table("microorganismos").select("id, nombre_cientifico").execute()
    # Traemos antibióticos
    a_query = supabase.table("antibioticos").select("id, nombre").execute()
    return m_query.data, a_query.data

try:
    micros, atbs_data = obtener_catalogos()
    dict_micros = {m['nombre_cientifico']: m['id'] for m in micros}
    # Filtramos solo tus 12 antibióticos específicos si es necesario
    nombres_atbs = [a['nombre'] for a in atbs_data]
    dict_atbs = {a['nombre']: a['id'] for a in atbs_data}
except Exception as e:
    st.error(f"Error cargando catálogos de Supabase: {e}")
    st.stop()

# --- 3. INTERFAZ DE USUARIO ---
st.title("🔬 Registro de Antibiograma Relacional")
st.info("Este formulario guarda datos vinculando las tablas de Microorganismos y Antibióticos.")

with st.form("registro_lims"):
    col1, col2 = st.columns(2)
    with col1:
        id_muestra = st.text_input("🆔 Identificación de Muestra")
        micro_sel = st.selectbox("🧫 Microorganismo detectado", options=list(dict_micros.keys()))
    with col2:
        fecha_proc = st.date_input("📅 Fecha de Registro", date.today())
        # Puedes añadir aquí valor_cim si lo usas
    
    st.write("---")
    st.write("### 🧪 Resultados de Susceptibilidad")
    
    # Creamos la cuadrícula para los antibióticos
    cols = st.columns(4)
    resultados_input = {}
    
    # Aquí usamos los nombres reales que vienen de tu tabla 'antibioticos'
    for i, nombre_atb in enumerate(nombres_atbs[:12]): # Limitamos a 12
        with cols[i % 4]:
            resultados_input[nombre_atb] = st.selectbox(nombre_atb, ["S", "I", "R"], key=nombre_atb)

    enviar = st.form_submit_button("💾 Guardar registros vinculados")

    if enviar:
        if id_muestra:
            try:
                # 4. PREPARACIÓN DE DATOS (Formato Relacional)
                filas_para_insertar = []
                for nombre_atb, interpretacion in resultados_input.items():
                    fila = {
                        "identificacion_muestra": id_muestra,
                        "fecha_registro": str(fecha_proc),
                        "microorganismo_id": dict_micros[micro_sel],
                        "antibiotico_id": dict_atbs[nombre_atb],
                        "interpretacion": interpretacion,
                        "valor_cim": "N/A" # Opcional
                    }
                    filas_para_insertar.append(fila)
                
                # 5. INSERCIÓN MASIVA
                supabase.table("resultados").insert(filas_para_insertar).execute()
                st.success(f"✅ Éxito: Se crearon {len(filas_para_insertar)} registros vinculados a la muestra {id_muestra}")
                
            except Exception as e:
                st.error(f"Error al insertar en la tabla 'resultados': {e}")
        else:
            st.warning("⚠️ El ID de muestra es obligatorio.")

# --- 6. VISTA DE DATOS ---
st.write("---")
if st.button("📊 Ver últimos resultados"):
    res_query = supabase.table("resultados").select("*, microorganismos(nombre_cientifico), antibioticos(nombre)").limit(20).execute()
    if res_query.data:
        st.dataframe(pd.DataFrame(res_query.data))
