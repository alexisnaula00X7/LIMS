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
    # Valores por defecto para desarrollo local
    SUPABASE_URL = "https://tu-proyecto.supabase.co"
    SUPABASE_KEY = "tu-clave-anon"

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

tab_datos, tab_graf, tab_prov, tab_avanzado = st.tabs([
    "📥 Gestión de Datos (IMC)", "📊 Resumen General Mensual", "🌍 Análisis por Provincia", "📈 Análisis Avanzado"
])

# --- OBTENER DATOS DESDE LA TABLA 'imc' EN SUPABASE ---
with st.spinner("Conectando con la base de datos 'imc'..."):
    try:
        res_m = supabase.table("imc").select("*").execute()
        df_muestras = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
        
        # Corrección automática de mayúsculas/minúsculas en las columnas comunes de Supabase
        if not df_muestras.empty:
            df_muestras.columns = [col.upper() for col in df_muestras.columns]
    except Exception as e:
        st.error(f"❌ Error de conexión con la tabla 'imc': {e}")
        st.info("Por favor, verifica tus Secrets en Streamlit Share y que la URL no tenga una '/' al final.")
        df_muestras = pd.DataFrame()

# Si la base de datos está vacía en Supabase, cargamos una simulación con tus campos reales para que la app no se rompa
if df_muestras.empty:
    st.warning("⚠️ No se encontraron registros en la tabla 'imc' de Supabase. Mostrando datos de simulación.")
    df_muestras = pd.DataFrame({
        "FECHA": ["2026-01-15", "2026-02-10", "2026-03-05", "2026-03-20", "2026-04-11", "2026-05-01"],
        "MES": ["Enero", "Febrero", "Marzo", "Marzo", "Abril", "Mayo"],
        "AÑO": [2026, 2026, 2026, 2026, 2026, 2026],
        "PROVINCIA": ["Pichincha", "Guayas", "Pichincha", "Guayas", "Azuay", "Manabí"],
        "POSITIVO": [6, 12, 4, 3, 2, 8],
        "NEGATIVO": [20, 45, 15, 12, 18, 22],
        "Nº MUESTRAS ANALIZADAS": [26, 57, 19, 15, 20, 30],
        "ENFERMEDAD/ DIAGNÓSTICO": ["Brucelosis", "Brucelosis", "Salmonella", "Mastitis", "Salmonella", "Peste Porcina"],
        "ESPECIE": ["Bovino", "Bovino", "Porcino", "Bovino", "Porcino", "Porcino"]
    })

# Asegurar tipos de datos numéricos para los análisis
df_muestras["POSITIVO"] = pd.to_numeric(df_muestras["POSITIVO"], errors='coerce').fillna(0)
df_muestras["NEGATIVO"] = pd.to_numeric(df_muestras["NEGATIVO"], errors='coerce').fillna(0)
if "Nº MUESTRAS ANALIZADAS" in df_muestras.columns:
    df_muestras["Nº MUESTRAS ANALIZADAS"] = pd.to_numeric(df_muestras["Nº MUESTRAS ANALIZADAS"], errors='coerce').fillna(0)
else:
    df_muestras["Nº MUESTRAS ANALIZADAS"] = df_muestras["POSITIVO"] + df_muestras["NEGATIVO"]

# --- TAB: GESTIÓN DE DATOS ---
with tab_datos:
    st.subheader("📋 Registros Actuales en la Tabla IMC")
    st.dataframe(df_muestras, use_container_width=True)
    
    # Formulario rápido para insertar datos respetando tus campos estructurados
    with st.expander("➕ Registrar Nueva Muestra Analizada"):
        with st.form("form_imc", clear_on_submit=True):
            col_a, col_b, col_c = st.columns(3)
            fecha_ins = col_a.date_input("Fecha", datetime.now())
            provincia_ins = col_b.text_input("Provincia", value="Pichincha")
            especie_ins = col_c.text_input("Especie", value="Bovino")
            
            col_d, col_e, col_f = st.columns(3)
            diagnostico_ins = col_d.text_input("Enfermedad / Diagnóstico", value="Brucelosis")
            pos_ins = col_e.number_input("Muestras Positivas", min_value=0, step=1, value=0)
            neg_ins = col_f.number_input("Muestras Negativas", min_value=0, step=1, value=0)
            
            if st.form_submit_button("Guardar en Supabase"):
                try:
                    nueva_data = {
                        "fecha": fecha_ins.isoformat(),
                        "mes": MESES_DB[fecha_ins.month - 1].capitalize(),
                        "año": fecha_ins.year,
                        "provincia": provincia_ins,
                        "especie": especie_ins,
                        "enfermedad/ diagnostico": diagnostico_ins,
                        "positivo": pos_ins,
                        "negativo": neg_ins,
                        "nº muestras analizadas": pos_ins + neg_ins
                    }
                    supabase.table("imc").insert(nueva_data).execute()
                    st.success("¡Registro guardado exitosamente!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")

