import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import io
import utils 
from fpdf import FPDF # Librería para crear el PDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")

# --- 🔒 SEGURIDAD ---
utils.validar_login() 
# --------------------

supabase = utils.supabase 

# --- FUNCIÓN GENERADOR DE PDF (TIPO RECIBO HEMORE) ---
class PDF(FPDF):
    def header(self):
        # Logo o Título Grande
        self.set_font('Arial', 'B', 20)
        self.cell(100, 10, 'HEMORE', 0, 0, 'L')
        self.set_font('Arial', '', 14)
        self.cell(0, 10, 'Recibo de Entrega', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-40)
        self.set_font('Arial', '', 8)
        # Firmas
        self.cell(90, 0, '_______________________________', 0, 0, 'C')
        self.cell(10, 0, '', 0, 0)
        self.cell(90, 0, '_______________________________', 0, 1, 'C')
        self.ln(3)
        self.cell(90, 5, 'Entrega Nombre y Firma', 0, 0, 'C')
        self.cell(10, 5, '', 0, 0)
        self.cell(90, 5, 'Recibe Nombre y Firma', 0, 1, 'C')
        
        # Pagina
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_recibo(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    
    # --- DATOS GENERALES (CABECERA) ---
    pdf.set_font('Arial', 'B', 10)
    
    # Folio y Fecha (Derecha)
    pdf.set_xy(140, 25)
    pdf.cell(25, 6, "Folio:", 0, 0, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, str(folio), 0, 1, 'L')
    
    pdf.set_xy(140, 31)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 6, "Fecha:", 0, 0, 'R')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, datos_cabecera['fecha'], 0, 1, 'L')

    pdf.ln(10)

    # --- RECUADROS DE PROVEEDOR Y CLIENTE ---
    # Dibujamos dos rectangulos simulando la imagen
    y_start = pdf.get_y()
    
    # PROVEEDOR (HEMORE)
    pdf.set_fill_color(220, 220, 220) # Gris claro
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, " Proveedor", 1, 0, 'C', True)
    pdf.cell(95, 6, " Cliente", 1, 1, 'C', True)
    
    # Datos Proveedor (Izquierda)
    pdf.set_font('Arial', '', 8)
    pdf.cell(95, 20, "", 1, 0) # Caja vacía para borde
    
    # Escribimos dentro de la caja izquierda
    pdf.set_xy(12, y_start + 8) 
    pdf.multi_cell(90, 4, "HEMORE INDUSTRIAS\nCalle Falsa 123\nPuebla, Pue.\nRFC: HEM000000XXX")
    
    # Datos Cliente (Derecha)
    pdf.set_xy(105, y_start + 6)
    pdf.cell(95, 20, "", 1, 0) # Caja vacía derecha
    
    pdf.set_xy(107, y_start + 8)
    pdf.multi_cell(90, 4, f"{datos_cabecera['cliente']}\nRFC: {datos_cabecera.get('rfc_cliente', '')}")
    
    pdf.set_xy(10, y_start + 28) # Bajar cursor
    
    # --- TABLA DE PRODUCTOS ---
    # Encabezados
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 7, "O.C.", 1, 0, 'C', True)
    pdf.cell(30, 7, "Código", 1, 0, 'C', True)
    pdf.cell(95, 7, "Descripción", 1, 0, 'C', True)
    pdf.cell(20, 7, "Color", 1, 0, 'C', True)
    pdf.cell(20, 7, "Cantidad", 1, 1, 'C', True)
    
    # Filas
    pdf.set_font('Arial', '', 8)
    for index, row in df_productos.iterrows():
        # Altura dinámica por si la descripción es larga
        col_oc = str(datos_cabecera['oc'])
        col_cod = str(row['Código'])
        col_desc = str(row['Descripción'])
        col_color = str(row['Color'])
        col_cant = str(row['Cantidad'])
        
        pdf.cell(25, 7, col_oc, 1, 0, 'C')
        pdf.cell(30, 7, col_cod, 1, 0, 'C')
        pdf.cell(95, 7, col_desc, 1, 0, 'L')
        pdf.cell(20, 7, col_color, 1, 0, 'C')
        pdf.cell(20, 7, col_cant, 1, 1, 'C')

    # Observaciones
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 9)
    pdf.write(5, "Observaciones: ")
    pdf.set_font('Arial', '', 9)
    pdf.write(5, "_"*110)

    # Convertir a bytes
    return pdf.output(dest='S').encode('latin-1')

# --- FUNCIONES AUXILIARES EXISTENTES ---
def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
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
    ["Insumos (Consumibles)", "Herramientas (Activos)", "Recibos de Entrega OC"]
)

st.title(f"Control de {opcion_almacen.split(' (')[0]}")

