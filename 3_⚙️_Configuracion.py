import streamlit as st
import pandas as pd
import utils # Tu archivo de conexión
import time

# Configuración de página
st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")

def app_personal():
    st.markdown("### 👥 Gestión de Personal (Datos Maestros)")
    st.info("Administra aquí a los 50 colaboradores. Desmarca la casilla 'Activo' para dar de baja sin borrar historial.")

    # --- 1. CARGAR DATOS ---
    try:
        # Traemos todos los datos de la tabla Personal
        response = utils.supabase.table("Personal").select("*").order("nombre").execute()
        df_personal = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    # Si la tabla está vacía, creamos estructura vacía para evitar error visual
    if df_personal.empty:
        df_personal = pd.DataFrame(columns=["id", "nombre", "puesto", "activo"])

    # --- PESTAÑAS ---
    tab_alta, tab_edicion = st.tabs(["➕ Alta Nueva", "✏️ Editar / Bajas"])

    # --- TAB 1: ALTA NUEVA ---
    with tab_alta:
        st.write("Registra un nuevo empleado.")
        with st.form("form_alta_personal", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nuevo_nombre = col1.text_input("Nombre Completo (Ej. Juan Perez)")
            nuevo_puesto = col2.selectbox("Puesto", ["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"])
            
            submitted = st.form_submit_button("Guardar Nuevo Empleado")
            
            if submitted:
                if nuevo_nombre:
                    # Validar si ya existe
                    # Convertimos a string y minúsculas para comparar
                    nombres_existentes = df_personal["nombre"].astype(str).str.lower().values
                    if nuevo_nombre.lower() in nombres_existentes:
                        st.error("⚠️ Ese nombre ya existe.")
                    else:
                        datos = {"nombre": nuevo_nombre, "puesto": nuevo_puesto, "activo": True}
                        utils.supabase.table("Personal").insert(datos).execute()
                        st.success(f"✅ {nuevo_nombre} registrado correctamente.")
                        st.cache_data.clear() # Limpiar memoria para ver cambios
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("El nombre es obligatorio.")

    # --- TAB 2: EDICIÓN TIPO EXCEL ---
    with tab_edicion:
        st.write("Modifica los datos en la tabla. Desmarca 'Activo' para dar de baja.")
        
        # Editor de datos interactivo
        edited_df = st.data_editor(
            df_personal,
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "nombre": st.column_config.TextColumn("Nombre", max_chars=50),
                "puesto": st.column_config.SelectboxColumn(
                    "Puesto",
                    options=["Operador", "Supervisor", "Almacén", "Mantenimiento", "Administrativo"],
                    required=True
                ),
                "activo": st.column_config.CheckboxColumn(
                    "¿Activo?",
                    help="Si lo desmarcas, el empleado ya no podrá recibir herramientas."
                ),
                "created_at": st.column_config.Column(disabled=True, hidden=True) # Ocultamos fecha
            },
            hide_index=True,
            use_container_width=True,
            key="editor_personal"
        )

        # Botón Guardar
        if st.button("💾 Guardar Cambios"):
            progress_text = "Actualizando base de datos..."
            barra = st.progress(0, text=progress_text)
            
            # Recorremos la tabla editada para actualizar fila por fila
            total = len(edited_df)
            for index, row in edited_df.iterrows():
                try:
                    utils.supabase.table("Personal").update({
                        "nombre": row["nombre"],
                        "puesto": row["puesto"],
                        "activo": bool(row["activo"])
                    }).eq("id", row["id"]).execute()
                except Exception as e:
                    st.error(f"Error al actualizar ID {row['id']}: {e}")
                
                barra.progress((index + 1) / total)
            
            barra.empty()
            st.success("✅ Datos actualizados correctamente.")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# Ejecutar la función principal
if __name__ == "__main__":
    app_personal()