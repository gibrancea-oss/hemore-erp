import streamlit as st
import pandas as pd
import utils # Tu archivo de conexión
import time
import datetime

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- FUNCIÓN INTELIGENTE (Para Clientes, Proveedores y Herramientas) ---
def renderizar_catalogo_generico(nombre_modulo, tabla_db, columnas_visibles, config_campos):
    st.markdown(f"### 📂 Catálogo de {nombre_modulo}")
    
    try:
        response = utils.supabase.table(tabla_db).select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error cargando {nombre_modulo}: {e}")
        return

    if df.empty:
        df = pd.DataFrame(columns=["id"] + list(config_campos.keys()))

    tab1, tab2 = st.tabs([f"➕ Nuevo {nombre_modulo}", "📋 Lista Completa"])

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
# 1. PERSONAL
# ==========================================
if opcion == "Personal":
    st.markdown("### 👥 Gestión de Recursos Humanos")
    try:
        response = utils.supabase.table("Personal").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if not df.empty and "fecha_ingreso" in df.columns:
            df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors='coerce').dt.date
    except: df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "nombre", "puesto", "activo"])

    t1, t2 = st.tabs(["➕ Alta Personal", "📋 Kardex Completo"])

    with t1:
        with st.form("alta_personal", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre Completo")
            puesto = col2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
            
            col3, col4 = st.columns(2)
            nacimiento = col3.text_input("Año Nacimiento")
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
                    st.warning("Nombre obligatorio")

    with t2:
        column_config = {
            "id": st.column_config.NumberColumn(disabled=True, width="small"),
            "nombre": st.column_config.TextColumn("Nombre", width="medium"),
            "puesto": st.column_config.SelectboxColumn("Puesto", options=["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"], width="medium"),
            "fecha_ingreso": st.column_config.DateColumn("Ingreso", format="DD/MM/YYYY", width="small"),
            "activo": st.column_config.CheckboxColumn("¿Activo?", width="small"),
            "anio_nacimiento": st.column_config.TextColumn("Año", width="small"),
            "domicilio": st.column_config.TextColumn("Domicilio", width="large"),
            "curp": st.column_config.TextColumn("CURP", width="medium"),
            "rfc": st.column_config.TextColumn("RFC", width="medium")
        }
        
        cols_ver = ["id", "nombre", "puesto", "anio_nacimiento", "domicilio", "curp", "rfc", "fecha_ingreso", "activo"]
        cols_reales = [c for c in cols_ver if c in df.columns]

        edited_df = st.data_editor(
            df[cols_reales],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_personal"
        )

        if st.button("💾 Actualizar Personal"):
            bar = st.progress(0, text="Guardando...")
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    datos = {c: row[c] for c in cols_reales if c != 'id'}
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
# 2. INSUMOS (SOLUCIÓN ERROR "NOT NULL INSUMO")
# ==========================================
elif opcion == "Insumos":
    lista_unidades = ["Pzas", "Kg", "Lts", "Mts", "Cajas", "Paquetes", "Rollos", "Juegos", "Botes", "Galones"]
    
    st.markdown("### 📦 Gestión de Almacén e Insumos")
    
    # 1. CARGAR DATOS
    try:
        response = utils.supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        
        # --- LIMPIEZA AUTOMÁTICA ---
        if not df.empty:
            if "Descripcion" not in df.columns: df["Descripcion"] = None
            for col_sucia in ["Insumo", "nombre", "Nombre"]:
                if col_sucia in df.columns:
                    df["Descripcion"] = df["Descripcion"].fillna(df[col_sucia])
            
            if "codigo" not in df.columns: df["codigo"] = df["id"].astype(str)
            else: df["codigo"] = df["codigo"].fillna(df["id"].astype(str))

            if "stock_minimo" not in df.columns: df["stock_minimo"] = 5.0
            if "Stock_Minimo" in df.columns:
                 df["stock_minimo"] = df["stock_minimo"].fillna(df["Stock_Minimo"])

            cols_a_borrar = ["Insumo", "nombre", "Nombre", "Stock_Minimo"]
            df = df.drop(columns=[c for c in cols_a_borrar if c in df.columns], errors='ignore')

    except Exception as e: 
        st.error(f"Error de limpieza: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"])

    t1, t2 = st.tabs(["➕ Alta de Insumo", "📋 Inventario Maestro"])

    # --- PESTAÑA ALTA CON FIX DE ERROR ---
    with t1:
        with st.form("alta_insumo", clear_on_submit=True):
            st.write("Datos del Insumo")
            
            col_cod, col_nom = st.columns([1, 3]) 
            nuevo_codigo = col_cod.text_input("Código / SKU", placeholder="Ej. HEM-CL-001", help="Código único alfanumérico")
            nuevo_nombre = col_nom.text_input("Descripción del Insumo")
            
            c1, c2, c3 = st.columns(3)
            nueva_unidad = c1.selectbox("Unidad", lista_unidades)
            nueva_cant = c2.number_input("Cantidad", min_value=0.0, step=1.0)
            nuevo_min = c3.number_input("Stock Mínimo", value=5.0)
            
            if st.form_submit_button("Guardar Insumo"):
                if nuevo_nombre and nuevo_codigo:
                    try:
                        # --- EL TRUCO DEL ESPEJO ---
                        # Enviamos el nombre tanto a 'Descripcion' como a 'Insumo'
                        # para satisfacer a la base de datos antigua y a la nueva.
                        datos_insert = {
                            "codigo": nuevo_codigo, 
                            "Descripcion": nuevo_nombre,
                            "Insumo": nuevo_nombre,  # <--- ESTO ARREGLA EL ERROR 23502
                            "Unidad": nueva_unidad,
                            "Cantidad": nueva_cant, 
                            "stock_minimo": nuevo_min
                        }
                        utils.supabase.table("Insumos").insert(datos_insert).execute()
                        st.success(f"✅ Insumo {nuevo_codigo} agregado exitosamente.")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        # Si falla, intentamos sin 'Insumo' (por si acaso ya la borraste)
                        if "column \"Insumo\" of relation \"Insumos\" does not exist" in str(e):
                             datos_insert.pop("Insumo")
                             utils.supabase.table("Insumos").insert(datos_insert).execute()
                             st.success(f"✅ Insumo {nuevo_codigo} agregado.")
                             st.rerun()
                        else:
                            st.error(f"Error al guardar: {e}")
                else:
                    st.warning("El Código y la Descripción son obligatorios.")

    # --- PESTAÑA EDICIÓN MAESTRA ---
    with t2:
        column_config = {
            "id": st.column_config.NumberColumn("ID Sistema", disabled=True, width="small"),
            "codigo": st.column_config.TextColumn("Código SKU", required=True, width="medium", help="Código alfanumérico único"),
            "Descripcion": st.column_config.TextColumn("Descripción del Insumo", width="large", required=True),
            "Cantidad": st.column_config.NumberColumn("Stock Actual", width="small", min_value=0),
            "Unidad": st.column_config.SelectboxColumn("Unidad", options=lista_unidades, required=True, width="small"),
            "stock_minimo": st.column_config.NumberColumn("Mínimo ⚠️", width="small")
        }
        
        cols_ver = ["id", "codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"]
        for c in cols_ver:
            if c not in df.columns: df[c] = None
            
        edited_df = st.data_editor(
            df[cols_ver],
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            height=500,
            key="editor_insumos_codigos_v2"
        )

        if st.button("💾 Guardar Cambios en Inventario"):
            bar = st.progress(0, text="Guardando cambios...")
            total = len(edited_df)
            
            for index, row in edited_df.iterrows():
                try:
                    # Al editar, también actualizamos ambas columnas para mantener consistencia
                    datos = {
                        "codigo": row["codigo"], 
                        "Descripcion": row["Descripcion"],
                        "Insumo": row["Descripcion"], # Espejo al editar también
                        "Cantidad": row["Cantidad"],
                        "Unidad": row["Unidad"],
                        "stock_minimo": row["stock_minimo"]
                    }
                    
                    if pd.notna(row["id"]):
                        utils.supabase.table("Insumos").update(datos).eq("id", row["id"]).execute()
                    else:
                        utils.supabase.table("Insumos").insert(datos).execute()
                except Exception as e:
                    # Fallback si falla el espejo
                    try:
                        datos.pop("Insumo")
                        if pd.notna(row["id"]):
                            utils.supabase.table("Insumos").update(datos).eq("id", row["id"]).execute()
                        else:
                            utils.supabase.table("Insumos").insert(datos).execute()
                    except: pass
                
                bar.progress((index+1)/total)
            
            bar.empty()
            st.success("✅ Inventario actualizado.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# ==========================================
# 3. OTROS MÓDULOS
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
