import streamlit as st
from supabase import create_client, Client

# 1. Configuración de Conexión a Supabase
# (Asegúrate de que tus st.secrets tengan estas claves)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# Inicializamos la variable global de conexión
supabase = init_connection()

# 2. Función de Seguridad (EL CANDADO)
def validar_login():
    """
    Esta función se pone al principio de cada página.
    Si el usuario no ha iniciado sesión, DETIENE todo y le pide ir al Home.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.warning("🔒 Acceso Bloqueado. Debes iniciar sesión primero.")
        st.info("Ve a la página de **Inicio (Home)** para ingresar tu contraseña.")
        st.stop() # <--- ESTO ES LO IMPORTANTE: Frena la carga de la página
