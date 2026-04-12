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

# --- LISTAS ---
provincias = ["Azuay", "Bolívar", "Cañar", "Carchi", "Chimborazo", "Cotopaxi", "El Oro", "Esmeraldas", "Galápagos", "Guayas", "Imbabura", "Loja", "Los Ríos", "Manabí", "Morona Santiago", "Napo", "Orellana", "Pastaza", "Pichincha", "Santa Elena", "Santo Domingo de los Tsáchilas", "Sucumbíos", "Tungurahua", "Zamora Chinchipe"]
origenes = ["Granja", "Casa", "Laboratorio", "Mercado al aire libre", "Tienda de mascotas", "Matadero", "Tienda de alimentos, puntos de venta", "Hospital veterinario", "Clínica veterinaria", "Hábitat natural", "Desconocido", "Otro"]
programas = ["Vigilancia", "Cuarentena", "Cliente Externo"]
especies = ["Aves", "Cerdos", "Bovinos"]
muestras = ["Hisopado", "Heces"]
bacterias = ["E. coli", "Salmonella spp."]
atbs_keys = ['amp', 'czo', 'caz', 'cro', 'fep', 'etp', 'mem', 'gen', 'cip', 'nor', 'fos', 'tmp']

st.title("🔬 Registro de Resistencia")

with st.form("formulario_lims"):
    st.subheader("🆔 Identificación Única")
    # AQUÍ ESTÁ EL CAMPO QUE NECESITAS
    codigo_id = st.text_input("Código de la Muestra (Ej: LAB-2026-001)")

    st.write("---")
    st.subheader("📋 Datos de Origen")
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
    st.subheader("🧪 Resultados (S / I / R)")
    cols = st.columns(6)
    resultados = {}
    for i, atb in enumerate(atbs_keys):
        with cols[i % 6]:
            resultados[atb] = st.selectbox(atb.upper(), ["S", "I", "R"], key=atb)

    if st.form_submit_button("💾 GUARDAR REGISTRO"):
        if not codigo_id:
            st.warning("⚠️ El Código de la Muestra es obligatorio.")
        else:
            datos = {
                "codigo_muestra": codigo_id, # Enviamos tu código manual
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
                st.success(f"✅ ¡Muestra {codigo_id} registrada!")
                st.balloons()
            except Exception as e:
                st.error(f"Error al insertar: {e}")

# --- TABLA DE CONSULTA ---
st.write("---")
if st.button("📊 Mostrar Registros"):
    res = supabase.table("registros_resistencia").select("*").order("fecha_creacion", desc=True).execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
