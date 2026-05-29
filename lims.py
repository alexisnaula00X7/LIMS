import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import unicodedata

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("❌ No se encontraron los Secrets de Supabase en Streamlit.")
    st.stop()

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# --- 2. GESTIÓN DE USUARIO ÚNICO ---
USUARIO_ADMIN = {"admin": "admin123"}

def login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("#")
        st.title("🔐 Acceso")
        st.info("Laboratorio de Biología Molecular")
        
        with st.form("login_form"):
            user_input = st.text_input("Usuario").lower().strip()
            pass_input = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Iniciar Sesión")
            
            if btn_login:
                if user_input in USUARIO_ADMIN and USUARIO_ADMIN[user_input] == pass_input:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.success("Bienvenido Administrador")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- SIDEBAR: LOGOUT ---
with st.sidebar:
    st.markdown(f"👤 **Sesión:** `ADMIN`")
    if st.button("Cerrar Sesión"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()

# --- 3. CONSTANTES Y UTILIDADES ---
MESES_DB = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

# --- 4. INTERFAZ DASHBOARD ---
st.set_page_config(page_title="LIMS - Biología Molecular", layout="wide")
st.title("🧪 Laboratorio de Biología Molecular - Control de Muestras")

# --- OBTENER DATOS DESDE LA TABLA 'DATA_BMI' EN SUPABASE ---
with st.spinner("Conectando con la base de datos 'DATA_BMI'..."):
    try:
        res_m = supabase.table("DATA_BMI").select("*").execute()
        df_muestras = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
        
        if not df_muestras.empty:
            df_muestras.columns = [col.upper() for col in df_muestras.columns]
    except Exception as e:
        st.error(f"❌ Error de conexión con la tabla 'DATA_BMI': {e}")
        df_muestras = pd.DataFrame()

# Simulación con datos de prueba incluyendo FILOGENIA
if df_muestras.empty:
    st.warning("⚠️ No se encontraron registros. Mostrando simulación.")
    df_muestras = pd.DataFrame({
        "FECHA": ["2026-01-15", "2026-02-10", "2026-03-05", "2026-03-20"],
        "MES": ["Enero", "Febrero", "Marzo", "Marzo"],
        "AÑO": [2026, 2026, 2026, 2026],
        "ESPECIE": ["Bovino", "Porcino", "Bovino", "Aviar"],
        "PROVINCIA": ["Pichincha", "Guayas", "Pichincha", "Azuay"],
        "ENFERMEDAD/ DIAGNÓSTICO": ["Brucelosis", "Salmonella", "FILOGENIA", "FILOGENIA"],
        "POSITIVO": [5, 10, 0, 0],
        "NEGATIVO": [15, 20, 0, 0],
        "Nº MUESTRAS ANALIZADAS": [20, 30, 0, 0],
        "ESPECIE_IDENTIFICADA": [None, None, "E. coli ST131", "Klebsiella pneumoniae"]
    })

# Estandarización de nombres de columnas de conteo
col_total = "Nº MUESTRAS ANALIZADAS" if "Nº MUESTRAS ANALIZADAS" in df_muestras.columns else "NIO MUESTRAS ANALIZADAS"
df_muestras["POSITIVO"] = pd.to_numeric(df_muestras["POSITIVO"], errors='coerce').fillna(0)
df_muestras["NEGATIVO"] = pd.to_numeric(df_muestras["NEGATIVO"], errors='coerce').fillna(0)
df_muestras[col_total] = pd.to_numeric(df_muestras[col_total], errors='coerce').fillna(0)

# --- 5. SECCIÓN GLOBAL DE FILTROS ---
st.markdown("### 🔍 Filtros Globales de Análisis")
c_filt1, c_filt2, c_filt3 = st.columns(3)

col_anio = "AÑO" if "AÑO" in df_muestras.columns else "ANO"
col_diag = next((c for c in df_muestras.columns if "ENFERMEDAD" in c or "DIAG" in c), None)
col_esp_id = "ESPECIE_IDENTIFICADA"

with c_filt1:
    anios = ["Todos"] + sorted([int(x) for x in df_muestras[col_anio].dropna().unique()], reverse=True)
    año_sel = st.selectbox("Año:", anios)

with c_filt2:
    diags = ["Todos"] + sorted(list(df_muestras[col_diag].dropna().unique()))
    diag_sel = st.selectbox("Enfermedad / Diagnóstico:", diags)

with c_filt3:
    especies = ["Todos"] + sorted(list(df_muestras["ESPECIE"].dropna().unique()))
    especie_sel = st.selectbox("Especie Animal:", especies)

# Aplicar Filtros
df_filtrado = df_muestras.copy()
if año_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_anio] == año_sel]
if diag_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_diag] == diag_sel]
if especie_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ESPECIE"] == especie_sel]

# --- 🚀 REGLA ESPECIAL PARA FILOGENIA ---
es_filogenia = (diag_sel == "FILOGENIA")

if es_filogenia:
    # Ignorar columnas numéricas y contar registros de ESPECIE_IDENTIFICADA
    # Solo tomamos filas donde se haya identificado algo
    df_filtrado = df_filtrado[df_filtrado[col_esp_id].notna() & (df_filtrado[col_esp_id] != "")]
    df_filtrado["POSITIVO"] = 1  # Cada identificación vale por 1
    df_filtrado["NEGATIVO"] = 0
    df_filtrado[col_total] = 1
    msg_tipo = "📊 Mostrando conteo por Especie Identificada (Filogenia)"
else:
    msg_tipo = "📊 Mostrando valores numéricos de Positivo/Negativo"

st.info(msg_tipo)
st.divider()

# --- 6. PESTAÑAS ---
tab_datos, tab_graf, tab_prov, tab_avanzado = st.tabs([
    "📥 Datos", "📊 Mensual", "🌍 Provincias", "📈 Avanzado"
])

# --- TAB: DATOS ---
with tab_
