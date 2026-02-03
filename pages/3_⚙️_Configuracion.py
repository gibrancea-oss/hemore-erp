import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Configuración", layout="wide")
utils.validar_login()
supabase = utils.init_connection()

st.title("⚙️ Datos Maestros")

tab1, tab2 = st.tabs(["Personal", "Alta de Insumos"])

with tab1:
    st.subheader("Alta de Personal")
    nombre = st.text_input("Nombre Completo")
    tipo = st.selectbox("Puesto", ["Operador", "Supervisor"])
    if st.button("Guardar Personal"):
        supabase.table("Operadores").insert({"Nombre_Operador": nombre, "Tipo": tipo}).execute()
        st.success("Guardado")

with tab2:
    st.subheader("Nuevo Insumo")
    nom_ins = st.text_input("Nombre Insumo")
    desc = st.text_input("Descripción")
    if st.button("Crear Insumo"):
        supabase.table("Insumos").insert({"Insumo": nom_ins, "Descripcion": desc, "Cantidad": 0}).execute()
        st.success("Guardado")