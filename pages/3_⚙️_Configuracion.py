import streamlit as st
import pandas as pd
import utils # Tu archivo de conexión
import time
import datetime

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- FUNCIÓN INTELIGENTE (Para Clientes, Proveedores y Herramientas) ---
def renderizar_catalogo_generico(nombre_modulo, tabla_db, columnas_visibles, config_campos):
    st.markdown(f"### 📂 Catálogo de {nombre_modulo}")
    
    # 1. Cargar Datos
    try:
        response = utils.supabase.table(tabla_db).select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error cargando {nombre_modulo}: {e}")
        return

    if df.empty:
        df = pd.DataFrame(columns=["id"] + list(config_campos.keys()))

    # Pestañas
    tab1, tab2 = st.tabs([f"➕ Nuevo {nombre_modulo}", "📋 Lista Completa y Edición"])

    # --- PESTAÑA 1: ALTA ---
    with tab1:
        st.write(f"Ingresa los datos del nuevo {nombre_modulo}.")
        with st.form(f"form_{tabla_db}", clear_on_submit=True):
            datos_a_guardar = {}
            claves = list(config_campos.keys())
            
            for i in range(0, len(claves), 2):
                c1, c2 = st.columns(2)
                key1 = claves[i]
                with c1:
                    if isinstance(config_campos[key1], list):
                        datos_a_guardar[key1] = st.selectbox(f"{key1.replace('_', ' ').title()}", config_campos[key1])
                    else:
                        datos_a_guardar[key1] = st.text_input(config_campos[key1])
                
                if i + 1 < len(claves):
                    key2 = claves[i+1]
                    with c2:
                        if isinstance(config_campos[key2], list):
                            datos_a_guardar[key2] = st.selectbox(f"{key2.replace('_', ' ').title()}", config_campos[key2])
                        else:
                            datos_a_guardar[key2] = st.text_input(config_campos[key2])

            st.write("---")
            if st.form_submit_button(f"💾 Guardar {nombre_modulo}"):
                if datos_a_guardar[claves[0]]:
                    utils.supabase.table(tabla_db).insert(datos_a_guardar).execute()
                    st.success("✅ Guardado correctamente")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("El primer campo es obligatorio.")

    # --- PESTAÑA 2: EDICIÓN ---
    with tab2:
        st.info("💡 Edita directamente en la tabla.")
        cols_finales = [c for c in columnas_visibles if c in df.columns]
        if not cols_finales: cols_finales = df.columns
        
        column_config = {"id": st.column_config.NumberColumn(disabled=True)}

        edited_df = st.data_editor(
            df[cols_finales],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{tabla_db}"
        )

        if st.button(f"🔄 Actualizar {nombre_modulo}"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {col: row[col] for col in cols_finales if col != 'id'}
                    if "id" in row and pd.notna(row["id"]):
                        utils.supabase.table(tabla_db).update(datos).eq("id", row["id"]).execute()
                    else:
                        utils.supabase.table(tabla_db).insert(datos).execute()
                except: pass
                bar.progress((index + 1) / total)
            bar.empty()
            st.success("✅ Actualizado.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores"]
)

