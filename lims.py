# Dentro de tu if enviar:
datos = {
    "origen": origen,
    "año": anio,
    "provincia": provincia,
    "programa": programa,
    "especie": especie,
    "tipo_de_muestra": muestra,
    "bacteria": bacteria,
    # Convertimos los nombres a minúsculas para que coincidan con la tabla SQL
    "amp": resultados['AMP'],
    "czo": resultados['CZO'],
    "caz": resultados['CAZ'],
    "cro": resultados['CRO'],
    "fep": resultados['FEP'],
    "etp": resultados['ETP'],
    "mem": resultados['MEM'],
    "gen": resultados['GEN'],
    "cip": resultados['CIP'],
    "nor": resultados['NOR'],
    "fos": resultados['FOS'],
    "tmp": resultados['TMP']
}

try:
    supabase.table("registros_resistencia").insert(datos).execute()
    st.success("✅ ¡Guardado en la base de datos SQL!")
except Exception as e:
    st.error(f"Error: {e}")
