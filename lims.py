import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
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

# --- 2. GESTIÓN DE USUARIOS (12 CUENTAS) ---
# He definido una lista de 12 usuarios. Puedes cambiar las contraseñas aquí.
USUARIOS_PERMITIDOS = {
    "admin": "admin123",
    "maria.vasconez": "lab2026",
    "jorge.irazabal": "mbi123",
    "blanca.obando": "b123",
    "ivana.rea": "f123",
    "aalex.minda": "cpa123",
    "juan.gualotuna": "cp123",
    "iban.garcia": "cl123",
    "jose.erazo": "cip123",
    "paulette.andrade": "cpp123",
    "luis.andrade": "cpb123",
    "alexis.naula": "bmi123"
}

def login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("#")
        st.title("🔐 Acceso")
        st.info("Dirección de Diagnóstico de Inocuidad de los Alimentos y Control de Insumos Agropecuarios")
        
        with st.form("login_form"):
            user_input = st.text_input("Usuario").lower().strip()
            pass_input = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Iniciar Sesión")
            
            if btn_login:
                if user_input in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[user_input] == pass_input:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.success(f"Bienvenido {user_input.capitalize()}")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Bloqueo de seguridad: Si no está autenticado, se detiene el script aquí
if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- SIDEBAR: LOGOUT ---
with st.sidebar:
    st.markdown(f"👤 **Sesión:** `{st.session_state['username'].upper()}`")
    if st.button("Cerrar Sesión"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()

# --- 3. DICCIONARIOS Y UTILIDADES ---
LABORATORIOS = {
    1: "BROMATOLOGÍA", 2: "MICROBIOLOGÍA", 3: "FERTILIZANTES",
    4: "CONT. AGRÍCOLAS", 5: "CALIDAD DE PLAGUICIDAS", 6: "CALIDAD DE LECHE",
    7: "CALIDAD DE INSUMOS VET.", 8: "CONT. PECUARIOS", 
    9: "PRODUCTOS BIOLÓGICOS", 10: "BIOLOGÍA MOLECULAR"
}

MESES_DB = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

def guardar_datos_lims(tabla, lab_id, año_val, mes_nombre, cantidad):
    lab_nombre = LABORATORIOS.get(lab_id)
    mes_col = mes_nombre.lower()
    try:
        data = {
            "laboratorio": lab_nombre, 
            "año": año_val, 
            mes_col: cantidad, 
            "fecha_actualizacion": datetime.now().isoformat(),
            "registrado_por": st.session_state["username"] # Auditoría de usuario
        }
        supabase.table(tabla).upsert(data).execute()
        return True, "Datos actualizados correctamente"
    except Exception as e:
        return False, str(e)

# --- 4. INTERFAZ DASHBOARD ---
st.set_page_config(page_title="LIMS Dashboard", layout="wide")
st.title("🧪 Control de Análisis y Procesamiento de Muestras")

tab_ing, tab_proc, tab_graf, tab_avanzado = st.tabs([
    "📥 Ingresos", "⚙️ Procesados", "📊 Resumen General", "📈 Análisis Avanzado"
])

# OBTENER DATOS DESDE SUPABASE
res_i = supabase.table("ingresos_muestras").select("*").order("laboratorio").execute()
res_p = supabase.table("procesados_muestras").select("*").order("laboratorio").execute()
df_i_full = pd.DataFrame(res_i.data) if res_i.data else pd.DataFrame()
df_p_full = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()

# --- TAB: INGRESOS ---
with tab_ing:
    col_f, col_t = st.columns([1, 4])
    with col_f:
        st.subheader("Registro de Muestras Ingresadas")
        with st.form("form_ing", clear_on_submit=True):
            lab = st.selectbox("Laboratorio", options=list(LABORATORIOS.keys()), format_func=lambda x: LABORATORIOS[x])
            año = st.number_input("Año", value=datetime.now().year, key="a_ing")
            mes = st.selectbox("Mes", options=[m.capitalize() for m in MESES_DB], key="m_ing")
            cant = st.number_input("Cantidad", min_value=0, step=1)
            if st.form_submit_button("Guardar Ingreso"):
                ok, msg = guardar_datos_lims("ingresos_muestras", lab, año, mes, cant)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)
    with col_t:
        if not df_i_full.empty:
            st.dataframe(df_i_full[["laboratorio", "año"] + MESES_DB + ["total"]], use_container_width=True)