# ==========================================
# 1. PERSONAL (Lógica Especializada RH)
# ==========================================
if opcion == "Personal":
    st.markdown("### 👥 Gestión de Recursos Humanos")
    
    # Cargar datos
    try:
        response = utils.supabase.table("Personal").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        
        # --- CORRECCIÓN DE ERROR DE FECHA ---
        # Convertimos el texto de la base de datos a formato FECHA REAL
        if not df.empty and "fecha_ingreso" in df.columns:
            df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors='coerce').dt.date
            
    except: df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "nombre", "puesto", "activo"])

    t1, t2 = st.tabs(["➕ Alta Personal", "📋 Kardex Completo"])

    with t1:
        st.write("Ficha de Ingreso")
        with st.form("alta_personal", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre Completo")
            puesto = col2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
            
            col3, col4 = st.columns(2)
            nacimiento = col3.text_input("Año Nacimiento (Ej. 1995)")
            domicilio = col4.text_input("Domicilio")
            
            col5, col6 = st.columns(2)
            curp = col5.text_input("CURP")
            rfc = col6.text_input("RFC")
            
            fecha_ingreso = st.date_input("Fecha de Ingreso", value=datetime.date.today())

            if st.form_submit_button("Guardar Empleado"):
                if nombre:
                    datos = {
                        "nombre": nombre, "puesto": puesto, 
                        "anio_nacimiento": nacimiento, "domicilio": domicilio,
                        "curp": curp, "rfc": rfc, 
                        "fecha_ingreso": fecha_ingreso.isoformat(),
                        "activo": True
                    }
                    utils.supabase.table("Personal").insert(datos).execute()
                    st.success(f"✅ {nombre} registrado.")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("El nombre es obligatorio")

    with t2:
        st.info("Desmarca la casilla 'Activo' para dar de baja sin borrar historial.")
        
        column_config = {
            "id": st.column_config.NumberColumn(disabled=True, width="small"),
            "nombre": st.column_config.TextColumn("Nombre", width="medium"),
            "puesto": st.column_config.SelectboxColumn("Puesto", options=["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"]),
            "fecha_ingreso": st.column_config.DateColumn("Ingreso", format="DD/MM/YYYY"),
            "activo": st.column_config.CheckboxColumn("¿Activo?")
        }
        
        cols_ver = ["id", "nombre", "puesto", "anio_nacimiento", "domicilio", "curp", "rfc", "fecha_ingreso", "activo"]
        cols_reales = [c for c in cols_ver if c in df.columns]

        edited_df = st.data_editor(
            df[cols_reales],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            height=500,
            key="editor_personal"
        )

        if st.button("💾 Actualizar Personal"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {c: row[c] for c in cols_reales if c != 'id'}
                    
                    # Convertimos la fecha a string para guardarla
                    if "fecha_ingreso" in datos and datos["fecha_ingreso"]:
                         datos["fecha_ingreso"] = str(datos["fecha_ingreso"])

                    if pd.notna(row["id"]):
                        utils.supabase.table("Personal").update(datos).eq("id", row["id"]).execute()
                    else:
                        utils.supabase.table("Personal").insert(datos).execute()
                except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Base actualizada")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# ==========================================
# 2. INSUMOS (Lógica Especializada Almacén)
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "Nombre", "Cantidad", "Unidad", "stock_minimo"])

    t1, t2 = st.tabs(["➕ Alta de Insumo", "📋 Inventario Maestro"])

    with t1:
        with st.form("alta_insumo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nuevo_nombre = c1.text_input("Descripción del Insumo")
            nueva_unidad = c2.selectbox("Unidad de Medida", lista_unidades)
            
            c3, c4 = st.columns(2)
            nueva_cant = c3.number_input("Cantidad Inicial", min_value=0.0, step=1.0)
            nuevo_min = c4.number_input("Stock Mínimo (Alerta)", value=5.0)
            
            if st.form_submit_button("Guardar Insumo"):
                if nuevo_nombre:
                    utils.supabase.table("Insumos").insert({
                        "Nombre": nuevo_nombre, "Unidad": nueva_unidad,
                        "Cantidad": nueva_cant, "stock_minimo": nuevo_min
                    }).execute()
                    st.success(f"✅ {nuevo_nombre} agregado.")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Descripción obligatoria")

    with t2:
        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Nombre": st.column_config.TextColumn("Descripción del Insumo", width="large", required=True),
            "Cantidad": st.column_config.NumberColumn("Stock Actual"),
            "Unidad": st.column_config.SelectboxColumn("Unidad", options=lista_unidades, required=True),
            "stock_minimo": st.column_config.NumberColumn("Stock Mínimo ⚠️")
        }
        
        cols_ver = ["id", "Nombre", "Cantidad", "Unidad", "stock_minimo"]
        cols_reales = [c for c in cols_ver if c in df.columns]

        edited_df = st.data_editor(
            df[cols_reales],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            height=500,
            key="editor_insumos"
        )

        if st.button("💾 Guardar Inventario"):
            bar = st.progress(0, text="Actualizando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {c: row[c] for c in cols_reales if c != 'id'}
                    if pd.notna(row["id"]):
                        utils.supabase.table("Insumos").update(datos).eq("id", row["id"]).execute()
                    else:
                        utils.supabase.table("Insumos").insert(datos).execute()
                except: pass
                bar.progress((index+1)/total)
            bar.empty()
            st.success("✅ Inventario actualizado")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# ==========================================
# 3. OTROS MÓDULOS (Lógica Genérica)
# ==========================================
elif opcion == "Herramientas":
    renderizar_catalogo_generico(
        "Herramientas", "Herramientas", 
        ["id", "Herramienta", "Estado", "Ubicacion"], 
        {"Herramienta": "Nombre Herramienta", "Estado": ["BUENO", "REGULAR", "MALO"], "Ubicacion": "Ubicación"}
    )

elif opcion == "Clientes":
    renderizar_catalogo_generico(
        "Clientes", "Clientes", 
        ["id", "nombre", "telefono", "direccion", "email"], 
        {"nombre": "Cliente / Empresa", "telefono": "Teléfono", "direccion": "Dirección", "email": "Correo"}
    )

elif opcion == "Proveedores":
    renderizar_catalogo_generico(
        "Proveedores", "Proveedores", 
        ["id", "empresa", "contacto", "telefono", "rfc"], 
        {"empresa": "Empresa", "contacto": "Contacto", "telefono": "Teléfono", "rfc": "RFC"}
    )
