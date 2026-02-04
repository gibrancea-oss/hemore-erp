import streamlit as st
import pandas as pd
import utils # Tu archivo de conexión
import time

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- FUNCIÓN INTELIGENTE (Crea las pantallas automáticamente) ---
def renderizar_catalogo(nombre_modulo, tabla_db, columnas_visibles, columnas_nuevas):
    st.markdown(f"### 📂 Catálogo de {nombre_modulo}")
    
    # 1. Cargar Datos
    try:
        response = utils.supabase.table(tabla_db).select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error cargando {nombre_modulo}: {e}")
        return

    # Si está vacía, crear estructura
    if df.empty:
        df = pd.DataFrame(columns=["id"] + list(columnas_nuevas.keys()))

    # Pestañas
    tab1, tab2 = st.tabs([f"➕ Nuevo {nombre_modulo}", "✏️ Editar Todo"])

    # --- PESTAÑA 1: ALTA ---
    with tab1:
        with st.form(f"form_{tabla_db}", clear_on_submit=True):
            col1, col2 = st.columns(2)
            datos_a_guardar = {}
            
            # Generamos los campos del formulario automáticamente
            keys = list(columnas_nuevas.keys())
            # Campo 1 (Ej. Nombre)
            datos_a_guardar[keys[0]] = col1.text_input(columnas_nuevas[keys[0]])
            
            # Campo 2 (Ej. Teléfono o Puesto) - Si existe
            if len(keys) > 1:
                if isinstance(columnas_nuevas[keys[1]], list): # Si es lista, usa Selectbox
                    datos_a_guardar[keys[1]] = col2.selectbox("Opción", columnas_nuevas[keys[1]])
                else:
                    datos_a_guardar[keys[1]] = col2.text_input(columnas_nuevas[keys[1]])
            
            # Campos extra (si hay más de 2, los ponemos abajo)
            for k in keys[2:]:
                datos_a_guardar[k] = st.text_input(columnas_nuevas[k])

            if st.form_submit_button("Guardar"):
                if datos_a_guardar[keys[0]]: # Si el primer campo tiene datos
                    utils.supabase.table(tabla_db).insert(datos_a_guardar).execute()
                    st.success("✅ Guardado correctamente")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("El primer campo es obligatorio.")

    # --- PESTAÑA 2: EDICIÓN ---
    with tab2:
        st.info("💡 Edita directamente en la tabla y presiona Guardar.")
        
        # Filtramos columnas para no mostrar IDs ni fechas raras
        cols_finales = [c for c in columnas_visibles if c in df.columns]
        df_editor = df[cols_finales] if not df.empty else df

        edited_df = st.data_editor(
            df_editor,
            num_rows="dynamic", # Permite agregar filas abajo
            use_container_width=True,
            key=f"editor_{tabla_db}"
        )

        if st.button(f"💾 Guardar Cambios en {nombre_modulo}"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            
            # Actualización inteligente fila por fila
            for index, row in edited_df.iterrows():
                try:
                    # Preparamos los datos limpios para subir
                    datos_update = {col: row[col] for col in columnas_visibles if col != 'id'}
                    
                    if "id" in row and pd.notna(row["id"]):
                        # Actualizar existente
                        utils.supabase.table(tabla_db).update(datos_update).eq("id", row["id"]).execute()
                    else:
                        # Es una fila nueva creada en el editor
                        utils.supabase.table(tabla_db).insert(datos_update).execute()
                except Exception as e:
                    pass # Ignoramos errores menores de filas vacías
                bar.progress((index + 1) / total)
            
            bar.empty()
            st.success("✅ Base de datos actualizada.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# --- MENÚ LATERAL PRINCIPAL ---
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores"]
)

st.title(f"Configuración de {opcion}")

# --- LÓGICA DE NAVEGACIÓN ---
if opcion == "Personal":
    # Tabla: Personal | Columnas a ver: id, nombre, puesto, activo
    # Formulario Nuevo: nombre (Label), puesto (Lista de opciones)
    renderizar_catalogo(
        "Personal", 
        "Personal", 
        ["id", "nombre", "puesto", "activo"],
        {"nombre": "Nombre Completo", "puesto": ["Operador", "Supervisor", "Almacén", "Mantenimiento"], "activo": "Activo (True/False)"}
    )

elif opcion == "Insumos":
    # Asumimos que tu tabla Insumos tiene columnas: 'Nombre', 'Cantidad', 'Unidad'
    # Ajusta los nombres de columnas según tu DB real
    renderizar_catalogo(
        "Insumos", 
        "Insumos", 
        ["id", "Nombre", "Cantidad", "Unidad"], 
        {"Nombre": "Nombre del Insumo", "Cantidad": "Stock Inicial", "Unidad": "Unidad (Pzas, Kg, Lts)"}
    )

elif opcion == "Herramientas":
    renderizar_catalogo(
        "Herramientas", 
        "Herramientas", 
        ["id", "Herramienta", "Estado", "Ubicacion"], 
        {"Herramienta": "Nombre Herramienta", "Estado": ["BUENO", "REGULAR", "MALO"], "Ubicacion": "Ubicación en Almacén"}
    )

elif opcion == "Clientes":
    renderizar_catalogo(
        "Clientes", 
        "Clientes", 
        ["id", "nombre", "telefono", "direccion", "email"], 
        {"nombre": "Nombre Cliente / Empresa", "telefono": "Teléfono", "direccion": "Dirección", "email": "Correo"}
    )

elif opcion == "Proveedores":
    renderizar_catalogo(
        "Proveedores", 
        "Proveedores", 
        ["id", "empresa", "contacto", "telefono", "rfc"], 
        {"empresa": "Nombre Empresa", "contacto": "Nombre Contacto", "telefono": "Teléfono", "rfc": "RFC"}
    )
