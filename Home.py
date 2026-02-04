import streamlit as st
import utils

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
                time.sleep(1)
                st.rerun()
            else:
                st.error("⛔ Contraseña incorrecta")
    
    st.stop() # Detiene el código aquí si no hay login

# --- CONTENIDO DEL SISTEMA (SOLO VISIBLE SI YA ENTRASTE) ---
st.title("🏠 Bienvenido al Panel de Control")
st.success(f"Sesión Activa | Acceso Total Habilitado")

st.markdown("""
### 🚀 Accesos Directos
Selecciona una opción en el menú de la izquierda:
- **📦 Almacén:** Control de inventarios, entradas y salidas.
- **⚙️ Configuración:** Alta de productos, clientes y personal.
""")