# --- TAB: RESUMEN GENERAL MENSUAL ---
with tab_graf:
    st.header("📊 Rendimiento Cronológico del Laboratorio")
    
    if "AÑO" in df_muestras.columns:
        años_disp = sorted(df_muestras['AÑO'].unique(), reverse=True)
        año_sel = st.selectbox("Seleccione el Año de Análisis:", options=años_disp, key="sel_anio_graf")
        
        df_anio = df_muestras[df_muestras['AÑO'] == año_sel]
        
        # Agrupar por mes de manera ordenada
        df_mes = df_anio.groupby("MES").agg({"POSITIVO": "sum", "NEGATIVO": "sum", "Nº MUESTRAS ANALIZADAS": "sum"}).reset_index()
        df_mes["MES_NORM"] = df_mes["MES"].apply(normalizar_texto)
        
        # Asegurar el orden correcto de los meses en el gráfico
        orden_meses = {m: i for i, m in enumerate(MESES_DB)}
        df_mes["ORDEN"] = df_mes["MES_NORM"].map(orden_meses).fillna(99)
        df_mes = df_mes.sort_values("ORDEN")
        
        # KPIs en tarjetas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Muestras Analizadas", f"{int(df_mes['Nº MUESTRAS ANALIZADAS'].sum())}")
        m2.metric("Total Positivos Identificados", f"{int(df_mes['POSITIVO'].sum())}")
        m3.metric("Total Negativos Confirmados", f"{int(df_mes['NEGATIVO'].sum())}")
        
        st.divider()
        
        # Gráfico evolutivo mensual
        fig_mensual = go.Figure(data=[
            go.Bar(name='Positivos', x=df_mes['MES'], y=df_mes['POSITIVO'], marker_color='#ef553b'),
            go.Bar(name='Negativos', x=df_mes['MES'], y=df_mes['NEGATIVO'], marker_color='#1f77b4')
        ])
        fig_mensual.update_layout(barmode='group', title=f"Distribución Mensual de Resultados - Gestión {año_sel}", yaxis_title="Cantidad de Muestras")
        st.plotly_chart(fig_mensual, use_container_width=True)

# --- TAB: ANÁLISIS POR PROVINCIA (SISTEMA DE ALERTAS ANTE >5 POSITIVOS) ---
with tab_prov:
    st.header("🌍 Monitoreo Epidemiológico y Control de Alertas por Provincia")
    
    if "PROVINCIA" in df_muestras.columns:
        # Agrupación por Provincias
        df_prov_est = df_muestras.groupby("PROVINCIA").agg({"POSITIVO": "sum", "NEGATIVO": "sum", "Nº MUESTRAS ANALIZADAS": "sum"}).reset_index()
        
        # KPIs de Alerta
        kpi1, kpi2, kpi3 = st.columns(3)
        alertas_activas = df_prov_est[df_prov_est["POSITIVO"] > 5]["PROVINCIA"].count()
        prov_max = df_prov_est.loc[df_prov_est["POSITIVO"].idxmax()]["PROVINCIA"] if not df_prov_est.empty else "N/A"
        
        kpi1.metric("Provincias en Alerta (>5 Positivos)", f"{alertas_activas}", delta="- Acción Inmediata" if alertas_activas > 0 else "Estable", delta_color="inverse")
        kpi2.metric("Foco Sanitario Principal", f"{prov_max}")
        kpi3.metric("Carga Total Positivos (Nacional)", f"{int(df_prov_est['POSITIVO'].sum())}")
        
        st.divider()
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Resaltar dinámicamente las provincias que sobrepasan el umbral que necesitas alertar por correo
            df_prov_est["Estado"] = df_prov_est["POSITIVO"].apply(lambda x: "🚨 Alerta (>5)" if x > 5 else "✅ Bajo Control")
            fig_alertas = px.bar(df_prov_est, x="PROVINCIA", y="POSITIVO", color="Estado",
                                 color_discrete_map={"🚨 Alerta (>5)": "#ef553b", "✅ Bajo Control": "#636efa"}, 
                                 text="POSITIVO", title="Muestras Positivas Acumuladas por Provincia")
            # Línea guía horizontal en el valor 5
            fig_alertas.add_hline(y=5, line_dash="dash", line_color="red", annotation_text="Límite de Alerta")
            st.plotly_chart(fig_alertas, use_container_width=True)
            
        with col_g2:
            # Gráfico de barras apiladas Positivos vs Negativos
            fig_stack = go.Figure()
            fig_stack.add_trace(go.Bar(name='Positivos', x=df_prov_est['PROVINCIA'], y=df_prov_est['POSITIVO'], marker_color='#ef553b'))
            fig_stack.add_trace(go.Bar(name='Negativos', x=df_prov_est['PROVINCIA'], y=df_prov_est['NEGATIVO'], marker_color='#00cc96'))
            fig_stack.update_layout(barmode='stack', title="Relación de Proporciones (Positivos vs Negativos)")
            st.plotly_chart(fig_stack, use_container_width=True)

