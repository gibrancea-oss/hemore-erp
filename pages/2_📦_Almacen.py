import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import io
import utils # Tu archivo de conexión

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")
supabase = utils.supabase 

# --- FUNCIÓN AUXILIAR PARA DESCARGAR EXCEL (CORREGIDA) ---
def convertir_df_a_excel(df):
    output = io.BytesIO()
    # CAMBIO: Quitamos "engine='xlsxwriter'" para usar el motor por defecto
    with pd.ExcelWriter(output) as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    processed_data = output.getvalue()
    return processed_data

# --- FUNCIÓN AUXILIAR PARA FILTROS DE FECHA ---
def aplicar_filtro_fechas(df, columna_fecha, filtro_seleccionado):
    if df.empty: return df
    
    # Asegurar que la columna sea datetime
    df[columna_fecha] = pd.to_datetime(df[columna_fecha])
    hoy = pd.Timestamp.now().normalize()
    
    if filtro_seleccionado == "Hoy":
        df = df[df[columna_fecha].dt.date == hoy.date()]
        
    elif filtro_seleccionado == "Ayer":
        ayer = hoy - timedelta(days=1)
        df = df[df[columna_fecha].dt.date == ayer.date()]
        
    elif filtro_seleccionado == "Esta última semana":
        inicio = hoy - timedelta(days=7)
        df = df[df[columna_fecha] >= inicio]
        
    elif filtro_seleccionado == "Semana pasada":
        inicio = hoy - timedelta(days=14)
        fin = hoy - timedelta(days=7)
        df = df[(df[columna_fecha] >= inicio) & (df[columna_fecha] < fin)]
        
    elif filtro_seleccionado == "Último mes":
        inicio = hoy - timedelta(days=30)
        df = df[df[columna_fecha] >= inicio]
        
    elif filtro_seleccionado == "Mes pasado":
        inicio = hoy - timedelta(days=60)
        fin = hoy - timedelta(days=30)
        df = df[(df[columna_fecha] >= inicio) & (df[columna_fecha] < fin)]
        
    return df

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
        
        # Cargar Personal
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
        
    except: 
        df_ins = pd.DataFrame()
        lista_personal = []

    # --- TABS ---
    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial y Reportes"])

    # --- PESTAÑA 1: REGISTRAR MOVIMIENTOS ---
    with tab_op:
        if df_ins.empty:
            st.warning("No hay insumos registrados.")
        else:
            # Limpieza de datos
            if "codigo" not in df_ins.columns: df_ins["codigo"] = df_ins["id"].astype(str)
            if "Descripcion" not in df_ins.columns: df_ins["Descripcion"] = "Sin Nombre"
            
            # Selector de Tipo
            tipo_operacion = st.radio("¿Qué deseas hacer?", ["📤 Entrega a Operador (Salida)", "📥 Re-Stock (Entrada)"], horizontal=True)
            
            st.divider()
            
            c_form, c_info = st.columns([2, 1])
            
            with c_form:
                # BUSCADOR
                lista_busqueda = [f"{row['codigo']} | {row['Descripcion']}" for i, row in df_ins.iterrows()]
                seleccion = st.selectbox("🔍 Buscar Insumo (Escribe código o nombre)", lista_busqueda)
                
                # Datos del item
                codigo_sel = seleccion.split(" | ")[0]
                item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                
                cant_mov = st.number_input("Cantidad", min_value=1.0, step=1.0, value=1.0)

                # LÓGICA
                if "Entrega" in tipo_operacion:
                    # SALIDA
                    responsable = st.selectbox("👤 ¿A quién se le entrega?", lista_personal, placeholder="Escribe el nombre...")
                    
                    if st.button("Confirmar Entrega (Salida)", type="primary"):
                        if item_actual['Cantidad'] >= cant_mov:
                            if responsable:
                                nuevo_stock = item_actual['Cantidad'] - cant_mov
                                try:
                                    supabase.table("Insumos").update({"Cantidad": nuevo_stock}).eq("id", int(item_actual['id'])).execute()
                                    
                                    try:
                                        supabase.table("Historial_Insumos").insert({
                                            "fecha": datetime.now().strftime('%Y-%m-%d %H:%M'),
                                            "codigo": item_actual['codigo'],
                                            "descripcion": item_actual['Descripcion'],
                                            "tipo_movimiento": "Salida",
                                            "cantidad": cant_mov,
                                            "responsable": responsable
                                        }).execute()
                                    except: pass 
                                    
                                    st.success(f"✅ Entregado a {responsable}. Stock restante: {nuevo_stock}")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
                            else:
                                st.warning("Debes seleccionar a quién se le entrega.")
                        else:
                            st.error(f"⛔ Stock insuficiente. Solo tienes {item_actual['Cantidad']}.")
                            
                else:
                    # ENTRADA
                    st.info("ℹ️ Estás registrando una entrada de material al almacén.")
                    if st.button("Confirmar Re-Stock (Entrada)"):
                        nuevo_stock = item_actual['Cantidad'] + cant_mov
                        try:
                            supabase.table("Insumos").update({"Cantidad": nuevo_stock}).eq("id", int(item_actual['id'])).execute()
                            
                            try:
                                supabase.table("Historial_Insumos").insert({
                                    "fecha": datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    "codigo": item_actual['codigo'],
                                    "descripcion": item_actual['Descripcion'],
                                    "tipo_movimiento": "Re-stock",
                                    "cantidad": cant_mov,
                                    "responsable": "Almacén"
                                }).execute()
                            except: pass
                            
                            st.success(f"✅ Stock actualizado. Nuevo total: {nuevo_stock}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")

            # Tarjeta Informativa
            with c_info:
                st.metric(label="Stock Actual", value=f"{item_actual['Cantidad']} {item_actual['Unidad']}")
                if item_actual['Cantidad'] <= item_actual['stock_minimo']:
                    st.error(f"⚠️ Stock Bajo (Mín: {item_actual['stock_minimo']})")
                else:
                    st.success("Stock Saludable")

    # --- PESTAÑA 2: EXISTENCIAS ---
    with tab_exist:
        c_tit, c_down = st.columns([3, 1])
        c_tit.subheader("Inventario en Tiempo Real")
        
        if not df_ins.empty:
            cols_show = ["codigo", "Descripcion", "Cantidad", "Unidad", "stock_minimo"]
            for c in cols_show:
                if c not in df_ins.columns: df_ins[c] = None
            
            # Botón Descarga Excel (Existencias)
            try:
                excel_data = convertir_df_a_excel(df_ins[cols_show])
                c_down.download_button(
                    label="📥 Descargar Existencias",
                    data=excel_data,
                    file_name=f"Existencias_Insumos_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                c_down.error("Error creando Excel. Verifica requisitos.")

            filtro_ins = st.text_input("🔍 Filtrar tabla...", placeholder="Código o Descripción")
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

    # --- PESTAÑA 3: HISTORIAL Y REPORTES ---
    with tab_hist:
        st.subheader("📜 Historial de Movimientos")
        try:
            # Traer historial completo (o un limite grande)
            historial = pd.DataFrame(supabase.table("Historial_Insumos").select("*").order("id", desc=True).limit(500).execute().data)
            
            if not historial.empty:
                cols_h = ["fecha", "codigo", "descripcion", "tipo_movimiento", "cantidad", "responsable"]
                for c in cols_h:
                    if c not in historial.columns: historial[c] = "-"

                # --- FILTROS DE FECHA ---
                c_filt1, c_filt2 = st.columns([1, 2])
                opcion_fecha = c_filt1.selectbox(
                    "Filtrar por Fecha:",
                    ["Todos", "Hoy", "Ayer", "Esta última semana", "Semana pasada", "Último mes", "Mes pasado", "Personalizado"]
                )

                df_filtrado = historial.copy()
                df_filtrado['fecha_dt'] = pd.to_datetime(df_filtrado['fecha'])

                # Lógica Personalizada
                if opcion_fecha == "Personalizado":
                    fecha_inicio = c_filt2.date_input("Fecha Inicio", value=datetime.now().date())
                    fecha_fin = c_filt2.date_input("Fecha Fin", value=datetime.now().date())
                    if fecha_inicio and fecha_fin:
                         df_filtrado = df_filtrado[
                             (df_filtrado['fecha_dt'].dt.date >= fecha_inicio) & 
                             (df_filtrado['fecha_dt'].dt.date <= fecha_fin)
                         ]
                elif opcion_fecha != "Todos":
                    df_filtrado = aplicar_filtro_fechas(df_filtrado, 'fecha_dt', opcion_fecha)

                # Mostrar Tabla Filtrada
                st.dataframe(
                    df_filtrado[cols_h], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                # Botón Descarga Excel (Historial Filtrado)
                if not df_filtrado.empty:
                    try:
                        excel_hist = convertir_df_a_excel(df_filtrado[cols_h])
                        st.download_button(
                            label="📥 Descargar Reporte Filtrado",
                            data=excel_hist,
                            file_name=f"Reporte_Movimientos_{opcion_fecha}_{datetime.now().strftime('%d-%m')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except: pass
            else:
                st.info("Aún no hay movimientos registrados.")
        except Exception as e:
            st.info(f"No se pudo cargar el historial: {e}")

# ==================================================
# 🔧 OPCIÓN 2: CONTROL DE HERRAMIENTAS
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

    # --- 🛡️ BLINDAJE ANTI-KEYERROR ---
    if df_her.empty:
        df_her = pd.DataFrame(columns=["id", "codigo", "Herramienta", "marca", "Responsable", "Estado", "descripcion"])
    
    if "Responsable" not in df_her.columns: 
        if "responsable" in df_her.columns: df_her["Responsable"] = df_her["responsable"]
        else: df_her["Responsable"] = "Bodega"
    
    df_her["Responsable"] = df_her["Responsable"].fillna("Bodega")
    
    # Otras columnas seguras
    if "codigo" not in df_her.columns: df_her["codigo"] = ""
    if "marca" not in df_her.columns: df_her["marca"] = ""
    if "Herramienta" not in df_her.columns: df_her["Herramienta"] = "Sin Nombre"
    if "id" not in df_her.columns: df_her["id"] = 0

    bodega = df_her[df_her['Responsable'] == 'Bodega']
    prestadas = df_her[df_her['Responsable'] != 'Bodega']

    # --- TABS: OPERACION, EXISTENCIAS, HISTORIAL (NUEVO) ---
    tab_mov_h, tab_exist_h, tab_hist_h = st.tabs(["📝 Registrar Movimientos", "📋 Existencias", "📜 Historial y Reportes"])

    # --- PESTAÑA 1: MOVIMIENTOS ---
    with tab_mov_h:
        c1, c2 = st.columns(2)
        
        # --- PRESTAR ---
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
                        try:
                            supabase.table("Herramientas").update({"Responsable": resp}).eq("id", id_h).execute()
                            try:
                                supabase.table("Historial_Herramientas").insert({
                                    "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    "Herramienta": sel_p.split(" | ")[1], "Movimiento": "Préstamo", "Responsable": resp
                                }).execute()
                            except: pass
                            st.success(f"✅ Entregado a {resp}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.warning("Datos incompletos.")

        # --- DEVOLVER ---
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
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.info("No hay devoluciones pendientes.")

    # --- PESTAÑA 2: EXISTENCIAS ---
    with tab_exist_h:
        c_tit_h, c_down_h = st.columns([3, 1])
        c_tit_h.subheader("Ubicación de Activos")
        
        filtro_h = st.text_input("🔍 Rastrear herramienta...", placeholder="Código, Nombre o Responsable")
        df_view = df_her.copy()
        if filtro_h and not df_view.empty:
            mask = df_view.astype(str).apply(lambda x: x.str.contains(filtro_h, case=False)).any(axis=1)
            df_view = df_view[mask]
        
        cols_her_show = ["codigo", "Herramienta", "marca", "Responsable", "Estado", "descripcion"]
        for c in cols_her_show:
            if c not in df_view.columns: df_view[c] = None
        
        # Botón Descarga Excel
        if not df_view.empty:
            try:
                excel_her = convertir_df_a_excel(df_view[cols_her_show])
                c_down_h.download_button(
                    label="📥 Descargar Inventario",
                    data=excel_her,
                    file_name=f"Inventario_Herramientas_{datetime.now().strftime('%d-%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except: pass
            
        st.dataframe(df_view[cols_her_show], use_container_width=True, hide_index=True)

    # --- PESTAÑA 3: HISTORIAL (NUEVO) ---
    with tab_hist_h:
        st.subheader("📜 Historial de Préstamos")
        try:
            historial_h = pd.DataFrame(supabase.table("Historial_Herramientas").select("*").order("id", desc=True).limit(500).execute().data)
            
            if not historial_h.empty:
                # Normalizar columnas
                cols_hh = ["Fecha_Hora", "Herramienta", "Movimiento", "Responsable", "Detalle"]
                for c in cols_hh:
                     if c not in historial_h.columns: historial_h[c] = "-"
                
                # --- FILTROS DE FECHA ---
                c_filt1, c_filt2 = st.columns([1, 2])
                opcion_fecha_h = c_filt1.selectbox(
                    "Filtrar Préstamos por Fecha:",
                    ["Todos", "Hoy", "Ayer", "Esta última semana", "Semana pasada", "Último mes", "Mes pasado", "Personalizado"],
                    key="filt_her"
                )

                df_filtrado_h = historial_h.copy()
                df_filtrado_h['fecha_dt'] = pd.to_datetime(df_filtrado_h['Fecha_Hora'])

                if opcion_fecha_h == "Personalizado":
                    fecha_inicio_h = c_filt2.date_input("Inicio", value=datetime.now().date(), key="d1_h")
                    fecha_fin_h = c_filt2.date_input("Fin", value=datetime.now().date(), key="d2_h")
                    if fecha_inicio_h and fecha_fin_h:
                         df_filtrado_h = df_filtrado_h[
                             (df_filtrado_h['fecha_dt'].dt.date >= fecha_inicio_h) & 
                             (df_filtrado_h['fecha_dt'].dt.date <= fecha_fin_h)
                         ]
                elif opcion_fecha_h != "Todos":
                    df_filtrado_h = aplicar_filtro_fechas(df_filtrado_h, 'fecha_dt', opcion_fecha_h)

                # Mostrar Tabla
                st.dataframe(df_filtrado_h[cols_hh], use_container_width=True, hide_index=True)
                
                # Botón Descarga Excel (Historial Filtrado)
                if not df_filtrado_h.empty:
                    try:
                        excel_hist_h = convertir_df_a_excel(df_filtrado_h[cols_hh])
                        st.download_button(
                            label="📥 Descargar Reporte Historial",
                            data=excel_hist_h,
                            file_name=f"Reporte_Prestamos_{opcion_fecha_h}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except: pass

            else:
                st.info("No hay historial de movimientos.")
        except Exception as e:
            st.info(f"No se pudo cargar el historial: {e}")
