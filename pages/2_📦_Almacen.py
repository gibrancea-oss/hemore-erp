import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import io
import os
import utils 
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")

# --- 🔒 SEGURIDAD ---
utils.validar_login() 
# --------------------

supabase = utils.supabase 

# --- CLASE PDF PERSONALIZADA ---
class PDF(FPDF):
    def header(self):
        # 1. LOGO
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33) 
        else:
            self.set_font('Arial', 'B', 20)
            self.cell(40, 10, 'HEMORE', 0, 0, 'L')

        # 2. TÍTULO (Variable según el tipo de doc, lo seteamos luego o usamos uno genérico)
        # Para simplificar, lo dejamos dinámico en la función de generación
        self.ln(1)

    def footer(self):
        self.set_y(-40)
        self.set_font('Arial', '', 8)
        # Firmas
        self.cell(90, 0, '_______________________________', 0, 0, 'C')
        self.cell(10, 0, '', 0, 0)
        self.cell(90, 0, '_______________________________', 0, 1, 'C')
        self.ln(4)
        self.cell(90, 5, 'Entrega (Nombre y Firma)', 0, 0, 'C')
        self.cell(10, 5, '', 0, 0)
        self.cell(90, 5, 'Recibe (Nombre y Firma)', 0, 1, 'C')
        
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- GENERADOR PDF: RECIBO DE ENTREGA (Salida a Cliente) ---
def generar_pdf_entrega(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    
    # Título Manual
    pdf.set_xy(0, 10) 
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Recibo de Entrega', 0, 1, 'C')
    
    # Folio y Fecha
    pdf.set_font('Arial', 'B', 10)
    pdf.set_xy(140, 25)
    pdf.cell(25, 6, "Folio:", 0, 0, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, str(folio), 0, 1, 'L')
    
    pdf.set_xy(140, 31)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 6, "Fecha:", 0, 0, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, datos_cabecera['fecha'], 0, 1, 'L')

    pdf.set_y(45) 
    y_start = pdf.get_y()
    
    # CAJAS: PROVEEDOR (HEMORE) -> CLIENTE (DESTINO)
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, " Proveedor (Origen)", 1, 0, 'L', True)
    pdf.cell(95, 6, " Cliente (Destino)", 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 25, "", 1, 0) 
    pdf.cell(95, 25, "", 1, 0) 
    
    # Izquierda: HEMORE
    pdf.set_xy(12, y_start + 8) 
    info_prov = (
        f"{datos_cabecera['prov_nombre']}\n"
        f"{datos_cabecera['prov_dir']}\n"
        f"Col. {datos_cabecera['prov_col']}, CP: {datos_cabecera['prov_cp']}\n"
        f"RFC: {datos_cabecera['prov_rfc']}"
    )
    pdf.multi_cell(90, 4, info_prov)
    
    # Derecha: CLIENTE
    pdf.set_xy(107, y_start + 8)
    info_cli = (
        f"{datos_cabecera['cli_nombre']}\n"
        f"{datos_cabecera['cli_dir']}\n"
        f"Col. {datos_cabecera['cli_col']}, CP: {datos_cabecera['cli_cp']}\n"
        f"RFC: {datos_cabecera['cli_rfc']}"
    )
    pdf.multi_cell(90, 4, info_cli)
    
    pdf.set_xy(10, y_start + 35) 
    _dibujar_tabla_productos(pdf, datos_cabecera, df_productos)
    return pdf.output(dest='S').encode('latin-1')

