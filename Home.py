import streamlit as st
import utils
import time # <--- ESTO FALTABA Y CAUSABA EL ERROR EN HOME

st.set_page_config(page_title="Inicio", layout="wide")

# --- SISTEMA DE LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # MODO BLOQUEADO
    st.title("🔐 Acceso al Sistema ERP")
    st.markdown("El sistema está protegido. Por favor ingresa la contraseña maestra.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        password_input = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar al Sistema", type="primary"):
            # AQUI CAMBIA "admin123" POR TU CONTRASEÑA REAL
            if password_input == "admin123": 
                st.session_state["authenticated"] = True
                st.toast("✅ Acceso Concedido")
                time.sleep(1) # Ahora sí funcionará
                st.rerun()
            else:
                st.error("⛔ Contraseña incorrecta")
    
    st.stop() 

# --- CONTENIDO DEL SISTEMA ---
st.title("🏠 Bienvenido al Panel de Control")
st.success(f"Sesión Activa | Acceso Total Habilitado")

st.markdown("""
### 🚀 Accesos Directos
Selecciona una opción en el menú de la izquierda:
- **📦 Almacén:** Control de inventarios, entradas, salidas y préstamos.
- **⚙️ Configuración:** Alta de productos, clientes, personal y catálogos maestros.
""")