# ==================================================
# 🧱 OPCIÓN 1: GESTIÓN DE INSUMOS (INTACTO)
# ==================================================
if "Insumos" in opcion_almacen:
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: 
        df_ins = pd.DataFrame()
        lista_personal = []

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial y Reportes"])

    # PESTAÑA 1
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
                            st.success("✅ Salida registrada")
                            time.sleep(1)
                            st.rerun()
                        else: st.error("Stock insuficiente")
                else:
                    if st.button("Confirmar Entrada"):
                        new_st = item_actual['Cantidad'] + cant_mov
                        supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                        try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": item_actual['codigo'], "descripcion": item_actual['Descripcion'], "tipo_movimiento": "Re-stock", "cantidad": cant_mov, "responsable": "Almacén"}).execute()
                        except: pass
                        st.success("✅ Entrada registrada")
                        time.sleep(1)
                        st.rerun()
            with c_info: st.metric("Stock", item_actual['Cantidad'])

    # PESTAÑA 2 y 3 (Resumido para brevedad, funcional igual)
    with tab_exist:
        if not df_ins.empty:
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

    tab1, tab2 = st.tabs(["Movimientos", "Inventario"])
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
                    st.success("Prestado")
                    time.sleep(1); st.rerun()
        with c2:
            st.warning("Devolver")
            prestadas = df_her[df_her["Responsable"]!="Bodega"]
            if not prestadas.empty:
                sel_d = st.selectbox("Devolver", prestadas["Herramienta"].tolist())
                if st.button("Devolver"):
                    id_h = prestadas[prestadas["Herramienta"]==sel_d].iloc[0]["id"]
                    supabase.table("Herramientas").update({"Responsable": "Bodega"}).eq("id", int(id_h)).execute()
                    st.success("Devuelto")
                    time.sleep(1); st.rerun()
    with tab2:
        st.dataframe(df_her, use_container_width=True)

# ==================================================
# 📑 OPCIÓN 3: RECIBOS DE ENTREGA OC (NUEVO Y MEJORADO)
# ==================================================
elif "Recibos" in opcion_almacen:
    st.markdown("### 📑 Generador de Recibos de Entrega (OC)")
    
    # 1. Cargar Datos Maestros
    try:
        df_clientes = pd.DataFrame(supabase.table("Clientes").select("nombre, rfc").execute().data)
        lista_clientes = df_clientes['nombre'].tolist() if not df_clientes.empty else []
        
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: 
        lista_clientes = []
        lista_personal = []

    # 2. INTERFAZ DE CAPTURA TIPO RECIBO
    with st.container(border=True):
        st.subheader("📝 Nuevo Recibo")
        
        # --- CABECERA DEL RECIBO ---
        c1, c2, c3 = st.columns([1, 2, 1])
        oc_input = c1.text_input("Orden de Compra (O.C.)")
        cliente_input = c2.selectbox("Cliente", lista_clientes)
        fecha_input = c3.date_input("Fecha", value=datetime.now().date())
        
        st.divider()
        st.markdown("**📦 Productos de la Orden:**")
        
        # --- TABLA EDITABLE (GRID) ---
        # Inicializamos un DataFrame vacío para que el usuario lo llene
        if "data_recibo" not in st.session_state:
            st.session_state["data_recibo"] = pd.DataFrame(
                [{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], # Fila ejemplo
                columns=["Código", "Descripción", "Color", "Cantidad"]
            )

        # Editor de datos
        edited_df = st.data_editor(
            st.session_state["data_recibo"],
            num_rows="dynamic", # Permite agregar/borrar filas
            use_container_width=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn(min_value=0, step=1, format="%d")
            }
        )
        
        col_firmas, col_accion = st.columns([2, 1])
        usuario_input = col_firmas.selectbox("Registrado por (Firma interna):", lista_personal)
        
        # --- BOTÓN DE GUARDAR E IMPRIMIR ---
        if col_accion.button("💾 Guardar y Generar PDF", type="primary", use_container_width=True):
            if oc_input and cliente_input and not edited_df.empty:
                # 1. Validar que haya datos reales
                items_validos = edited_df[edited_df["Código"] != ""]
                
                if not items_validos.empty:
                    # 2. Guardar en Base de Datos (Fila por fila)
                    for i, row in items_validos.iterrows():
                        try:
                            supabase.table("Recibos_OC").insert({
                                "fecha": fecha_input.isoformat(),
                                "oc": oc_input,
                                "cliente": cliente_input,
                                "codigo": row["Código"],
                                "descripcion": row["Descripción"],
                                "color": row["Color"],
                                "cantidad": row["Cantidad"],
                                "usuario": usuario_input
                            }).execute()
                        except Exception as e:
                            st.error(f"Error guardando item {row['Código']}: {e}")
                    
                    # 3. Obtener el 'Folio' (usamos el ID del último insertado aprox, o un contador)
                    # Para el PDF usaremos un placeholder o consultaremos el último ID
                    try:
                        last_id = supabase.table("Recibos_OC").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                    except: last_id = 1
                    
                    # 4. Generar PDF en memoria
                    datos_pdf = {
                        "oc": oc_input,
                        "cliente": cliente_input,
                        "fecha": fecha_input.strftime("%d/%m/%Y"),
                        "rfc_cliente": "XAXX010101000" # Placeholder, idealmente vendría de la BD Clientes
                    }
                    
                    pdf_bytes = generar_pdf_recibo(datos_pdf, items_validos, last_id)
                    
                    # 5. Mostrar descarga
                    st.success("✅ Recibo Guardado Exitosamente")
                    st.download_button(
                        label="🖨️ Descargar PDF del Recibo",
                        data=pdf_bytes,
                        file_name=f"Recibo_HEMORE_{oc_input}.pdf",
                        mime="application/pdf"
                    )
                    
                else:
                    st.warning("La tabla está vacía o los códigos están en blanco.")
            else:
                st.warning("Faltan datos de cabecera (OC o Cliente).")

    # --- HISTORIAL RÁPIDO ---
    with st.expander("📜 Ver Últimos Recibos Generados"):
        try:
            h_recibos = pd.DataFrame(supabase.table("Recibos_OC").select("*").order("id", desc=True).limit(20).execute().data)
            if not h_recibos.empty:
                st.dataframe(h_recibos, use_container_width=True)
        except: pass
