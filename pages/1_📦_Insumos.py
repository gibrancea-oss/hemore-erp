import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sys
import os

# Truco para importar utils desde la carpeta superior
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Insumos", layout="wide")
utils.validar_login() # BLOQUEA SI NO HAY LOGIN
supabase = utils.init_connection()

st.title("📦 Gestión de Insumos")

# Cargar datos
df_insumos = pd.DataFrame(supabase.table("Insumos").select("*").order("ID").execute().data)
df_operadores = pd.DataFrame(supabase.table("Operadores").select("Nombre_Operador").execute().data)

tab1, tab2 = st.tabs(["Movimientos (Entrada/Salida)", "Inventario Completo"])

with tab1:
    col1, col2 = st.columns(2)
    lista_insumos = [f"{row['ID']} - {row['Insumo']} (Stock: {row['Cantidad']})" for i, row in df_insumos.iterrows()]
    lista_ops = df_operadores['Nombre_Operador'].tolist() if not df_operadores.empty else []

    with col1.form("salida"):
        st.subheader("➖ Registrar Salida")
        item = st.selectbox("Insumo", lista_insumos)
        cant = st.number_input("Cantidad", min_value=0.1)
        quien = st.selectbox("Solicitante", lista_ops)
        
        if st.form_submit_button("Confirmar Salida"):
            id_ins = int(item.split(" - ")[0])
            stock_actual = float(item.split("Stock: ")[1].replace(")",""))
            if stock_actual >= cant:
                supabase.table("Insumos").update({"Cantidad": stock_actual - cant}).eq("ID", id_ins).execute()
                supabase.table("Historial_Insumos").insert({
                    "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Insumo": item.split(" - ")[1],
                    "Movimiento": "Salida",
                    "Cantidad": cant,
                    "Entregado_A": quien
                }).execute()
                st.success("Salida Registrada")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Stock insuficiente")

    with col2.form("entrada"):
        st.subheader("➕ Registrar Entrada")
        item_e = st.selectbox("Insumo", lista_insumos, key="e_item")
        cant_e = st.number_input("Cantidad a sumar", min_value=0.1, key="e_cant")
        
        if st.form_submit_button("Confirmar Entrada"):
            id_ins = int(item_e.split(" - ")[0])
            stock_actual = float(item_e.split("Stock: ")[1].replace(")",""))
            
            supabase.table("Insumos").update({"Cantidad": stock_actual + cant_e}).eq("ID", id_ins).execute()
            supabase.table("Historial_Insumos").insert({
                "Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "Insumo": item_e.split(" - ")[1],
                "Movimiento": "Entrada",
                "Cantidad": cant_e,
                "Entregado_A": "Almacén"
            }).execute()
            st.success("Entrada Registrada")
            time.sleep(1)
            st.rerun()

with tab2:
    st.dataframe(df_insumos, use_container_width=True)