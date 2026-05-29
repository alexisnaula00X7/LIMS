import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import unicodedata

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
try:
    SUPABASE_URL = "https://ptyemcxzvvzkkvxbeqxw.supabase.co"
    SUPABASE_KEY = "sb_publishable_IOE6cLvYfS7PuALxUXOWFw_uGtCQsSB"
    
except Exception:
    # Valores por defecto para desarrollo local
    SUPABASE_URL = "https://ptyemcxzvvzkkvxbeqxw.supabase.co"
    SUPABASE_KEY = "sb_publishable_IOE6cLvYfS7PuALxUXOWFw_uGtCQsSB"

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
LABORATORIO_UNICO = "BIOLOGÍA MOLECULAR"

MESES_DB = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

def guardar_datos_lims(tabla, año_val, mes_nombre, cantidad):
    mes_col = mes_nombre.lower()
    try:
        data = {
            "laboratorio": LABORATORIO_UNICO, 
            "año": año_val, 
            mes_col: cantidad, 
            "fecha_actualizacion": datetime.now().isoformat(),
            "registrado_por": st.session_state["username"]
        }
        supabase.table(tabla).upsert(data).execute()
        return True, "Datos actualizados correctamente"
    except Exception as e:
        return False, str(e)

# --- 4. INTERFAZ DASHBOARD ---
st.set_page_config(page_title="LIMS - Biología Molecular", layout="wide")
st.title("🧪 Laboratorio de Biología Molecular - Control de Muestras")

tab_ing, tab_proc, tab_graf, tab_prov, tab_avanzado = st.tabs([
    "📥 Ingresos", "⚙️ Procesados", "📊 Resumen General", "🌍 Análisis por Provincia", "📈 Análisis Avanzado"
])
# --- OBTENER DATOS FILTRADOS DESDE SUPABASE ---
with st.spinner("Conectando con el servidor de Biología Molecular..."):
    try:
        res_i = supabase.table("ingresos_muestras").select("*").eq("laboratorio", LABORATORIO_UNICO).execute()
        res_p = supabase.table("procesados_muestras").select("*").eq("laboratorio", LABORATORIO_UNICO).execute()
        df_i_full = pd.DataFrame(res_i.data) if res_i.data else pd.DataFrame()
        df_p_full = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error de conexión con la base de datos Supabase: {e}")
        st.info("Por favor, verifica que la URL y KEY en los Secrets de Streamlit sean correctas y que la base de datos no esté pausada.")
        df_i_full = pd.DataFrame()
        df_p_full = pd.DataFrame()

try:
    res_m = supabase.table("muestras_detalle").select("*").execute()
    df_muestras = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
except Exception:
    df_muestras = pd.DataFrame()
try:
    res_m = supabase.table("muestras_detalle").select("*").execute()
    df_muestras = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
except Exception:
    df_muestras = pd.DataFrame()

# --- TAB: INGRESOS ---
with tab_ing:
    col_f, col_t = st.columns([1, 4])
    with col_f:
        st.subheader("Ingresos")
        with st.form("form_ing", clear_on_submit=True):
            año = st.number_input("Año", value=datetime.now().year, key="a_ing")
            mes = st.selectbox("Mes", options=[m.capitalize() for m in MESES_DB], key="m_ing")
            cant = st.number_input("Cantidad", min_value=0, step=1)
            if st.form_submit_button("Guardar Ingreso"):
                ok, msg = guardar_datos_lims("ingresos_muestras", año, mes, cant)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)
    with col_t:
        if not df_i_full.empty:
            st.dataframe(df_i_full[["año"] + MESES_DB + ["total"]], use_container_width=True)

