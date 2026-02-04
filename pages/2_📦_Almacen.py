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
        
        # El título se define en cada función generadora para flexibilidad
        self.ln(1)

    def footer(self):
        self.set_y(-40)
        self.set_font('Arial', '', 8)
        # Firmas
        self.cell(90, 0, '_______________________________', 0, 0, 'C')
        self.cell(10, 0, '', 0, 0)
        self.cell(90, 0, '_______________________________', 0, 1, 'C')
        self.ln(4)
        self.cell(90, 5, 'Entrega / Autoriza', 0, 0, 'C')
        self.cell(10, 5, '', 0, 0)
        self.cell(90, 5, 'Recibe / Caja', 0, 1, 'C')
        
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- GENERADORES DE PDF ---

def generar_pdf_entrega(datos_cabecera, df_productos, folio):
    # (Código existente para Entregas de Material)
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Recibo de Entrega', 0, 1, 'C')
    
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    _bloque_cajas_prov_cli(pdf, "Proveedor (Origen)", datos_cabecera['prov_texto'], "Cliente (Destino)", datos_cabecera['cli_texto'])
    _dibujar_tabla_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_entrada(datos_cabecera, df_productos, folio):
    # (Código existente para Entradas de Material)
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Constancia de Entrada', 0, 1, 'C')
    
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    _bloque_cajas_prov_cli(pdf, "Proveedor (Origen)", datos_cabecera['prov_texto'], "Receptor (Destino)", datos_cabecera['hemore_texto'])
    _dibujar_tabla_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_dinero(datos_cabecera, df_conceptos, folio):
    # (NUEVO: Para Recibos de Dinero)
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    pdf.set_xy(0, 10); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Recibo de Dinero', 0, 1, 'C')
    
    _bloque_folio_fecha(pdf, folio, datos_cabecera['fecha'])
    
    # Caja grande de información
    pdf.set_y(45)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "  Información del Pago", 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 10)
    # Recibimos de
    pdf.cell(40, 8, "Recibimos de:", 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, datos_cabecera['cliente'], 0, 1)
    
    # La cantidad de
    pdf.set_font('Arial', '', 10)
    pdf.cell(40, 8, "La cantidad de:", 0, 0)
    pdf.set_font('Arial', 'B', 12)
    # Calcular total para mostrarlo grande
    total = df_conceptos["Monto"].sum()
    pdf.cell(0, 8, f"$ {total:,.2f} MXN", 0, 1)
    
    # Método de Pago
    pdf.set_font('Arial', '', 10)
    pdf.cell(40, 8, "Método de Pago:", 0, 0)
    pdf.cell(0, 8, datos_cabecera['metodo'], 0, 1)
    pdf.ln(5)
    
    # Tabla de Conceptos (Diferente a la de productos)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(140, 8, "Concepto / Descripción", 1, 0, 'C', True)
    pdf.cell(50, 8, "Importe", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 9)
    for index, row in df_conceptos.iterrows():
        pdf.cell(140, 8, str(row['Concepto']), 1, 0, 'L')
        pdf.cell(50, 8, f"$ {row['Monto']:,.2f}", 1, 1, 'R')
        
    # Total al final de la tabla
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(140, 8, "TOTAL RECIBIDO", 1, 0, 'R')
    pdf.cell(50, 8, f"$ {total:,.2f}", 1, 1, 'R')

    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

# --- HELPERS PDF (Para no repetir código) ---
def _bloque_folio_fecha(pdf, folio, fecha):
    pdf.set_font('Arial', 'B', 10)
    pdf.set_xy(140, 25); pdf.cell(25, 6, "Folio:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, str(folio), 0, 1, 'L')
    pdf.set_xy(140, 31); pdf.set_font('Arial', 'B', 10); pdf.cell(25, 6, "Fecha:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, fecha, 0, 1, 'L')

def _bloque_cajas_prov_cli(pdf, titulo1, texto1, titulo2, texto2):
    pdf.set_y(45); y_start = pdf.get_y()
    pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, f" {titulo1}", 1, 0, 'L', True); pdf.cell(95, 6, f" {titulo2}", 1, 1, 'L', True)
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 25, "", 1, 0); pdf.cell(95, 25, "", 1, 0)
    pdf.set_xy(12, y_start + 8); pdf.multi_cell(90, 4, texto1)
    pdf.set_xy(107, y_start + 8); pdf.multi_cell(90, 4, texto2)
    pdf.set_xy(10, y_start + 35)

def _dibujar_tabla_productos(pdf, oc, df_productos):
    pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 7, "O.C.", 1, 0, 'C', True); pdf.cell(30, 7, "Codigo", 1, 0, 'C', True)
    pdf.cell(95, 7, "Descripcion", 1, 0, 'C', True); pdf.cell(20, 7, "Color", 1, 0, 'C', True); pdf.cell(20, 7, "Cant", 1, 1, 'C', True)
    pdf.set_font('Arial', '', 8)
    for index, row in df_productos.iterrows():
        pdf.cell(25, 7, str(oc), 1, 0, 'C'); pdf.cell(30, 7, str(row['Código']), 1, 0, 'C')
        pdf.cell(95, 7, str(row['Descripción'])[:55], 1, 0, 'L'); pdf.cell(20, 7, str(row['Color']), 1, 0, 'C'); pdf.cell(20, 7, str(row['Cantidad']), 1, 1, 'C')

