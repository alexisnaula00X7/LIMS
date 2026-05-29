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

tab_datos, tab_graf, tab_prov, tab_avanzado = st.tabs([
    "📥 Gestión de Datos (BMI)", "📊 Resumen General Mensual", "🌍 Análisis por Provincia", "📈 Análisis Avanzado"
])

# --- OBTENER DATOS DESDE LA TABLA 'DATA_BMI' EN SUPABASE ---
with st.spinner("Conectando con la base de datos 'DATA_BMI'..."):
    try:
        res_m = supabase.table("DATA_BMI").select("*").execute()
        df_muestras = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
        
        # Forzamos los nombres de las columnas a Mayúsculas para mantener consistencia en los gráficos
        if not df_muestras.empty:
            df_muestras.columns = [col.upper() for col in df_muestras.columns]
    except Exception as e:
        st.error(f"❌ Error de conexión con la tabla 'DATA_BMI': {e}")
        st.info("Asegúrate de haber ejecutado 'NOTIFY pgrst, 'reload schema';' en el SQL Editor de Supabase si la tabla es muy nueva.")
        df_muestras = pd.DataFrame()

# Simulación con tu NUEVA estructura exacta si la base de datos está vacía
if df_muestras.empty:
    st.warning("⚠️ No se encontraron registros en la tabla 'DATA_BMI'. Mostrando simulación con tu nueva estructura de columnas.")
    df_muestras = pd.DataFrame({
        "CODIGO DE MUESTRA": ["M-001", "M-002"],
        "FECHA": ["2026-01-15", "2026-02-10"],
        "MES": ["Enero", "Febrero"],
        "AÑO": [2026, 2026],  # Nota: Si en Supabase falla por la Ñ, cámbialo a "ANO" aquí y en el formulario
        "ORDEN DE TRABAJO": ["OT-100", "OT-101"],
        "TIPO DE CLIENTE": ["Interno", "Externo"],
        "INFORME": ["INF-01", "INF-02"],
        "ESPECIE": ["Bovino", "Porcino"],
        "PROPIETARIO": ["Juan Pérez", "María López"],
        "MOTIVO DE ANÁLISIS": ["Vigilancia", "Diagnóstico"],
        "PROYECTO/PROGRAMA/PROCESO": ["Control Sanitario", "Erradicación"],
        "PROVINCIA": ["Pichincha", "Guayas"],
        "CANTON": ["Quito", "Guayaquil"],
        "PARROQUIA": ["Iñaquito", "Tarqui"],
        "TIPO DE MUESTRA": ["Sangre", "Suero"],
        "FECHA DE COLECTA": ["2026-01-10", "2026-02-05"],
        "ENFERMEDAD/ DIAGNÓSTICO": ["Brucelosis", "Salmonella"],
        "TÉCNICA DIAGNÓSTICA": ["PCR", "ELISA"],
        "FECHA INICIO ANÁLISIS": ["2026-01-12", "2026-02-08"],
        "FECHA FINALIZACIÓN ANÁLISIS": ["2026-01-15", "2026-02-10"],
        "FECHA DE INFORME": ["2026-01-16", "2026-02-11"],
        "Nº INFORMES EMITIDOS": [1, 1],
        "Nº MUESTRAS ANALIZADAS": [10, 20],
        "POSITIVO": [2, 5],
        "NEGATIVO": [8, 15],
        "ESPECIE_IDENTIFICADA": ["Brucella abortus", "Salmonella enterica"]
    })

# Asegurar tipos de datos numéricos obligatorios para gráficos
df_muestras["POSITIVO"] = pd.to_numeric(df_muestras["POSITIVO"], errors='coerce').fillna(0)
df_muestras["NEGATIVO"] = pd.to_numeric(df_muestras["NEGATIVO"], errors='coerce').fillna(0)
col_total = "Nº MUESTRAS ANALIZADAS" if "Nº MUESTRAS ANALIZADAS" in df_muestras.columns else "NIO MUESTRAS ANALIZADAS"
if col_total in df_muestras.columns:
    df_muestras[col_total] = pd.to_numeric(df_muestras[col_total], errors='coerce').fillna(0)
else:
    df_muestras[col_total] = df_muestras["POSITIVO"] + df_muestras["NEGATIVO"]

