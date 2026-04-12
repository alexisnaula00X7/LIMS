import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- CONEXIÓN ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de credenciales.")
    st.stop()

st.set_page_config(page_title="LIMS RAM Nacional", layout="wide")

# --- LISTAS DE OPCIONES ---
provincias = ["Azuay", "Bolívar", "Cañar", "Carchi", "Chimborazo", "Cotopaxi", "El Oro", "Esmeraldas", "Galápagos", "Guayas", "Imbabura", "Loja", "Los Ríos", "Manabí", "Morona Santiago", "Napo", "Orellana", "Pastaza", "Pichincha", "Santa Elena", "Santo Domingo de los Tsáchilas", "Sucumbíos", "Tungurahua", "Zamora Chinchipe"]
origenes = ["Granja", "Casa", "Laboratorio", "Mercado al aire libre", "Tienda de mascotas", "Matadero", "Tienda de alimentos, puntos de venta", "Hospital veterinario", "Clínica veterinaria", "Hábitat natural", "Desconocido", "Otro"]
programas = ["Vigilancia", "Cuarentena", "Cliente Externo"]
especies = ["Aves", "Cerdos", "Bovinos"]
muestras = ["Carne", "Heces"]
bacterias = ["E. coli", "Salmonella spp."]
atbs_keys = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

st.title("🔬 Registro de Resistencia")

with st.form("formulario_lims"):
    st.subheader("🆔 Identificación de la Muestra")
    # Este dato será tu ID en la base de datos
    codigo_id = st.text_input("Ingrese el Código de Muestra (ID)", placeholder="Ej: 2026-AVE-001")

    st.write("---")
    c1, c2, c3, c4 = st.columns(4)
    origen = c1.selectbox("Origen", origenes)
    anio = c2.number_input("Año", 2020, 2030, 2026)
    provincia = c3.selectbox("Provincia", provincias)
    programa = c4.selectbox("Programa", programas)
    
    c5, c6, c7 = st.columns(3)
    especie = c5.selectbox("Especie", especies)
    tipo_muestra = c6.selectbox("Tipo de Muestra", muestras)
    bacteria = c7.selectbox("Bacteria", bacterias)

    st.write("---")
    st.subheader("🧪 Resultados Antibióticos")
    cols = st.columns(6)
    resultados = {}
    for i, atb in enumerate(atbs_keys):
        with cols[i % 6]:
            resultados[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=atb)

    if st.form_submit_button("💾 REGISTRAR MUESTRA"):
        if not codigo_id:
            st.warning("⚠️ Debes ingresar un Código de Muestra para poder guardar.")
        else:
            datos = {
                "codigo_muestra": codigo_id, # Se registra como la llave primaria
                "origen": origen, 
                "año": anio, 
                "provincia": provincia,
                "programa": programa, 
                "especie": especie, 
                "tipo_de_muestra": tipo_muestra, 
                "bacteria": bacteria,
                **resultados
            }
            
            try:
                supabase.table("registros_resistencia").insert(datos).execute()
                st.success(f"✅ Muestra {codigo_id} registrada exitosamente.")
                st.balloons()
            except Exception as e:
                st.error(f"Error: Tal vez el código {codigo_id} ya existe. Detalle: {e}")

# --- CONSULTA ---
st.write("---")
if st.button("📊 Ver Base de Datos"):
    res = supabase.table("registros_resistencia").select("*").execute()
    if res.data:
        # Mostramos la tabla. Verás que 'codigo_muestra' aparece como la primera columna
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
