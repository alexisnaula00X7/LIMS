import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

# 1. Conexión a Supabase
# En producción, usa st.secrets para proteger estas claves
SUPABASE_URL = "https://xbqwxdcelgjwpancjjlj.supabase.co"
SUPABASE_KEY = "sb_secret_xotldyoauUJ2awRx2pXUCA_MKQ0wgKk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="LIMS Cloud (Supabase)", layout="wide")

atbs = ['AMP', 'CIP', 'FEP', 'CRO', 'CAZ', 'CZO', 'ETP', 'FOS', 'GEN', 'MEM', 'NOR', 'TMP']

st.title("🔬 LIMS Cloud - Registro con Supabase")

# --- FORMULARIO ---
with st.form("registro_supabase"):
    c1, c2 = st.columns(2)
    id_muestra = c1.text_input("🆔 ID de Muestra")
    fecha = c2.date_input("📅 Fecha", date.today())
    
    st.write("### Panel de Antibióticos")
    cols = st.columns(4)
    res = {atb: cols[i % 4].selectbox(atb, ["S", "I", "R"], key=atb) for i, atb in enumerate(atbs)}
    
    if st.form_submit_button("💾 Guardar en Supabase"):
        if id_muestra:
            # Preparar los datos para Supabase
            datos = {
                "id_muestra": id_muestra,
                "fecha": str(fecha),
                **res
            }
            
            # Enviar a la base de datos
            try:
                response = supabase.table("resultados").insert(datos).execute()
                st.success(f"✅ Muestra {id_muestra} guardada en la nube.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")
        else:
            st.warning("Escribe el ID de la muestra.")

# --- VISUALIZACIÓN DE DATOS ---
st.markdown("---")
if st.button("🔄 Consultar Base de Datos Online"):
    try:
        # Consultar datos de la tabla
        query = supabase.table("resultados").select("*").execute()
        df = pd.DataFrame(query.data)
        
        if not df.empty:
            st.subheader("📊 Registros en la Nube")
            st.dataframe(df, use_container_width=True)
            
            # Gráfico rápido de un antibiótico
            atb_sel = st.selectbox("Estadística de:", atbs)
            conteo = df[atb_sel].value_counts()
            st.bar_chart(conteo)
        else:
            st.info("La base de datos está vacía.")
    except Exception as e:
        st.error(f"Error al conectar: {e}")