# --- TAB: PROCESADOS ---
with tab_proc:
    col_f2, col_t2 = st.columns([1, 4])
    with col_f2:
        st.subheader("Procesados")
        with st.form("form_proc", clear_on_submit=True):
            año_p = st.number_input("Año", value=datetime.now().year, key="a_proc")
            mes_p = st.selectbox("Mes", options=[m.capitalize() for m in MESES_DB], key="m_proc")
            cant_p = st.number_input("Cantidad", min_value=0, step=1)
            if st.form_submit_button("Guardar Procesado"):
                ok, msg = guardar_datos_lims("procesados_muestras", año_p, mes_p, cant_p)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)
    with col_t2:
        if not df_p_full.empty:
            st.dataframe(df_p_full[["año"] + MESES_DB + ["total"]], use_container_width=True)

# --- TAB: RESUMEN GENERAL ---
with tab_graf:
    st.header("📊 Rendimiento Histórico Anual")
    
    if not df_i_full.empty:
        años_resumen = sorted(df_i_full['año'].unique(), reverse=True)
        año_res_sel = st.selectbox("Seleccione el año:", options=años_resumen, key="sel_resumen_anual")
        
        df_i_res = df_i_full[df_i_full['año'] == año_res_sel]
        df_p_res = df_p_full[df_p_full['año'] == año_res_sel]
        
        total_ing = int(df_i_res['total'].sum()) if not df_i_res.empty else 0
        total_proc = int(df_p_res['total'].sum()) if not df_p_res.empty else 0
        pendiente = total_ing - total_proc
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Muestras Ingresadas", f"{total_ing}")
        m2.metric("Total Muestras Procesadas", f"{total_proc}")
        m3.metric("Muestras Pendientes", f"{pendiente}", delta_color="inverse")
        
        st.divider()
        
        # Gráfico comparativo de barras mensual para el año seleccionado
        v_i_mes = [df_i_res.iloc[0].get(m, 0) for m in MESES_DB] if not df_i_res.empty else [0]*12
        v_p_mes = [df_p_res.iloc[0].get(m, 0) for m in MESES_DB] if not df_p_res.empty else [0]*12
        
        fig = go.Figure(data=[
            go.Bar(name='Ingresadas', x=[m.capitalize() for m in MESES_DB], y=v_i_mes, marker_color='#1f77b4'),
            go.Bar(name='Procesadas', x=[m.capitalize() for m in MESES_DB], y=v_p_mes, marker_color='#2ca02c')
        ])
        fig.update_layout(barmode='group', title=f"Flujo Mensual de Trabajo - Gestión {año_res_sel}", yaxis_title="Cantidad de Muestras")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos registrados en el sistema para generar el resumen.")

# --- TAB: ANÁLISIS POR PROVINCIA ---
with tab_prov:
    st.header("🌍 Monitoreo Epidemiológico por Provincia")
    
    if df_muestras.empty:
        st.info("💡 Cargando datos de muestra para el análisis de provincias.")
        df_muestras = pd.DataFrame({
            "PROVINCIA": ["Pichincha", "Pichincha", "Guayas", "Guayas", "Azuay", "Manabí", "Manabí", "El Oro"],
            "POSITIVO": [6, 4, 12, 3, 2, 7, 1, 8],
            "NEGATIVO": [20, 15, 45, 12, 18, 22, 14, 19],
            "ENFERMEDAD/ DIAGNÓSTICO": ["Brucelosis", "Salmonella", "Brucelosis", "Mastitis", "Salmonella", "Brucelosis", "Mastitis", "Peste Porcina"],
            "ESPECIE": ["Bovino", "Porcino", "Bovino", "Bovino", "Porcino", "Bovino", "Caprino", "Porcino"]
        })

    df_prov_est = df_muestras.groupby("PROVINCIA").agg({"POSITIVO": "sum", "NEGATIVO": "sum"}).reset_index()
    df_prov_est["Total"] = df_prov_est["POSITIVO"] + df_prov_est["NEGATIVO"]

    kpi1, kpi2, kpi3 = st.columns(3)
    alertas_activas = df_prov_est[df_prov_est["POSITIVO"] > 5]["PROVINCIA"].count()
    kpi1.metric("Provincias en Alerta (>5 Positivos)", f"{alertas_activas}")
    kpi2.metric("Total Positivos Detectados", f"{df_prov_est['POSITIVO'].sum()}")
    kpi3.metric("Total Muestras Secuenciadas", f"{df_prov_est['Total'].sum()}")

    st.divider()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df_prov_est["Condición"] = df_prov_est["POSITIVO"].apply(lambda x: "Alerta (>5)" if x > 5 else "Estable")
        fig_alertas = px.bar(df_prov_est, x="PROVINCIA", y="POSITIVO", color="Condición",
                             color_discrete_map={"Alerta (>5)": "#ef553b", "Estable": "#636efa"}, text="POSITIVO",
                             title="Muestras Positivas por Provincia (Línea de Alerta)")
        fig_alertas.add_hline(y=5, line_dash="dash", line_color="red")
        st.plotly_chart(fig_alertas, use_container_width=True)

    with col_g2:
        fig_pie = go.Figure()
        fig_pie.add_trace(go.Bar(name='Positivos', x=df_prov_est['PROVINCIA'], y=df_prov_est['POSITIVO'], marker_color='#ef553b'))
        fig_pie.add_trace(go.Bar(name='Negativos', x=df_prov_est['PROVINCIA'], y=df_prov_est['NEGATIVO'], marker_color='#00cc96'))
        fig_pie.update_layout(barmode='stack', title="Relación Positivos vs Negativos")
        st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB: ANÁLISIS AVANZADO ---
