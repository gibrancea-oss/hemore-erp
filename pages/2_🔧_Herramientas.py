import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Herramientas", layout="wide")
utils.validar_login()
supabase = utils.init_connection()

st.title("🔧 Control de Herramientas")

# Cargar datos
df_her = pd.DataFrame(supabase.table("Herramientas").select("*").order("ID").execute().data)
df_ops = pd.DataFrame(supabase.table("Operadores").select("Nombre_Operador").execute().data)
lista_ops = df_ops['Nombre_Operador'].tolist() if not df_ops.empty else []

tab1, tab2 = st.tabs(["Préstamos", "Listado Activos"])

with tab1:
    bodega = df_her[df_her['Responsable'] == 'Bodega']
    prestadas = df_her[df_her['Responsable'] != 'Bodega']
    
    c1, c2 = st.columns(2)
    
    with c1.form("prestar"):
        st.subheader("📤 Prestar")
        l_bodega = [f"{r['ID']} - {r['Herramienta']}" for i,r in bodega.iterrows()]
        sel_p = st.selectbox("Herramienta Disponible", l_bodega)
        resp = st.selectbox("Se entrega a:", lista_ops)
        
        if st.form_submit_button("Prestar"):
            if sel_p:
                id_h = int(sel_p.split(" - ")[0])
                nom_h = sel_p.split(" - ")[1]
                supabase.table("Herramientas").update({"Responsable": resp}).eq("ID", id_h).execute()
                supabase.table("Historial_Herramientas").insert({
                    "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Herramienta": nom_h,
                    "Movimiento": "Préstamo",
                    "Responsable": resp
                }).execute()
                st.success("Prestado")
                time.sleep(1)
                st.rerun()

    with c2.form("devolver"):
        st.subheader("📥 Devolver")
        l_prest = [f"{r['ID']} - {r['Herramienta']} ({r['Responsable']})" for i,r in prestadas.iterrows()]
        sel_d = st.selectbox("Herramienta Prestada", l_prest)
        estado = st.selectbox("Estado", ["BUENO", "MALO"])
        
        if st.form_submit_button("Devolver"):
            if sel_d:
                id_h = int(sel_d.split(" - ")[0])
                nom_h = sel_d.split(" - ")[1].split(" (")[0]
                supabase.table("Herramientas").update({"Responsable": "Bodega", "Estado": estado}).eq("ID", id_h).execute()
                supabase.table("Historial_Herramientas").insert({
                    "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Herramienta": nom_h,
                    "Movimiento": "Devolución",
                    "Responsable": "Bodega",
                    "Detalle": estado
                }).execute()
                st.success("Devuelto")
                time.sleep(1)
                st.rerun()

with tab2:
    st.dataframe(df_her, use_container_width=True)