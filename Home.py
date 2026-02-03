import streamlit as st
import plotly.express as px
import pandas as pd
import utils # Importamos tu archivo de herramientas

# Configuración de página (SIEMPRE PRIMERO)
st.set_page_config(page_title="Hemore Cloud", page_icon="🏭", layout="wide")

utils.cargar_estilos()
supabase = utils.init_connection()

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Hemore ERP")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if password == "HEMORE2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
else:
    # --- DASHBOARD PRINCIPAL ---
    st.title("🏭 Dashboard General")
    st.success(f"Bienvenido, Ing. Gibran. Sistema conectado.")
    
    col1, col2 = st.columns(2)
    
    # Cargar datos frescos para el dashboard
    with st.spinner("Actualizando métricas..."):
        df_insumos = pd.DataFrame(supabase.table("Insumos").select("Insumo, Cantidad").execute().data)
        df_herramientas = pd.DataFrame(supabase.table("Herramientas").select("Responsable").execute().data)

    with col1:
        st.subheader("📦 Stock Crítico")
        if not df_insumos.empty:
            st.plotly_chart(px.bar(df_insumos, x='Insumo', y='Cantidad'), use_container_width=True)
            
    with col2:
        st.subheader("🔧 Herramientas")
        if not df_herramientas.empty:
            df_herramientas['Estado'] = df_herramientas['Responsable'].apply(lambda x: 'Disponible' if x == 'Bodega' else 'Prestado')
            st.plotly_chart(px.pie(df_herramientas, names='Estado', title="Uso de Activos"), use_container_width=True)