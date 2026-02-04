import streamlit as st
import pandas as pd
import utils # Tu archivo de conexión
import time
import datetime

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- FUNCIÓN INTELIGENTE MEJORADA (Soporta fechas y más campos) ---
def renderizar_catalogo(nombre_modulo, tabla_db, columnas_visibles, config_campos):
    st.markdown(f"### 📂 Catálogo de {nombre_modulo}")
    
    # 1. Cargar Datos
    try:
        # Traemos todo ordenado por ID
        response = utils.supabase.table(tabla_db).select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error cargando {nombre_modulo}: {e}")
        return

    if df.empty:
        # Creamos columnas vacías basadas en la configuración si no hay datos
        cols = ["id"] + list(config_campos.keys())
        df = pd.DataFrame(columns=cols)

    # Pestañas
    tab1, tab2 = st.tabs([f"➕ Nuevo {nombre_modulo}", "📋 Lista Completa y Edición"])

    # --- PESTAÑA 1: ALTA (FORMULARIO) ---
    with tab1:
        st.write(f"Ingresa los datos del nuevo {nombre_modulo}.")
        with st.form(f"form_{tabla_db}", clear_on_submit=True):
            datos_a_guardar = {}
            
            # Organizamos los campos en columnas de 2 en 2 para que se vea ordenado
            claves = list(config_campos.keys())
            
            # Iteramos sobre los campos configurados
            for i in range(0, len(claves), 2):
                c1, c2 = st.columns(2)
                
                # Campo 1 (Izquierda)
                key1 = claves[i]
                tipo1 = config_campos[key1]
                
                with c1:
                    if isinstance(tipo1, list): # Es una lista -> Selectbox
                        datos_a_guardar[key1] = st.selectbox(f"{key1.replace('_', ' ').title()}", tipo1)
                    elif "Fecha" in str(key1) or "fecha" in str(key1): # Es fecha -> Date Input
                        datos_a_guardar[key1] = st.date_input(f"{key1.replace('_', ' ').title()}", value=datetime.date.today()).isoformat()
                    elif "Activo" in str(tipo1): # Es checkbox oculto (siempre True al crear)
                         datos_a_guardar[key1] = True
                    else: # Texto normal
                        datos_a_guardar[key1] = st.text_input(f"{tipo1}")

                # Campo 2 (Derecha) - Solo si existe un siguiente campo
                if i + 1 < len(claves):
                    key2 = claves[i+1]
                    tipo2 = config_campos[key2]
                    with c2:
                        if isinstance(tipo2, list):
                            datos_a_guardar[key2] = st.selectbox(f"{key2.replace('_', ' ').title()}", tipo2)
                        elif "Fecha" in str(key2) or "fecha" in str(key2):
                            datos_a_guardar[key2] = st.date_input(f"{key2.replace('_', ' ').title()}", value=datetime.date.today()).isoformat()
                        elif "Activo" in str(tipo2):
                             datos_a_guardar[key2] = True
                        else:
                            datos_a_guardar[key2] = st.text_input(f"{tipo2}")

            st.write("---")
            if st.form_submit_button(f"💾 Guardar Nuevo {nombre_modulo}"):
                # Validar que al menos el primer campo tenga datos (generalmente el nombre)
                primera_llave = claves[0]
                if datos_a_guardar[primera_llave]:
                    try:
                        utils.supabase.table(tabla_db).insert(datos_a_guardar).execute()
                        st.success("✅ Registrado correctamente")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning(f"El campo {primera_llave} es obligatorio.")

    # --- PESTAÑA 2: LISTA Y EDICIÓN ---
    with tab2:
        st.info("💡 Aquí tienes la lista completa. Modifica cualquier dato directamente en la tabla.")
        
        # Filtramos columnas para mostrar solo lo que pediste
        # Aseguramos que 'id' no sea editable y 'activo' sea checkbox
        column_config = {
            "id": st.column_config.NumberColumn(disabled=True),
            "activo": st.column_config.CheckboxColumn("¿Activo?", help="Desmarca para dar de baja"),
        }

        # Aseguramos que las columnas existan en el DF antes de mostrarlas
        cols_finales = [c for c in columnas_visibles if c in df.columns]
        if not cols_finales: cols_finales = df.columns # Fallback

        edited_df = st.data_editor(
            df[cols_finales],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            height=500, # Tabla más alta para ver más gente
            key=f"editor_{tabla_db}"
        )

        if st.button(f"🔄 Actualizar Cambios en {nombre_modulo}"):
            bar = st.progress(0, text="Guardando cambios...")
            total = len(edited_df)
            
            for index, row in edited_df.iterrows():
                try:
                    datos_update = {col: row[col] for col in cols_finales if col != 'id'}
                    
                    if "id" in row and pd.notna(row["id"]):
                        utils.supabase.table(tabla_db).update(datos_update).eq("id", row["id"]).execute()
                    else:
                        utils.supabase.table(tabla_db).insert(datos_update).execute()
                except Exception as e:
                    pass 
                bar.progress((index + 1) / total)
            
            bar.empty()
            st.success("✅ Base de datos actualizada.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# --- MENÚ LATERAL ---
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores"]
)

st.title(f"Administración de {opcion}")

# --- CONFIGURACIÓN DE CADA MÓDULO ---
if opcion == "Personal":
    # DEFINICIÓN DE CAMPOS PARA PERSONAL
    campos_personal = {
        "nombre": "Nombre Completo",
        "puesto": ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"],
        "anio_nacimiento": "Año de Nacimiento (Ej. 1995)",
        "domicilio": "Domicilio Completo",
        "curp": "CURP",
        "rfc": "RFC",
        "fecha_ingreso": "Fecha de Ingreso", # El código detecta 'fecha' y pone calendario
        "activo": "Activo (Check)"
    }
    
    cols_vista = ["id", "nombre", "puesto", "anio_nacimiento", "domicilio", "curp", "rfc", "fecha_ingreso", "activo"]
    
    renderizar_catalogo("Personal", "Personal", cols_vista, campos_personal)

elif opcion == "Insumos":
    renderizar_catalogo(
        "Insumos", "Insumos", 
        ["id", "Nombre", "Cantidad", "Unidad"], 
        {"Nombre": "Nombre Insumo", "Cantidad": "Stock Inicial", "Unidad": "Unidad (Kg, Pzas)"}
    )

elif opcion == "Herramientas":
    renderizar_catalogo(
        "Herramientas", "Herramientas", 
        ["id", "Herramienta", "Estado", "Ubicacion"], 
        {"Herramienta": "Nombre", "Estado": ["BUENO", "REGULAR", "MALO"], "Ubicacion": "Ubicación"}
    )

elif opcion == "Clientes":
    renderizar_catalogo(
        "Clientes", "Clientes", 
        ["id", "nombre", "telefono", "direccion", "email"], 
        {"nombre": "Cliente", "telefono": "Teléfono", "direccion": "Dirección", "email": "Email"}
    )

elif opcion == "Proveedores":
    renderizar_catalogo(
        "Proveedores", "Proveedores", 
        ["id", "empresa", "contacto", "telefono", "rfc"], 
        {"empresa": "Empresa", "contacto": "Contacto", "telefono": "Teléfono", "rfc": "RFC"}
    )