# --- GENERADOR PDF: ENTRADA DE MATERIAL (Llegada de Proveedor) ---
def generar_pdf_entrada(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    
    # Título Manual
    pdf.set_xy(0, 10) 
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Constancia de Entrada', 0, 1, 'C')
    
    # Folio y Fecha
    pdf.set_font('Arial', 'B', 10)
    pdf.set_xy(140, 25)
    pdf.cell(25, 6, "Folio Entrada:", 0, 0, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, str(folio), 0, 1, 'L')
    
    pdf.set_xy(140, 31)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 6, "Fecha:", 0, 0, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, datos_cabecera['fecha'], 0, 1, 'L')

    pdf.set_y(45) 
    y_start = pdf.get_y()
    
    # CAJAS: PROVEEDOR (ORIGEN) -> HEMORE (DESTINO)
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, " Proveedor (Origen)", 1, 0, 'L', True)
    pdf.cell(95, 6, " Receptor (Destino)", 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 25, "", 1, 0) 
    pdf.cell(95, 25, "", 1, 0) 
    
    # Izquierda: PROVEEDOR EXTERNO
    pdf.set_xy(12, y_start + 8) 
    info_prov = (
        f"{datos_cabecera['prov_nombre']}\n"
        f"{datos_cabecera['prov_dir']}\n"
        f"Col. {datos_cabecera['prov_col']}, CP: {datos_cabecera['prov_cp']}\n"
        f"RFC: {datos_cabecera['prov_rfc']}"
    )
    pdf.multi_cell(90, 4, info_prov)
    
    # Derecha: HEMORE (NOSOTROS)
    pdf.set_xy(107, y_start + 8)
    info_hemore = "HEMORE INDUSTRIAS\nCalle Falsa 123\nPuebla, Pue.\nRFC: HEM000000XXX\nAlmacén Central"
    pdf.multi_cell(90, 4, info_hemore)
    
    pdf.set_xy(10, y_start + 35) 
    _dibujar_tabla_productos(pdf, datos_cabecera, df_productos)
    return pdf.output(dest='S').encode('latin-1')

def _dibujar_tabla_productos(pdf, datos_cabecera, df_productos):
    # Encabezados
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 7, "O.C.", 1, 0, 'C', True)
    pdf.cell(30, 7, "Codigo", 1, 0, 'C', True)
    pdf.cell(95, 7, "Descripcion", 1, 0, 'C', True)
    pdf.cell(20, 7, "Color", 1, 0, 'C', True)
    pdf.cell(20, 7, "Cantidad", 1, 1, 'C', True)
    
    # Filas
    pdf.set_font('Arial', '', 8)
    for index, row in df_productos.iterrows():
        col_oc = str(datos_cabecera['oc'])
        col_cod = str(row['Código'])
        col_desc = str(row['Descripción'])[:55]
        col_color = str(row['Color'])
        col_cant = str(row['Cantidad'])
        
        pdf.cell(25, 7, col_oc, 1, 0, 'C')
        pdf.cell(30, 7, col_cod, 1, 0, 'C')
        pdf.cell(95, 7, col_desc, 1, 0, 'L')
        pdf.cell(20, 7, col_color, 1, 0, 'C')
        pdf.cell(20, 7, col_cant, 1, 1, 'C')

    # Observaciones
    pdf.ln(8)
    pdf.set_font('Arial', 'B', 9)
    pdf.write(5, "Observaciones: ")
    pdf.set_font('Arial', '', 9)
    obs_text = datos_cabecera.get('observaciones', '')
    if obs_text: pdf.write(5, obs_text)
    else: pdf.write(5, "_"*110)

# --- FUNCIONES AUXILIARES ---
def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        df.to_excel(writer, index=False, sheet_name='Recibo')
    processed_data = output.getvalue()
    return processed_data

def aplicar_filtro_fechas(df, columna_fecha, filtro_seleccionado):
    if df.empty: return df
    df[columna_fecha] = pd.to_datetime(df[columna_fecha])
    hoy = pd.Timestamp.now().normalize()
    if filtro_seleccionado == "Hoy": df = df[df[columna_fecha].dt.date == hoy.date()]
    elif filtro_seleccionado == "Ayer": 
        ayer = hoy - timedelta(days=1)
        df = df[df[columna_fecha].dt.date == ayer.date()]
    return df

# ==========================================
# MENÚ LATERAL
# ==========================================
st.sidebar.title("🏭 Almacén Central")
opcion_almacen = st.sidebar.radio(
    "Selecciona Operación:",
    ["Insumos (Consumibles)", "Herramientas (Activos)", "Recibos de Entrega OC", "Entrada de Material"]
)

st.title(f"Control de {opcion_almacen.split(' (')[0]}")