def _bloque_observaciones(pdf, texto):
    pdf.ln(8); pdf.set_font('Arial', 'B', 9); pdf.write(5, "Observaciones: "); pdf.set_font('Arial', '', 9)
    pdf.write(5, texto if texto else "_"*110)

# --- FUNCIONES DATOS ---
def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer: df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

def aplicar_filtro_fechas(df, columna_fecha, filtro_seleccionado):
    if df.empty: return df
    df[columna_fecha] = pd.to_datetime(df[columna_fecha])
    hoy = pd.Timestamp.now().normalize()
    if filtro_seleccionado == "Hoy": df = df[df[columna_fecha].dt.date == hoy.date()]
    elif filtro_seleccionado == "Ayer": 
        ayer = hoy - timedelta(days=1); df = df[df[columna_fecha].dt.date == ayer.date()]
    return df

# ==========================================
# MENÚ LATERAL
# ==========================================
st.sidebar.title("🏭 Almacén Central")
opcion_almacen = st.sidebar.radio(
    "Selecciona Operación:",
    ["Insumos (Consumibles)", "Herramientas (Activos)", "Recibos de Entrega OC", "Entrada de Material", "Recibos de Dinero"]
)

st.title(f"Control de {opcion_almacen.split(' (')[0]}")

# ==================================================
# 🧱 OPCIÓN 1: INSUMOS
# ==================================================
if "Insumos" in opcion_almacen:
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: df_ins = pd.DataFrame(); lista_personal = []

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial"])
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
# 🔧 OPCIÓN 2: HERRAMIENTAS
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
                        
                        prov_text = f"{prov_input}\n{prov_data.get('domicilio', '')}\nCol. {prov_data.get('colonia', '')}, CP: {prov_data.get('codigo_postal', '')}\nRFC: {prov_data.get('rfc', '')}"
                        cli_text = f"{cliente_input}\n{cli_data.get('direccion', '')}\nCol. {cli_data.get('colonia', '')}, CP: {cli_data.get('codigo_postal', '')}\nRFC: {cli_data.get('rfc', '')}"
                        
                        datos_pdf = {"oc": oc_input, "fecha": fecha_input.strftime("%d/%m/%Y"), "observaciones": observaciones, "prov_texto": prov_text, "cli_texto": cli_text}
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
# 📥 OPCIÓN 4: ENTRADA DE MATERIAL
# ==================================================
elif "Entrada" in opcion_almacen:
    st.markdown("### 📥 Registro de Entrada de Material (Proveedores)")
    try:
        res_prov = supabase.table("Proveedores").select("*").execute(); df_provs = pd.DataFrame(res_prov.data)
        col_p = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
        lista_provs = df_provs[col_p].tolist() if not df_provs.empty else []
        df_pers = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_pers = df_pers['nombre'].tolist() if not df_pers.empty else []
    except: lista_provs = []; lista_pers = []; df_provs = pd.DataFrame()

    tab_ent_new, tab_ent_hist = st.tabs(["➕ Nueva Entrada", "📜 Historial"])
    with tab_ent_new:
        with st.container(border=True):
            st.subheader("Datos de la Entrada")
            c1, c2, c3 = st.columns([1, 1, 1])
            oc_in = c1.text_input("Orden de Compra / Remisión", placeholder="Folio del Proveedor")
            fecha_in = c2.date_input("Fecha de Llegada", value=datetime.now().date())
            prov_in = c3.selectbox("Proveedor (Origen):", lista_provs, index=None)
            
            st.divider()
            if "data_entrada" not in st.session_state: st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
            edited_df_in = st.data_editor(st.session_state["data_entrada"], num_rows="dynamic", use_container_width=True, column_config={"Cantidad": st.column_config.NumberColumn(min_value=0)})
            obs_in = st.text_area("Observaciones de llegada:", key="obs_in")
            col_f, col_a = st.columns([1, 1])
            user_in = col_f.selectbox("Recibido por (Hemore):", lista_pers, key="user_in")
            
            if col_a.button("💾 Registrar Entrada y PDF", type="primary", use_container_width=True):
                if oc_in and prov_in and not edited_df_in.empty:
                    items_in = edited_df_in[edited_df_in["Código"] != ""]
                    if not items_in.empty:
                        for i, row in items_in.iterrows():
                            supabase.table("Entradas_Material").insert({"fecha": fecha_in.isoformat(), "oc": oc_in, "proveedor": prov_in, "codigo": row["Código"], "descripcion": row["Descripción"], "color": row["Color"], "cantidad": row["Cantidad"], "usuario": user_in, "observaciones": obs_in}).execute()
                        
                        col_p_name = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
                        prov_data = df_provs[df_provs[col_p_name] == prov_in].iloc[0]
                        try: last_id = supabase.table("Entradas_Material").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        prov_text = f"{prov_in}\n{prov_data.get('domicilio', '')}\nCol. {prov_data.get('colonia', '')}, CP: {prov_data.get('codigo_postal', '')}\nRFC: {prov_data.get('rfc', '')}"
                        hemore_text = "HEMORE INDUSTRIAS\nCalle Falsa 123\nPuebla, Pue.\nRFC: HEM000000XXX\nAlmacén Central"
                        datos_pdf = {"fecha": fecha_in.strftime("%d/%m/%Y"), "oc": oc_in, "observaciones": obs_in, "prov_texto": prov_text, "hemore_texto": hemore_text}
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