# --- TAB: GESTIÓN DE DATOS ---
with tab_datos:
    st.subheader("📋 Registros Actuales en DATA_BMI")
    st.dataframe(df_muestras, use_container_width=True)
    
    with st.expander("➕ Registrar Nueva Muestra Analizada Completa"):
        with st.form("form_bmi_completo", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            cod_m = c1.text_input("Código de Muestra", value="M-003")
            fecha_p = c2.date_input("Fecha Registro", datetime.now())
            orden_t = c3.text_input("Orden de Trabajo", value="OT-102")
            tipo_c = c4.selectbox("Tipo de Cliente", ["Interno", "Externo"])
            
            c5, c6, c7, c8 = st.columns(4)
            informe_p = c5.text_input("Informe Nº", value="INF-03")
            especie_p = c6.text_input("Especie", value="Bovino")
            prop_p = c7.text_input("Propietario", value="Particular")
            motivo_p = c8.text_input("Motivo de Análisis", value="Diagnóstico")
            
            c9, c10, c11, c12 = st.columns(4)
            proyecto_p = c9.text_input("Proyecto/Programa", value="Vigilancia")
            prov_p = c10.text_input("Provincia", value="Pichincha")
            cant_p = c11.text_input("Cantón", value="Quito")
            parr_p = c12.text_input("Parroquia", value="Belisario")
            
            c13, c14, c15, c16 = st.columns(4)
            tipo_mu_p = c13.text_input("Tipo de Muestra", value="Sangre")
            fecha_col = c14.date_input("Fecha de Colecta", datetime.now())
            diag_p = c15.text_input("Enfermedad / Diagnóstico", value="Brucelosis")
            tecnica_p = c16.text_input("Técnica Diagnóstica", value="PCR")
            
            c17, c18, c19, c20 = st.columns(4)
            f_ini = c17.date_input("Fecha Inicio Análisis", datetime.now())
            f_fin = c18.date_input("Fecha Fin Análisis", datetime.now())
            f_inf = c19.date_input("Fecha de Informe", datetime.now())
            n_inf_emitidos = c20.number_input("Nº Informes Emitidos", min_value=0, value=1, step=1)
            
            c21, c22, c23 = st.columns(3)
            pos_p = c21.number_input("Muestras Positivas", min_value=0, value=0, step=1)
            neg_p = c22.number_input("Muestras Negativas", min_value=0, value=0, step=1)
            esp_id_p = c23.text_input("Especie Identificada (Patógeno)", value="Brucella")
            
            if st.form_submit_button("Guardar en Supabase"):
                try:
                    # Diccionario mapeado con la estructura exacta que pasaste
                    nueva_data = {
                        "Codigo de Muestra": cod_m,
                        "FECHA": fecha_p.isoformat(),
                        "MES": MESES_DB[fecha_p.month - 1].capitalize(),
                        "AÑO": fecha_p.year,  # Si da error por la Ñ en tu Supabase, cámbialo a "ANO" o "AÑO" según corresponda
                        "ORDEN DE TRABAJO": orden_t,
                        "TIPO DE CLIENTE": tipo_c,
                        "INFORME": informe_p,
                        "ESPECIE": especie_p,
                        "PROPIETARIO": prop_p,
                        "MOTIVO DE ANÁLISIS": motivo_p,
                        "PROYECTO/PROGRAMA/PROCESO": proyecto_p,
                        "PROVINCIA": prov_p,
                        "CANTON": cant_p,
                        "PARROQUIA": parr_p,
                        "TIPO DE MUESTRA": tipo_mu_p,
                        "FECHA DE COLECTA": fecha_col.isoformat(),
                        "ENFERMEDAD/ DIAGNÓSTICO": diag_p,
                        "TÉCNICA DIAGNÓSTICA": tecnica_p,
                        "FECHA INICIO ANÁLISIS": f_ini.isoformat(),
                        "FECHA FINALIZACIÓN ANÁLISIS": f_fin.isoformat(),
                        "FECHA DE INFORME": f_inf.isoformat(),
                        "Nº INFORMES EMITIDOS": n_inf_emitidos,
                        "Nº MUESTRAS ANALIZADAS": pos_p + neg_p,
                        "POSITIVO": pos_p,
                        "NEGATIVO": neg_p,
                        "ESPECIE_IDENTIFICADA": esp_id_p
                    }
                    supabase.table("DATA_BMI").insert(nueva_data).execute()
                    st.success("¡Registro completo guardado exitosamente en DATA_BMI!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al guardar: {ex}")

# --- TAB: RESUMEN GENERAL MENSUAL ---
with tab_graf:
    st.header("📊 Rendimiento Cronológico del Laboratorio")
    col_anio_busca = "AÑO" if "AÑO" in df_muestras.columns else "ANO"
    if col_anio_busca in df_muestras.columns:
        años_disp = sorted(df_muestras[col_anio_busca].unique(), reverse=True)
        año_sel = st.selectbox("Seleccione el Año de Análisis:", options=años_disp, key="sel_anio_graf")
        df_anio = df_muestras[df_muestras[col_anio_busca] == año_sel]
        
        df_mes = df_anio.groupby("MES").agg({"POSITIVO": "sum", "NEGATIVO": "sum", col_total: "sum"}).reset_index()
        df_mes["MES_NORM"] = df_mes["MES"].apply(normalizar_texto)
        
        orden_meses = {m: i for i, m in enumerate(MESES_DB)}
        df_mes["ORDEN"] = df_mes["MES_NORM"].map(orden_meses).fillna(99)
        df_mes = df_mes.sort_values("ORDEN")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Muestras Analizadas", f"{int(df_mes[col_total].sum())}")
        m2.metric("Total Positivos Identificados", f"{int(df_mes['POSITIVO'].sum())}")
        m3.metric("Total Negativos Confirmados", f"{int(df_mes['NEGATIVO'].sum())}")
        
        st.divider()
        
        fig_mensual = go.Figure(data=[
            go.Bar(name='Positivos', x=df_mes['MES'], y=df_mes['POSITIVO'], marker_color='#ef553b'),
            go.Bar(name='Negativos', x=df_mes['MES'], y=df_mes['NEGATIVO'], marker_color='#1f77b4')
        ])
        fig_mensual.update_layout(barmode='group', title=f"Distribución Mensual de Resultados - Gestión {año_sel}", yaxis_title="Cantidad de Muestras")
        st.plotly_chart(fig_mensual, use_container_width=True)

# --- TAB: ANÁLISIS POR PROVINCIA ---
with tab_prov:
    st.header("🌍 Monitoreo Epidemiológico por Provincia")
    if "PROVINCIA" in df_muestras.columns:
        df_prov_est = df_muestras.groupby("PROVINCIA").agg({"POSITIVO": "sum", "NEGATIVO": "sum", col_total: "sum"}).reset_index()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        alertas_activas = df_prov_est[df_prov_est["POSITIVO"] > 5]["PROVINCIA"].count()
        prov_max = df_prov_est.loc[df_prov_est["POSITIVO"].idxmax()]["PROVINCIA"] if not df_prov_est.empty else "N/A"
        
        kpi1.metric("Provincias en Alerta (>5 Positivos)", f"{alertas_activas}", delta="- Acción Inmediata" if alertas_activas > 0 else "Estable", delta_color="inverse")
        kpi2.metric("Foco Sanitario Principal", f"{prov_max}")
        kpi3.metric("Carga Total Positivos (Nacional)", f"{int(df_prov_est['POSITIVO'].sum())}")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            df_prov_est["Estado"] = df_prov_est["POSITIVO"].apply(lambda x: "🚨 Alerta (>5)" if x > 5 else "✅ Bajo Control")
            fig_alertas = px.bar(df_prov_est, x="PROVINCIA", y="POSITIVO", color="Estado",
                                 color_discrete_map={"🚨 Alerta (>5)": "#ef553b", "✅ Bajo Control": "#636efa"}, 
                                 text="POSITIVO", title="Muestras Positivas Acumuladas por Provincia")
            fig_alertas.add_hline(y=5, line_dash="dash", line_color="red", annotation_text="Límite de Alerta")
            st.plotly_chart(fig_alertas, use_container_width=True)
            
        with col_g2:
            fig_stack = go.Figure()
            fig_stack.add_trace(go.Bar(name='Positivos', x=df_prov_est['PROVINCIA'], y=df_prov_est['POSITIVO'], marker_color='#ef553b'))
            fig_stack.add_trace(go.Bar(name='Negativos', x=df_prov_est['PROVINCIA'], y=df_prov_est['NEGATIVO'], marker_color='#00cc96'))
            fig_stack.update_layout(barmode='stack', title="Relación de Proporciones (Positivos vs Negativos)")
            st.plotly_chart(fig_stack, use_container_width=True)

# --- TAB: ANÁLISIS AVANZADO ---
with tab_avanzado:
    st.header("📈 Estadística Avanzada y Distribución de Patologías")
    col_diag = None
    for c in df_muestras.columns:
        if "ENFERMEDAD" in c or "DIAG" in c:
            col_diag = c
            break

    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.markdown("#### 📊 Descriptores Estadísticos")
        media_pos = round(df_muestras["POSITIVO"].mean(), 2)
        desviacion_pos = round(df_muestras["POSITIVO"].std(), 2)
        total_analizadas = df_muestras[col_total].sum()
        tasa_positividad = round((df_muestras["POSITIVO"].sum() / total_analizadas) * 100, 2) if total_analizadas > 0 else 0
        
        st.metric("Media de Positivos por Registro", f"{media_pos} muestras")
        st.metric("Desviación Estándar (Dispersión)", f"{desviacion_pos}")
        st.metric("Tasa de Positividad Molecular", f"{tasa_positividad}%")
        
    with col_s2:
        fig_box = px.box(df_muestras, x="PROVINCIA" if "PROVINCIA" in df_muestras.columns else None, y="POSITIVO",
                         title="Análisis Clínico de Variabilidad por Provincia")
        st.plotly_chart(fig_box, use_container_width=True)
        
    st.divider()
    st.subheader("🔬 Clasificación Taxonómica de Diagnósticos Positivos")
    col_tree, col_sun = st.columns(2)
    
    with col_tree:
        if col_diag and "PROVINCIA" in df_muestras.columns:
            fig_tree = px.treemap(df_muestras, path=[col_diag, 'PROVINCIA'], values='POSITIVO',
                                 title="Distribución de Enfermedades por Región Geográfica", color_continuous_scale='Reds')
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Faltan los campos clínicos necesarios para renderizar el mapa jerárquico.")
            
    with col_sun:
        if "ESPECIE" in df_muestras.columns and col_diag:
            fig_sun = px.sunburst(df_muestras, path=['ESPECIE', col_diag], values='POSITIVO',
                                  title="Afectación por Especie Animal y Patología", color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_sun, use_container_width=True)