# ==================================================
# 🧱 OPCIÓN 1: INSUMOS (INTACTO)
# ==================================================
if "Insumos" in opcion_almacen:
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: df_ins = pd.DataFrame(); lista_personal = []

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial y Reportes"])
    with tab_op:
        if df_ins.empty: st.warning("No hay insumos.")
        else:
            if "codigo" not in df_ins.columns: df_ins["codigo"] = df_ins["id"].astype(str)
            if "Descripcion" not in df_ins.columns: df_ins["Descripcion"] = "Sin Nombre"
            tipo_operacion = st.radio("Acción:", ["📤 Entrega (Salida)", "📥 Re-Stock (Entrada)"], horizontal=True)
            c_form, c_info = st.columns([2, 1])
            with c_form:
                lista_busqueda = [f"{row['codigo']} | {row['Descripcion']}" for i, row in df_ins.iterrows()]
                seleccion = st.selectbox("Buscar:", lista_busqueda)
                codigo_sel = seleccion.split(" | ")[0]
                item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                cant_mov = st.number_input("Cantidad", min_value=1.0, value=1.0)
                if "Entrega" in tipo_operacion:
                    responsable = st.selectbox("Entregar a:", lista_personal)
                    if st.button("Confirmar Salida", type="primary"):
                        if item_actual['Cantidad'] >= cant_mov:
                            new_st = item_actual['Cantidad'] - cant_mov
                            supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                            try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": item_actual['codigo'], "descripcion": item_actual['Descripcion'], "tipo_movimiento": "Salida", "cantidad": cant_mov, "responsable": responsable}).execute()
                            except: pass
                            st.success("✅ Salida registrada"); time.sleep(1); st.rerun()
                        else: st.error("Stock insuficiente")
                else:
                    if st.button("Confirmar Entrada"):
                        new_st = item_actual['Cantidad'] + cant_mov
                        supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                        try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": item_actual['codigo'], "descripcion": item_actual['Descripcion'], "tipo_movimiento": "Re-stock", "cantidad": cant_mov, "responsable": "Almacén"}).execute()
                        except: pass
                        st.success("✅ Entrada registrada"); time.sleep(1); st.rerun()
            with c_info: st.metric("Stock", item_actual['Cantidad'])
    with tab_exist:
        if not df_ins.empty:
            try:
                excel_data = convertir_df_a_excel(df_ins[["codigo", "Descripcion", "Cantidad", "Unidad"]])
                st.download_button("📥 Descargar Existencias", excel_data, "Existencias.xlsx")
            except: pass
            st.dataframe(df_ins[["codigo", "Descripcion", "Cantidad", "Unidad"]], use_container_width=True)
    with tab_hist:
        try:
            h = pd.DataFrame(supabase.table("Historial_Insumos").select("*").order("id", desc=True).limit(100).execute().data)
            st.dataframe(h, use_container_width=True)
        except: pass