with tab_avanzado:
    if not df_i_full.empty:
        años_disp = sorted(df_i_full['año'].unique(), reverse=True)
        
        st.subheader("🌐 Curvas de Tendencia de Biología Molecular")
        seleccion_años_global = st.multiselect("Selecciona años a comparar", options=años_disp, default=años_disp[:1])
        
        if seleccion_años_global:
            fig_global = go.Figure()
            for a in seleccion_años_global:
                sum_i = df_i_full[df_i_full['año'] == a][MESES_DB].sum()
                sum_p = df_p_full[df_p_full['año'] == a][MESES_DB].sum()
                
                fig_global.add_trace(go.Scatter(x=[m.capitalize() for m in MESES_DB], y=sum_i, name=f"Ingresos {a}", mode='lines+markers'))
                fig_global.add_trace(go.Scatter(x=[m.capitalize() for m in MESES_DB], y=sum_p, name=f"Procesados {a}", mode='lines', line=dict(dash='dash')))
            
            fig_global.update_layout(hovermode="x unified", title="Dinámica de Carga de Trabajo Mensual")
            st.plotly_chart(fig_global, use_container_width=True)
        
        st.divider()
        
        # Estadísticas operativas agregadas
        df_melted_i = df_i_full.melt(id_vars=['año'], value_vars=MESES_DB, var_name='Mes', value_name='Ingresadas')
        df_melted_p = df_p_full.melt(id_vars=['año'], value_vars=MESES_DB, var_name='Mes', value_name='Procesadas')
        df_stats = pd.merge(df_melted_i, df_melted_p, on=['año', 'Mes']).fillna(0)
        df_stats["Eficiencia (%)"] = (df_stats["Procesadas"] / df_stats["Ingresadas"].replace(0, 1)) * 100
        
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            st.markdown("#### 📊 Descriptores Estadísticos de Procesamiento")
            st.metric("Media de Muestras Procesadas / Mes", f"{round(df_stats['Procesadas'].mean(), 1)}")
            st.metric("Desviación Estándar de la Demanda", f"{round(df_stats['Ingresadas'].std(), 1)}")
            st.metric("Eficiencia Operativa Promedio", f"{round(df_stats['Eficiencia (%)'].mean(), 1)}%")
        with c_s2:
            fig_box = px.box(df_stats, y="Procesadas", title="Variabilidad Operativa Mensual (Distribución de Caja)")
            st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("Faltan datos históricos para procesar el modelado estadístico.")
