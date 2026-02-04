import streamlit as st
import pandas as pd
from datetime import datetime
import time
import utils # Tu archivo de conexión

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")
supabase = utils.supabase 

# ==========================================
# MENÚ LATERAL
# ==========================================
st.sidebar.title("🏭 Almacén Central")
opcion_almacen = st.sidebar.radio(
    "Selecciona Operación:",
    ["Insumos (Consumibles)", "Herramientas (Activos)"]
)

st.title(f"Control de {opcion_almacen.split(' (')[0]}")

# ==================================================
# 🧱 OPCIÓN 1: GESTIÓN DE INSUMOS
# ==================================================
if "Insumos" in opcion_almacen:
    # 1. Cargar Datos
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
    except: df_ins = pd.DataFrame()

    tab_mov, tab_exist = st.tabs(["📝 Registrar Movimientos (Entradas/Salidas)", "📊 Existencias en Tiempo Real"])

    # --- PESTAÑA 1: MOVIMIENTOS ---
    with tab_mov:
        st.subheader("Operación de Inventario")
        
        if df_ins.empty:
            st.warning("No hay insumos registrados. Ve a Configuración para agregar.")
        else:
            # Limpieza de datos
            if "codigo" not in df_ins.columns: df_ins["codigo"] = df_ins["id"].astype(str)
            if "Descripcion" not in df_ins.columns: df_ins["Descripcion"] = "Sin Nombre"
            
            c_form, _ = st.columns([1, 1]) 
            with c_form:
                st.markdown("##### Selecciona el producto:")
                lista_insumos = [f"{row['codigo']} - {row['Descripcion']}" for i, row in df_ins.iterrows()]
                seleccion = st.selectbox("Buscar Insumo", lista_insumos)
                
                # Obtener datos
                codigo_sel = seleccion.split(" - ")[0]
                item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                
                st.info(f"📦 En Stock: **{item_actual['Cantidad']} {item_actual['Unidad']}**")
                
                st.markdown("##### Detalle del Movimiento:")
                c_cant, c_motivo = st.columns([1, 2])
                cantidad_mov = c_cant.number_input("Cantidad", min_value=1.0, step=1.0)
                motivo = c_motivo.text_input("Motivo / Referencia", placeholder="Ej. Lote 5 / Factura A1")
                
                col_salida, col_entrada = st.columns(2)
                
                # BOTÓN SALIDA
                if col_salida.button("📉 SALIDA (Consumo)", type="primary", use_container_width=True):
                    if item_actual['Cantidad'] >= cantidad_mov:
                        nuevo_stock = item_actual['Cantidad'] - cantidad_mov
                        try:
                            supabase.table("Insumos").update({"Cantidad": nuevo_stock}).eq("id", int(item_actual['id'])).execute()
                            st.success(f"✅ Salida registrada. Stock Nuevo: {nuevo_stock}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                    else:
                        st.error("⛔ Stock insuficiente.")

                # BOTÓN ENTRADA
                if col_entrada.button("📈 ENTRADA (Surtido)", use_container_width=True):
                    nuevo_stock = item_actual['Cantidad'] + cantidad_mov
                    try:
                        supabase.table("Insumos").update({"Cantidad": nuevo_stock}).eq("id", int(item_actual['id'])).execute()
                        st.success(f"✅ Entrada registrada. Stock Nuevo: {nuevo_stock}")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- PESTAÑA 2: EXISTENCIAS ---
    with tab_exist:
        st.subheader("Inventario Actualizado")
        if not df_ins.empty:
            cols_show = ["codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"]
            for c in cols_show:
                if c not in df_ins.columns: df_ins[c] = None
            
            filtro_ins = st.text_input("🔍 Buscar en inventario...", placeholder="Código o Descripción")
            df_show = df_ins[cols_show].copy()
            
            if filtro_ins:
                mask = (
                    df_show["codigo"].astype(str).str.contains(filtro_ins, case=False, na=False) | 
                    df_show["Descripcion"].astype(str).str.contains(filtro_ins, case=False, na=False)
                )
                df_show = df_show[mask]

            st.dataframe(
                df_show, 
                use_container_width=True,
                column_config={
                    "stock_minimo": st.column_config.NumberColumn("Mínimo", help="Nivel de reorden"),
                    "Descripcion": st.column_config.TextColumn("Descripción", width="large")
                },
                hide_index=True
            )
        else:
            st.info("No hay datos para mostrar.")

# ==================================================
# 🔧 OPCIÓN 2: CONTROL DE HERRAMIENTAS (CORREGIDO)
# ==================================================
elif "Herramientas" in opcion_almacen:
    # 1. Cargar Datos
    try:
        df_her = pd.DataFrame(supabase.table("Herramientas").select("*").order("id").execute().data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        df_her = pd.DataFrame()
        lista_personal = []

    # --- 🛡️ BLINDAJE ANTI-ERRORES (AQUÍ ESTÁ LA SOLUCIÓN) ---
    # Aseguramos que existan las columnas clave en el DataFrame aunque no vengan de la DB
    if "Responsable" not in df_her.columns: df_her["Responsable"] = "Bodega"
    df_her["Responsable"] = df_her["Responsable"].fillna("Bodega")
    
    if "codigo" not in df_her.columns: df_her["codigo"] = ""
    if "marca" not in df_her.columns: df_her["marca"] = ""
    if "Herramienta" not in df_her.columns: df_her["Herramienta"] = "Sin Nombre"
    if "id" not in df_her.columns: df_her["id"] = 0

    # Ahora filtramos con seguridad
    bodega = df_her[df_her['Responsable'] == 'Bodega']
    prestadas = df_her[df_her['Responsable'] != 'Bodega']

    # --- TABS SEPARADOS ---
    tab_mov_h, tab_exist_h = st.tabs(["📝 Registrar Movimientos (Préstamo/Devolución)", "📋 Existencias en Tiempo Real"])

    # --- PESTAÑA 1: MOVIMIENTOS ---
    with tab_mov_h:
        c1, c2 = st.columns(2)

        # --- PANEL IZQUIERDO: PRESTAR ---
        with c1:
            st.info("📤 **SALIDA DE HERRAMIENTA**")
            with st.form("prestar"):
                l_bodega = []
                if not bodega.empty:
                    l_bodega = [f"{r['id']} | {r['codigo']} - {r['Herramienta']} ({r['marca']})" for i, r in bodega.iterrows()]
                
                sel_p = st.selectbox("Seleccionar Herramienta (En Bodega)", l_bodega)
                resp = st.selectbox("Entregar a:", lista_personal)
                
                if st.form_submit_button("Confirmar Préstamo", type="primary"):
                    if sel_p and resp:
                        id_h = int(sel_p.split(" | ")[0])
                        # Intentamos actualizar en la base de datos
                        try:
                            supabase.table("Herramientas").update({"Responsable": resp}).eq("id", id_h).execute()
                            # Historial
                            try:
                                supabase.table("Historial_Herramientas").insert({
                                    "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    "Herramienta": sel_p.split(" | ")[1], 
                                    "Movimiento": "Préstamo", "Responsable": resp
                                }).execute()
                            except: pass
                            
                            st.success(f"✅ Entregado a {resp}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar (Verifica que la columna 'Responsable' exista en Supabase): {e}")
                    else: st.warning("Datos incompletos.")

        # --- PANEL DERECHO: DEVOLVER ---
        with c2:
            st.warning("📥 **DEVOLUCIÓN A BODEGA**")
            with st.form("devolver"):
                l_prest = []
                if not prestadas.empty:
                    l_prest = [f"{r['id']} | {r['codigo']} - {r['Herramienta']} (Tiene: {r['Responsable']})" for i, r in prestadas.iterrows()]
                    
                sel_d = st.selectbox("Seleccionar Herramienta (Prestada)", l_prest)
                estado_dev = st.selectbox("Estado al devolver", ["BUEN ESTADO", "MAL ESTADO", "EN REPARACIÓN"])
                
                if st.form_submit_button("Confirmar Devolución"):
                    if sel_d:
                        id_h = int(sel_d.split(" | ")[0])
                        nombre_clean = sel_d.split(" | ")[1]
                        
                        try:
                            supabase.table("Herramientas").update({"Responsable": "Bodega", "Estado": estado_dev}).eq("id", id_h).execute()
                            # Historial
                            try:
                                supabase.table("Historial_Herramientas").insert({
                                    "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    "Herramienta": nombre_clean, "Movimiento": "Devolución",
                                    "Responsable": "Bodega", "Detalle": estado_dev
                                }).execute()
                            except: pass
                            
                            st.success("✅ Devuelto a Bodega")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                    else: st.info("No hay devoluciones pendientes.")

    # --- PESTAÑA 2: EXISTENCIAS ---
    with tab_exist_h:
        st.subheader("Ubicación de Activos")
        
        filtro_h = st.text_input("🔍 Rastrear herramienta...", placeholder="Código, Nombre o Responsable")
        
        df_view = df_her.copy()
        if filtro_h and not df_view.empty:
            mask = df_view.astype(str).apply(lambda x: x.str.contains(filtro_h, case=False)).any(axis=1)
            df_view = df_view[mask]

        cols_her_show = ["codigo", "Herramienta", "marca", "Responsable", "Estado", "descripcion"]
        # Aseguramos columnas visuales
        for c in cols_her_show:
            if c not in df_view.columns: df_view[c] = None

        st.dataframe(
            df_view, 
            use_container_width=True,
            column_order=cols_her_show,
            hide_index=True
        )