# ==================================================
# 💰 OPCIÓN 5: RECIBOS DE DINERO (NUEVO)
# ==================================================
elif "Dinero" in opcion_almacen:
    st.markdown("### 💰 Recibos de Dinero (Caja/Pagos)")
    
    try:
        res_cli = supabase.table("Clientes").select("nombre").execute(); df_c = pd.DataFrame(res_cli.data)
        lista_clientes = df_c['nombre'].tolist() if not df_c.empty else []
        df_p = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_p = df_p['nombre'].tolist() if not df_p.empty else []
    except: lista_clientes = []; lista_p = []

    tab_money_new, tab_money_hist = st.tabs(["➕ Nuevo Recibo de Pago", "📜 Historial de Pagos"])

    with tab_money_new:
        with st.container(border=True):
            st.subheader("Detalles del Pago")
            c1, c2 = st.columns(2)
            fecha_pago = c1.date_input("Fecha de Recepción", value=datetime.now().date())
            cliente_pago = c2.selectbox("Recibimos de (Cliente):", lista_clientes, index=None)
            
            c3, c4 = st.columns(2)
            metodo = c3.selectbox("Método de Pago", ["Transferencia", "Efectivo", "Cheque", "Depósito"], index=0)
            usuario_pago = c4.selectbox("Recibe (Hemore):", lista_p)
            
            st.divider()
            st.markdown("**Desglose de Conceptos:**")
            
            if "data_money" not in st.session_state:
                st.session_state["data_money"] = pd.DataFrame([{"Concepto": "", "Monto": 0.0}], columns=["Concepto", "Monto"])
                
            edited_money = st.data_editor(
                st.session_state["data_money"],
                num_rows="dynamic",
                use_container_width=True,
                column_config={"Monto": st.column_config.NumberColumn(format="$ %.2f", min_value=0.0)}
            )
            
            # Calcular Total Dinámico
            total_money = edited_money["Monto"].sum()
            st.markdown(f"#### Total a Recibir: :green[$ {total_money:,.2f}]")
            
            obs_money = st.text_area("Observaciones:", key="obs_money")
            
            if st.button("💾 Generar Recibo de Dinero", type="primary", use_container_width=True):
                if cliente_pago and total_money > 0:
                    items_m = edited_money[edited_money["Concepto"] != ""]
                    if not items_m.empty:
                        # Guardar
                        for i, row in items_m.iterrows():
                            supabase.table("Recibos_Dinero").insert({
                                "fecha": fecha_pago.isoformat(),
                                "cliente": cliente_pago,
                                "concepto": row["Concepto"],
                                "monto": row["Monto"],
                                "metodo_pago": metodo,
                                "usuario": usuario_pago,
                                "observaciones": obs_money
                            }).execute()
                        
                        # PDF
                        try: last_id = supabase.table("Recibos_Dinero").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        datos_pdf = {"fecha": fecha_pago.strftime("%d/%m/%Y"), "cliente": cliente_pago, "metodo": metodo, "observaciones": obs_money}
                        pdf_bytes = generar_pdf_dinero(datos_pdf, items_m, last_id)
                        
                        st.success("✅ Recibo Generado."); st.download_button("🖨️ Descargar PDF", pdf_bytes, f"Recibo_Dinero_{cliente_pago}.pdf", "application/pdf")
                    else: st.warning("Agrega al menos un concepto.")
                else: st.warning("Faltan datos o el monto es 0.")

    with tab_money_hist:
        try:
            h_mon = pd.DataFrame(supabase.table("Recibos_Dinero").select("*").order("id", desc=True).limit(200).execute().data)
            if not h_mon.empty:
                filtro_m = st.text_input("🔍 Buscar Recibo:", key="search_mon")
                if filtro_m: h_mon = h_mon[h_mon.astype(str).apply(lambda x: x.str.contains(filtro_m, case=False)).any(axis=1)]
                
                # Agrupación visual (Opcional, o tabla plana)
                st.dataframe(h_mon[["id", "fecha", "cliente", "concepto", "monto", "metodo_pago", "usuario"]], use_container_width=True, hide_index=True)
                
                # Totalizador simple del filtro
                total_hist = h_mon["monto"].sum()
                st.info(f"💰 Suma total en esta vista: $ {total_hist:,.2f}")
            else: st.info("No hay recibos de dinero.")
        except: pass
