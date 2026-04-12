import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. Configuración de la página (Solo debe aparecer una vez al principio)
st.set_page_config(page_title="LIMS Resistencia RAM", layout="wide")

# 2. Conexión con Google Sheets
# IMPORTANTE: Asegúrate de que este link sea de una HOJA DE CÁLCULO de Google, no un archivo de Drive común.
url = "https://drive.google.com/file/d/13jfBryqSa6Lb9u7pYxsfccwhvAly8-9z/view?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Lista de antibióticos
atbs = ['AMP', 'CIP', 'FEP', 'CRO', 'CAZ', 'CZO', 'ETP', 'FOS', 'GEN', 'MEM', 'NOR', 'TMP']

st.title("🔬 LIMS - Registro de Resistencia Antimicrobiana")
st.markdown("---")

# 4. Formulario de Entrada
with st.form("registro_principal"):
    c1, c2 = st.columns(2)
    with c1:
        id_muestra = st.text_input("🆔 ID de Muestra / Código Paciente")
    with c2:
        fecha = st.date_input("📅 Fecha de Proceso", date.today())

    st.write("### 🧫 Resultados del Panel (S/I/R)")
    
    # Creamos 4 columnas para que queden 3 antibióticos por fila
    cols = st.columns(4)
    res = {}
    for i, atb in enumerate(atbs):
        with cols[i % 4]:
            res[atb] = st.selectbox(f"**{atb}**", ["S", "I", "R"], key=atb)

    st.markdown("---")
    boton_guardar = st.form_submit_button("💾 Guardar en la Nube")

    if boton_guardar:
        if id_muestra:
            try:
                # Preparar nueva fila
                nueva_fila = pd.DataFrame([{
                    "ID": id_muestra,
                    "Fecha": str(fecha),
                    **res
                }])

                # Leer datos actuales, concatenar y subir
                existente = conn.read(spreadsheet=url)
                actualizado = pd.concat([existente, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=url, data=actualizado)
                
                st.success(f"✅ Muestra {id_muestra} guardada con éxito.")
            except Exception as e:
                st.error(f"Error al conectar con Google Sheets: {e}")
        else:
            st.warning("⚠️ Por favor, ingresa un ID de muestra antes de guardar.")

# 5. Alertas Microbiológicas (Solo se muestran si se detectan ciertos perfiles)
if res['MEM'] == 'R' or res['ETP'] == 'R':
    st.warning("⚠️ **ALERTA:** Posible Carbapenemasa detectada. Verificar cepa.")

if res['MEM'] == 'R' and res['ETP'] == 'R' and res['CIP'] == 'R':
    st.error("🚨 **ALERTA:** Perfil de multirresistencia detectado (Carbapenémicos + Quinolonas).")

# 6. Histórico y Estadísticas
st.markdown("---")
st.header("📊 Histórico y Estadísticas")

if st.button("🔄 Actualizar Historial"):
    try:
        df_historico = conn.read(spreadsheet=url)
        
        # Tabla de datos
        st.subheader("Registros recientes")
        st.dataframe(df_historico, use_container_width=True)

        # Gráfico de resistencia
        st.subheader("📈 Análisis por Antibiótico")
        atb_analizar = st.selectbox("Selecciona un antibiótico para ver estadística:", atbs)
        
        if atb_analizar in df_historico.columns:
            conteo = df_historico[atb_analizar].value_counts()
            st.bar_chart(conteo)
        
    except Exception as e:
        st.info("Aún no hay datos para mostrar o el archivo no es accesible.")
