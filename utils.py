import streamlit as st
from supabase import create_client
import pandas as pd
import qrcode
import io
import base64

# --- CONEXIÓN A SUPABASE ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

# --- VALIDAR SESIÓN ---
def validar_login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        st.warning("🔒 Acceso denegado. Por favor inicia sesión en el Inicio.")
        st.stop() # Detiene la ejecución si no está logueado

# --- ESTILOS COMUNES ---
def cargar_estilos():
    st.markdown("""
        <style>
        .stMetric { background-color: #f0f2f6; border-radius: 10px; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- GENERADOR QR ---
def generar_qr_b64(texto):
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(str(texto))
        qr.make(fit=True)
        buffer = io.BytesIO()
        qr.make_image(fill='black', back_color='white').save(buffer, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    except: return None