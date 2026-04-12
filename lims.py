import streamlit as st
from supabase import create_client, Client

# ... (tu conexión a supabase sigue igual)

def guardar_resultados_relacionales(id_muestra, resultados_dict):
    try:
        # 1. Preparamos los datos para insertar varias filas
        # En tu tabla, cada antibiótico es un registro independiente
        filas_a_insertar = []
        
        for atb_codigo, interpretacion in resultados_dict.items():
            # Necesitamos el ID del antibiótico. 
            # Como ejemplo, usaremos una lógica donde mapeamos el código al ID.
            # (Lo ideal sería consultar la tabla 'antibioticos' primero)
            
            nueva_fila = {
                "identificacion_muestra": id_muestra,
                "interpretacion": interpretacion,
                # Aquí deberías poner el ID numérico del antibiótico 
                # correspondiente a 'AMP', 'CIP', etc.
                "antibiotico_id": obtener_id_atb(atb_codigo), 
                "valor_cim": "N/A" # O el valor que desees
            }
            filas_a_insertar.append(nueva_fila)
        
        # 2. Insertamos todas las filas de una vez en la tabla 'resultados'
        supabase.table("resultados").insert(filas_a_insertar).execute()
        st.success(f"✅ Se han registrado los 12 antibióticos para la muestra {id_muestra}")

    except Exception as e:
        st.error(f"Error al guardar: {e}")

# Función auxiliar para convertir el código (AMP) en el ID que espera tu tabla (int4)
def obtener_id_atb(codigo):
    # Esto es un ejemplo. Debes asegurarte de que estos IDs 
    # coincidan con los de tu tabla 'antibioticos'
    mapeo = {
        'AMP': 1, 'CIP': 2, 'FEP': 3, 'CRO': 4, 'CAZ': 5, 
        'CZO': 6, 'ETP': 7, 'FOS': 8, 'GEN': 9, 'MEM': 10, 
        'NOR': 11, 'TMP': 12
    }
    return mapeo.get(codigo)