# --- TAB: ANÁLISIS AVANZADO ---
with tab_avanzado:
    st.header("📈 Estadística Avanzada y Distribución de Patologías")
    
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.markdown("#### 📊 Descriptores Estadísticos Generales")
        media_pos = round(df_muestras["POSITIVO"].mean(), 2)
        desviacion_pos = round(df_muestras["POSITIVO"].std(), 2)
        total_analizadas = df_muestras["Nº MUESTRAS ANALIZADAS"].sum()
        tasa_positividad = round((df_muestras["POSITIVO"].sum() / total_analizadas) * 100, 2) if total_analizadas > 0 else 0
        
        st.metric("Media de Positivos por Registro", f"{media_pos} muestras")
        st.metric("Desviación Estándar (Dispersión)", f"{desviacion_pos}")
        st.metric("Tasa de Positividad General Molecular", f"{tasa_positividad}%")
        
    with col_s2:
        # Gráfico Boxplot para medir la dispersión y detectar anomalías o picos de contagio
        fig_box = px.box(df_muestras, x="PROVINCIA" if "PROVINCIA" in df_muestras.columns else None, y="POSITIVO",
                         title="Análisis Clínico de Variabilidad y Valores Atípicos (Picos de Positivos)")
        st.plotly_chart(fig_box, use_container_width=True)
        
    st.divider()
    
    # Análisis avanzado de jerarquías clínicas usando Treemap y Sunburst
    st.subheader("🔬 Clasificación Taxonómica de Diagnósticos Positivos")
    col_tree, col_sun = st.columns(2)
    
    # Buscamos nombres de columnas tolerando variaciones de tildes
    col_diag = "ENFERMEDAD/ DIAGNÓSTICO" if "ENFERMEDAD/ DIAGNÓSTICO" in df_muestras.columns else "ENFERMEDAD/ DIAGNILA"
    if col_diag not in df_muestras.columns:
        # Encontrar la columna que contenga la palabra ENFERMEDAD
        for c in df_muestras.columns:
            if "ENFERMEDAD" in c or "DIAG" in c:
                col_diag = c
                break

    with col_tree:
        if col_diag in df_muestras.columns and "PROVINCIA" in df_muestras.columns:
            fig_tree = px.treemap(df_muestras, path=[col_diag, 'PROVINCIA'], values='POSITIVO',
                                 title="Distribución de Enfermedades por Región Geográfica", color_continuous_scale='Reds')
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Faltan los campos clínicos necesarios para renderizar el mapa jerárquico.")
            
    with col_sun:
        if "ESPECIE" in df_muestras.columns and col_diag in df_muestras.columns:
            fig_sun = px.sunburst(df_muestras, path=['ESPECIE', col_diag], values='POSITIVO',
                                  title="Afectación por Especie Animal y Patología Asociada", color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.info("Faltan los campos 'ESPECIE' o 'DIAGNÓSTICO' para procesar el gráfico solar.")
