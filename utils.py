import streamlit as st
from supabase import create_client
import pandas as pd

# --- CONEXIÓN PRINCIPAL ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None

# ESTA ES LA LINEA QUE FALTA Y QUE ARREGLA EL ERROR:
# Creamos la variable 'supabase' para que los otros archivos la puedan usar
supabase = init_connection()

# --- FUNCIONES DE AYUDA (CACHÉ) ---
# Esto ayuda a que el sistema no sea lento con 50 usuarios
@st.cache_data(ttl=60)
def cargar_datos(tabla):
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table(tabla).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

def limpiar_cache():
    st.cache_data.clear()
# --- AGREGAR AL FINAL DE utils.py ---

def cargar_estilos():
    # Función parche para evitar el error en Home.py
    import streamlit as st
    st.markdown("""<style>.main {padding-top: 2rem;}</style>""", unsafe_allow_html=True)

def validar_login():
    # Función parche por si alguna página antigua la llama
    pass
