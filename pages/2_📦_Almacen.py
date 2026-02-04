import streamlit as st
import pandas as pd
from datetime import datetime
import time
import utils # Tu archivo de conexión

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")
supabase = utils.supabase 

st.title("🏭 Control de Almacén")

# 2. DEFINIR PESTAÑAS
tab_insumos, tab_herramientas = st.tabs(["🧱 Insumos (Consumibles)", "🔧 Herramientas (Activos)"])

# ==================================================
# 🟢 PESTAÑA 1: GESTIÓN DE INSUMOS
# ==================================================
with tab_insumos:
    st.header("Movimientos de Inventario")
    
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
    except: df_ins = pd.DataFrame()

    if df_ins.empty:
        st.warning("No hay insumos registrados. Ve a Configuración para agregar.")
    else:
        col_op, col_view = st.columns([1, 2])
        
        with col_op:
            st.markdown("### 📝 Registrar Movimiento")
            
            # Limpieza para evitar errores
            if "codigo" not in df_ins.columns: df_ins["codigo"] = df_ins["id"].astype(str)
            if "Descripcion" not in df_ins.columns: df_ins["Descripcion"] = "Sin Nombre"
            
            lista_insumos = [f"{row['codigo']} - {row['Descripcion']}" for i, row in df_ins.iterrows()]
            seleccion = st.selectbox("Seleccionar Insumo", lista_insumos)
            
            codigo_sel = seleccion.split(" - ")[0]
            item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
            
            st.info(f"📦 Stock Actual: **{item_actual['Cantidad']} {item_actual['Unidad']}**")
            
            cantidad_mov = st.number_input("Cantidad a mover", min_value=1.0, step=1.0)
            motivo = st.text_input("Motivo / Referencia (Opcional)", placeholder="Ej. Producción Lote 5")
            
            c_btn1, c_btn2 = st.columns(2)
            
            if c_btn1.button("📉 SALIDA (Consumo)", type="primary"):
                if item_actual['Cantidad'] >= cantidad_mov:
                    nuevo_stock = item_actual['Cantidad'] - cantidad_mov
                    try:
                        supabase.table("Insumos").update({"Cantidad": nuevo_stock}).eq("id", int(item_actual['id'])).execute()
                        st.success(f"✅ Salida registrada. Nuevo stock: {nuevo_stock}")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                else: st.error("⛔ Stock insuficiente.")

            if c_btn2.button("📈 ENTRADA (Surtido)"):
                nuevo_stock = item_actual['Cantidad'] + cantidad_mov
                try:
                    supabase.table("Insumos").update({"Cantidad": nuevo_stock}).eq("id", int(item_actual['id'])).execute()
                    st.success(f"✅ Entrada registrada. Nuevo stock: {nuevo_stock}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

        with col_view:
            st.markdown("### 📊 Existencias en Tiempo Real")
            cols_show = ["codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"]
            for c in cols_show:
                if c not in df_ins.columns: df_ins[c] = None
            st.dataframe(df_ins[cols_show], use_container_width=True)

# ==================================================
# 🔵 PESTAÑA 2: CONTROL DE HERRAMIENTAS (CORREGIDO)
# ==================================================
with tab_herramientas:
    # 1. Cargar Datos
    try:
        df_her = pd.DataFrame(supabase.table("Herramientas").select("*").order("id").execute().data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        df_her = pd.DataFrame()
        lista_personal = []

    # --- 🛡️ BLINDAJE ANTI-ERRORES ---
    # Si la tabla está vacía, la inicializamos con las columnas necesarias
    if df_her.empty:
        df_her = pd.DataFrame(columns=["id", "codigo", "Herramienta", "marca", "Responsable", "Estado", "descripcion"])

    # Aseguramos que existan las columnas clave aunque vengan vacías
    if "Responsable" not in df_her.columns: df_her["Responsable"] = "Bodega"
    df_her["Responsable"] = df_her["Responsable"].fillna("Bodega") # Rellenar nulos
    
    if "codigo" not in df_her.columns: df_her["codigo"] = ""
    if "Herramienta" not in df_her.columns: df_her["Herramienta"] = "Desconocido"
    if "marca" not in df_her.columns: df_her["marca"] = ""

    # Ahora sí podemos filtrar sin miedo al KeyError
    bodega = df_her[df_her['Responsable'] == 'Bodega']
    prestadas = df_her[df_her['Responsable'] != 'Bodega']

    c1, c2 = st.columns(2)

    # --- SECCIÓN PRESTAR ---
    with c1.form("prestar"):
        st.subheader("📤 Prestar Herramienta")
        
        l_bodega = []
        if not bodega.empty:
            l_bodega = [f"{r['id']} | {r['codigo']} - {r['Herramienta']} ({r['marca']})" for i, r in bodega.iterrows()]
        
        sel_p = st.selectbox("Herramienta Disponible", l_bodega)
        resp = st.selectbox("Se entrega a:", lista_personal)
        
        if st.form_submit_button("Confirmar Préstamo"):
            if sel_p and resp:
                id_h = int(sel_p.split(" | ")[0])
                supabase.table("Herramientas").update({"Responsable": resp}).eq("id", id_h).execute()
                
                try: # Registrar historial
                    supabase.table("Historial_Herramientas").insert({
                        "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                        "Herramienta": sel_p.split(" | ")[1], 
                        "Movimiento": "Préstamo", "Responsable": resp
                    }).execute()
                except: pass
                
                st.success(f"✅ Herramienta entregada a {resp}")
                time.sleep(1)
                st.rerun()
            else: st.warning("Datos incompletos.")

    # --- SECCIÓN DEVOLVER ---
    with c2.form("devolver"):
        st.subheader("📥 Devolver a Bodega")
        
        l_prest = []
        if not prestadas.empty:
            l_prest = [f"{r['id']} | {r['codigo']} - {r['Herramienta']} (Tiene: {r['Responsable']})" for i, r in prestadas.iterrows()]
            
        sel_d = st.selectbox("Herramienta Prestada", l_prest)
        estado_dev = st.selectbox("Estado de Devolución", ["BUEN ESTADO", "MAL ESTADO", "EN REPARACIÓN"])
        
        if st.form_submit_button("Confirmar Devolución"):
            if sel_d:
                id_h = int(sel_d.split(" | ")[0])
                nombre_clean = sel_d.split(" | ")[1]
                
                supabase.table("Herramientas").update({"Responsable": "Bodega", "Estado": estado_dev}).eq("id", id_h).execute()
                
                try:
                    supabase.table("Historial_Herramientas").insert({
                        "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                        "Herramienta": nombre_clean, "Movimiento": "Devolución",
                        "Responsable": "Bodega", "Detalle": estado_dev
                    }).execute()
                except: pass
                
                st.success("✅ Herramienta devuelta a Bodega")
                time.sleep(1)
                st.rerun()
            else: st.info("Nada por devolver.")

    st.divider()
    st.subheader("📋 Listado Global de Activos")
    
    filtro = st.text_input("🔍 Buscar en herramientas...", placeholder="Escribe código, nombre o responsable")
    
    df_view = df_her.copy()
    if filtro and not df_view.empty:
        mask = df_view.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)
        df_view = df_view[mask]

    cols_her_show = ["codigo", "Herramienta", "marca", "Responsable", "Estado", "descripcion"]
    # Asegurar que existan visualmente
    for c in cols_her_show:
        if c not in df_view.columns: df_view[c] = None

    st.dataframe(df_view, use_container_width=True, column_order=cols_her_show, hide_index=True)