# ==================================================
# 🔧 OPCIÓN 2: HERRAMIENTAS (INTACTO)
# ==================================================
elif "Herramientas" in opcion_almacen:
    try:
        df_her = pd.DataFrame(supabase.table("Herramientas").select("*").order("id").execute().data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: df_her = pd.DataFrame(); lista_personal = []

    if df_her.empty: df_her = pd.DataFrame(columns=["id", "codigo", "Herramienta", "Responsable", "Estado"])
    if "Responsable" not in df_her.columns: df_her["Responsable"] = "Bodega"
    df_her["Responsable"].fillna("Bodega", inplace=True)

    tab1, tab2, tab3 = st.tabs(["Movimientos", "Inventario", "Historial"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.info("Prestar")
            bodega = df_her[df_her["Responsable"]=="Bodega"]
            if not bodega.empty:
                sel = st.selectbox("Herramienta", bodega["Herramienta"].tolist())
                resp = st.selectbox("A quien", lista_personal)
                if st.button("Prestar"):
                    id_h = bodega[bodega["Herramienta"]==sel].iloc[0]["id"]
                    supabase.table("Herramientas").update({"Responsable": resp}).eq("id", int(id_h)).execute()
                    try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'), "Herramienta": sel, "Movimiento": "Préstamo", "Responsable": resp}).execute()
                    except: pass
                    st.success("Prestado"); time.sleep(1); st.rerun()
        with c2:
            st.warning("Devolver")
            prestadas = df_her[df_her["Responsable"]!="Bodega"]
            if not prestadas.empty:
                sel_d = st.selectbox("Devolver", prestadas["Herramienta"].tolist())
                if st.button("Devolver"):
                    id_h = prestadas[prestadas["Herramienta"]==sel_d].iloc[0]["id"]
                    supabase.table("Herramientas").update({"Responsable": "Bodega"}).eq("id", int(id_h)).execute()
                    try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'), "Herramienta": sel_d, "Movimiento": "Devolución", "Responsable": "Bodega"}).execute()
                    except: pass
                    st.success("Devuelto"); time.sleep(1); st.rerun()
    with tab2: st.dataframe(df_her, use_container_width=True)
    with tab3:
        try:
            h_her = pd.DataFrame(supabase.table("Historial_Herramientas").select("*").order("id", desc=True).limit(100).execute().data)
            st.dataframe(h_her, use_container_width=True)
        except: pass

# ==================================================
# 📑 OPCIÓN 3: RECIBOS DE ENTREGA OC (CLIENTES)
# ==================================================
elif "Recibos" in opcion_almacen:
    st.markdown("### 📑 Recibos de Entrega (Salidas a Clientes)")
    try:
        res_cli = supabase.table("Clientes").select("*").execute(); df_clientes = pd.DataFrame(res_cli.data)
        lista_nombres_cli = df_clientes['nombre'].tolist() if not df_clientes.empty else []
        res_prov = supabase.table("Proveedores").select("*").execute(); df_proveedores = pd.DataFrame(res_prov.data)
        col_p = 'empresa' if 'empresa' in df_proveedores.columns else 'nombre'
        lista_nombres_prov = df_proveedores[col_p].tolist() if not df_proveedores.empty else []
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: lista_nombres_cli = []; lista_nombres_prov = []; lista_personal = []; df_clientes = pd.DataFrame(); df_proveedores = pd.DataFrame()

    tab_nuevo, tab_historial = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    with tab_nuevo:
        with st.container(border=True):
            st.subheader("Datos de la Entrega")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_input = c1.text_input("Orden de Compra (O.C.)", placeholder="Ej. 2183")
            fecha_input = c2.date_input("Fecha", value=datetime.now().date())
            prov_input = c3.selectbox("Proveedor (Origen):", lista_nombres_prov, index=None, placeholder="Hemore...")
            cliente_input = st.selectbox("Cliente (Destino):", lista_nombres_cli, index=None)
            
            st.divider()
            if "data_recibo" not in st.session_state: st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            edited_df = st.data_editor(st.session_state["data_recibo"], num_rows="dynamic", use_container_width=True, column_config={"Cantidad": st.column_config.NumberColumn(min_value=0)})
            observaciones = st.text_area("Observaciones:")
            col_firmas, col_accion = st.columns([1, 1])
            usuario_input = col_firmas.selectbox("Registrado por:", lista_personal)
            
            if col_accion.button("💾 Guardar y PDF", type="primary", use_container_width=True):
                if oc_input and cliente_input and prov_input and not edited_df.empty:
                    items = edited_df[edited_df["Código"] != ""]
                    if not items.empty:
                        for i, row in items.iterrows():
                            supabase.table("Recibos_OC").insert({"fecha": fecha_input.isoformat(), "oc": oc_input, "cliente": cliente_input, "proveedor": prov_input, "codigo": row["Código"], "descripcion": row["Descripción"], "color": row["Color"], "cantidad": row["Cantidad"], "usuario": usuario_input, "observaciones": observaciones}).execute()
                        
                        cli_data = df_clientes[df_clientes['nombre'] == cliente_input].iloc[0]
                        col_p_name = 'empresa' if 'empresa' in df_proveedores.columns else 'nombre'
                        prov_data = df_proveedores[df_proveedores[col_p_name] == prov_input].iloc[0]
                        try: last_id = supabase.table("Recibos_OC").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        datos_pdf = {"oc": oc_input, "fecha": fecha_input.strftime("%d/%m/%Y"), "observaciones": observaciones, "prov_nombre": prov_input, "prov_dir": prov_data.get('domicilio', ''), "prov_col": prov_data.get('colonia', ''), "prov_cp": prov_data.get('codigo_postal', ''), "prov_rfc": prov_data.get('rfc', ''), "cli_nombre": cliente_input, "cli_dir": cli_data.get('direccion', ''), "cli_col": cli_data.get('colonia', ''), "cli_cp": cli_data.get('codigo_postal', ''), "cli_rfc": cli_data.get('rfc', '')}
                        pdf_bytes = generar_pdf_entrega(datos_pdf, items, last_id)
                        st.success("Guardado."); st.download_button("🖨️ PDF", pdf_bytes, f"Recibo_{oc_input}.pdf", "application/pdf")
                    else: st.warning("Tabla vacía.")
                else: st.warning("Faltan datos.")

    with tab_historial:
        try:
            h = pd.DataFrame(supabase.table("Recibos_OC").select("*").order("id", desc=True).limit(200).execute().data)
            if not h.empty:
                filtro = st.text_input("🔍 Buscar:", key="search_rec")
                if filtro: h = h[h.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
                h = h.sort_values(by=["oc", "id"], ascending=[False, False])
                st.dataframe(h[["oc", "fecha", "cliente", "proveedor", "codigo", "descripcion", "cantidad", "usuario"]], use_container_width=True, hide_index=True)
            else: st.info("Sin registros.")
        except: pass

# ==================================================
# 📥 OPCIÓN 4: ENTRADA DE MATERIAL (NUEVO MODULO)
# ==================================================
elif "Entrada" in opcion_almacen:
    st.markdown("### 📥 Registro de Entrada de Material (Proveedores)")
    
    # Cargar Maestros
    try:
        res_prov = supabase.table("Proveedores").select("*").execute(); df_provs = pd.DataFrame(res_prov.data)
        col_p = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
        lista_provs = df_provs[col_p].tolist() if not df_provs.empty else []
        df_pers = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_pers = df_pers['nombre'].tolist() if not df_pers.empty else []
    except: lista_provs = []; lista_pers = []; df_provs = pd.DataFrame()

    tab_ent_new, tab_ent_hist = st.tabs(["➕ Nueva Entrada", "📜 Historial Entradas"])

    with tab_ent_new:
        with st.container(border=True):
            st.subheader("Datos de la Entrada")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_in = c1.text_input("Orden de Compra / Remisión", placeholder="Folio del Proveedor")
            fecha_in = c2.date_input("Fecha de Llegada", value=datetime.now().date())
            prov_in = c3.selectbox("Proveedor (Origen):", lista_provs, index=None)
            
            st.divider()
            st.markdown("**📦 Material Recibido:**")
            
            if "data_entrada" not in st.session_state: st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            edited_df_in = st.data_editor(st.session_state["data_entrada"], num_rows="dynamic", use_container_width=True, column_config={"Cantidad": st.column_config.NumberColumn(min_value=0)})
            
            obs_in = st.text_area("Observaciones de llegada:", key="obs_in")
            col_f, col_a = st.columns([1, 1])
            user_in = col_f.selectbox("Recibido por (Hemore):", lista_pers, key="user_in")
            
            if col_a.button("💾 Registrar Entrada y PDF", type="primary", use_container_width=True):
                if oc_in and prov_in and not edited_df_in.empty:
                    items_in = edited_df_in[edited_df_in["Código"] != ""]
                    if not items_in.empty:
                        # Guardar
                        for i, row in items_in.iterrows():
                            supabase.table("Entradas_Material").insert({"fecha": fecha_in.isoformat(), "oc": oc_in, "proveedor": prov_in, "codigo": row["Código"], "descripcion": row["Descripción"], "color": row["Color"], "cantidad": row["Cantidad"], "usuario": user_in, "observaciones": obs_in}).execute()
                        
                        # Datos PDF
                        col_p_name = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
                        prov_data = df_provs[df_provs[col_p_name] == prov_in].iloc[0]
                        try: last_id = supabase.table("Entradas_Material").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        # Armar dict. Notar que aqui Proveedor es Origen. Cliente es HEMORE (fijo en funcion)
                        datos_pdf = {
                            "fecha": fecha_in.strftime("%d/%m/%Y"), 
                            "oc": oc_in, 
                            "observaciones": obs_in,
                            "prov_nombre": prov_in,
                            "prov_dir": prov_data.get('domicilio', ''),
                            "prov_col": prov_data.get('colonia', ''),
                            "prov_cp": prov_data.get('codigo_postal', ''),
                            "prov_rfc": prov_data.get('rfc', '')
                        }
                        
                        pdf_bytes = generar_pdf_entrada(datos_pdf, items_in, last_id)
                        st.success("✅ Entrada Registrada."); st.download_button("🖨️ Constancia PDF", pdf_bytes, f"Entrada_{oc_in}.pdf", "application/pdf")
                    else: st.warning("Tabla vacía.")
                else: st.warning("Faltan datos.")

    with tab_ent_hist:
        try:
            h_in = pd.DataFrame(supabase.table("Entradas_Material").select("*").order("id", desc=True).limit(200).execute().data)
            if not h_in.empty:
                filtro_in = st.text_input("🔍 Buscar Entrada:", key="search_ent")
                if filtro_in: h_in = h_in[h_in.astype(str).apply(lambda x: x.str.contains(filtro_in, case=False)).any(axis=1)]
                h_in = h_in.sort_values(by=["oc", "id"], ascending=[False, False])
                st.dataframe(h_in[["oc", "fecha", "proveedor", "codigo", "descripcion", "cantidad", "usuario"]], use_container_width=True, hide_index=True)
            else: st.info("Sin registros de entradas.")
        except: pass