# --- TAB: PROCESADOS ---
with tab_proc:
    col_f2, col_t2 = st.columns([1, 4])
    with col_f2:
        st.subheader("Registro de Muestras Procesadas")
        with st.form("form_proc", clear_on_submit=True):
            lab_p = st.selectbox("Laboratorio", options=list(LABORATORIOS.keys()), format_func=lambda x: LABORATORIOS[x], key="sb_p")
            año_p = st.number_input("Año", value=datetime.now().year, key="a_proc")
            mes_p = st.selectbox("Mes", options=[m.capitalize() for m in MESES_DB], key="m_proc")
            cant_p = st.number_input("Cantidad", min_value=0, step=1)
            if st.form_submit_button("Guardar Procesado"):
                ok, msg = guardar_datos_lims("procesados_muestras", lab_p, año_p, mes_p, cant_p)
                if ok: st.success(msg); st.rerun()
                else: st.error(msg)
    with col_t2:
        if not df_p_full.empty:
            st.dataframe(df_p_full[["laboratorio", "año"] + MESES_DB + ["total"]], use_container_width=True)

# --- TAB: RESUMEN GENERAL ---
with tab_graf:
    st.header("📊 Resumen General de la Dirección")
    
    if not df_i_full.empty:
        # 1. Selector de año para el resumen
        años_resumen = sorted(df_i_full['año'].unique(), reverse=True)
        año_res_sel = st.selectbox("Seleccione el año para visualizar el resumen:", options=años_resumen, key="sel_resumen_anual")
        
        # 2. Filtrado de datos según el año seleccionado
        df_i_res = df_i_full[df_i_full['año'] == año_res_sel][['laboratorio', 'total']].rename(columns={'total': 'Ingresadas'})
        df_p_res = df_p_full[df_p_full['año'] == año_res_sel][['laboratorio', 'total']].rename(columns={'total': 'Procesadas'})
        
        # Unimos los datos de ingresos y procesados
        df_resumen = pd.merge(df_i_res, df_p_res, on="laboratorio", how="outer").fillna(0)
        
        if not df_resumen.empty:
            # 3. Métricas destacadas
            m1, m2, m3 = st.columns(3)
            total_ing = int(df_resumen['Ingresadas'].sum())
            total_proc = int(df_resumen['Procesadas'].sum())
            pendiente = total_ing - total_proc
            
            m1.metric(f"Total Ingresos ({año_res_sel})", f"{total_ing}")
            m2.metric(f"Total Procesados ({año_res_sel})", f"{total_proc}")
            m3.metric("Diferencia (Ing vs Proc)", f"{pendiente}", delta_color="inverse")
            
            st.divider()
            
            # 4. Gráfico de barras comparativo
            fig = go.Figure(data=[
                go.Bar(name='Ingresadas', x=df_resumen['laboratorio'], y=df_resumen['Ingresadas'], marker_color='#1f77b4'),
                go.Bar(name='Procesadas', x=df_resumen['laboratorio'], y=df_resumen['Procesadas'], marker_color='#2ca02c')
            ])
            
            fig.update_layout(
                barmode='group', 
                title=f"Comparativa por Laboratorio - Gestión {año_res_sel}",
                xaxis_title="Laboratorios",
                yaxis_title="Cantidad de Muestras",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 5. Tabla de datos detallada (opcional, para mayor claridad)
            with st.expander("Ver tabla de datos detallada"):
                st.table(df_resumen.set_index('laboratorio'))
        else:
            st.warning(f"No se encontraron datos procesados para el año {año_res_sel}.")
    else:
        st.info("No hay datos registrados en el sistema para generar el resumen.")

# --- TAB: ANÁLISIS AVANZADO ---
with tab_avanzado:
    if not df_i_full.empty:
        años_disp = sorted(df_i_full['año'].unique(), reverse=True)
        
        # 1. GRÁFICO GLOBAL COMPARATIVO
        st.subheader("🌐 Análisis Global de la Dirección de Inocuidad de los Alimentos y Control de Insumos Agropecuarios")
        seleccion_años_global = st.multiselect("Selecciona años para comparar", options=años_disp, default=años_disp[:2], key="global_years")
        
        if seleccion_años_global:
            fig_global = go.Figure()
            for a in seleccion_años_global:
                sum_i = df_i_full[df_i_full['año'] == a][MESES_DB].sum()
                sum_p = df_p_full[df_p_full['año'] == a][MESES_DB].sum()
                
                fig_global.add_trace(go.Scatter(x=[m.capitalize() for m in MESES_DB], y=sum_i, name=f"Ingresos {a}", mode='lines+markers'))
                fig_global.add_trace(go.Scatter(x=[m.capitalize() for m in MESES_DB], y=sum_p, name=f"Procesados {a}", mode='lines', line=dict(dash='dash')))
            
            fig_global.update_layout(hovermode="x unified", title="Tendencia Global: Ingresos vs Procesados")
            st.plotly_chart(fig_global, use_container_width=True)
        
        st.divider()
        
        # 2. ANÁLISIS POR LABORATORIO
        st.subheader("🔬 Análisis Detallado por Laboratorio")
        c1, c2 = st.columns(2)
        lab_sel = c1.selectbox("Seleccione Laboratorio", options=list(LABORATORIOS.values()))
        año_sel = c2.selectbox("Año de Referencia", options=años_disp)
        
        lab_norm = normalizar_texto(lab_sel)
        df_l_i = df_i_full[(df_i_full['laboratorio'].apply(normalizar_texto) == lab_norm) & (df_i_full['año'] == año_sel)]
        df_l_p = df_p_full[(df_p_full['laboratorio'].apply(normalizar_texto) == lab_norm) & (df_p_full['año'] == año_sel)]
        
        v_i = [df_l_i.iloc[0].get(m, 0) for m in MESES_DB] if not df_l_i.empty else [0]*12
        v_p = [df_l_p.iloc[0].get(m, 0) for m in MESES_DB] if not df_l_p.empty else [0]*12
            
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=[m.capitalize() for m in MESES_DB], y=v_i, name="Ingresos", mode='lines+markers', line=dict(color='#1f77b4')))
        fig_line.add_trace(go.Scatter(x=[m.capitalize() for m in MESES_DB], y=v_p, name="Procesados", mode='lines+markers', line=dict(color='#2ca02c')))
        fig_line.update_layout(hovermode="x unified", title=f"Flujo Mensual: {lab_sel} ({año_sel})")
        st.plotly_chart(fig_line, use_container_width=True)

        # 3. COMPARATIVA DE BARRAS POR LABORATORIO
        st.divider()
        st.subheader(f"📊 Comparativa Histórica Mensual: {lab_sel}")
        seleccion_años_lab = st.multiselect("Selecciona años a comparar para este laboratorio", options=años_disp, default=años_disp[:2], key="lab_years")
        
        if seleccion_años_lab:
            fig_hist = go.Figure()
            for a in seleccion_años_lab:
                d_i = df_i_full[(df_i_full['laboratorio'].apply(normalizar_texto) == lab_norm) & (df_i_full['año'] == a)]
                d_p = df_p_full[(df_p_full['laboratorio'].apply(normalizar_texto) == lab_norm) & (df_p_full['año'] == a)]
                
                v_i_bar = [d_i.iloc[0].get(m, 0) for m in MESES_DB] if not d_i.empty else [0]*12
                v_p_bar = [d_p.iloc[0].get(m, 0) for m in MESES_DB] if not d_p.empty else [0]*12
                
                fig_hist.add_trace(go.Bar(name=f"Ingresos {a}", x=[m.capitalize() for m in MESES_DB], y=v_i_bar))
                fig_hist.add_trace(go.Bar(name=f"Procesados {a}", x=[m.capitalize() for m in MESES_DB], y=v_p_bar))
            
            fig_hist.update_layout(barmode='group', xaxis_title="Meses", yaxis_title="Muestras")
            st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No hay datos suficientes para el análisis avanzado.")
