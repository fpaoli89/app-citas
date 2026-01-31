import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN DE MARCA Y PÁGINA ---
# Personaliza estos valores para tu cliente
NOMBRE_NEGOCIO = "Lo del Fer" 
COLOR_PRIMARIO = "#E91E63" # Un rosado elegante, puedes cambiarlo

st.set_page_config(
    page_title=NOMBRE_NEGOCIO, 
    page_icon="✨", 
    layout="wide"
)

# Estilo personalizado para que se vea "Premium"
st.markdown(f"""
    <style>
    .main {{ background-color: #f8f9fa; }}
    .stButton>button {{
        width: 100%;
        border-radius: 20px;
        background-color: {COLOR_PRIMARIO};
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect('database_citas.db', check_same_thread=False)
    return conn

def inicializar_db():
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            telefono TEXT NOT NULL,
            fecha DATE NOT NULL,
            hora TEXT NOT NULL,
            servicio TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- FUNCIONES DE AYUDA ---
def generar_link_whatsapp(fila):
    # Limpiar el número
    tel = "".join(filter(str.isdigit, str(fila['telefono'])))
    # Mensaje con formato profesional para WhatsApp
    mensaje = (
        f"👋 Hola *{fila['cliente']}*,\n\n"
        f"Te recordamos tu cita en *{NOMBRE_NEGOCIO}*:\n"
        f"📅 *{fila['fecha']}*\n"
        f"⏰ *{fila['hora']}*\n\n"
        f"¡Te esperamos!"
    )
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

# --- INTERFAZ PRINCIPAL ---
inicializar_db()

st.title(f"✨ {NOMBRE_NEGOCIO}")
st.subheader("Gestión de Agenda y Clientes")

tab1, tab2, tab3 = st.tabs(["📝 Registrar Cita", "📅 Agenda del Día", "📊 Reportes"])

# PESTAÑA 1: REGISTRO
with tab1:
    with st.container():
        st.write("### Datos de la Cita")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo")
            fecha = st.date_input("Día de la Cita", min_value=datetime.today())
        with col2:
            tel = st.text_input("WhatsApp (Ej: 5491122334455)")
            hora = st.time_input("Hora")
        
        servicio = st.selectbox("Servicio", ["Corte de Cabello", "Manicura", "Masajes", "Consulta General", "Otro"])
        
        if st.button("Confirmar y Guardar"):
            if nombre and tel:
                conn = conectar_db()
                c = conn.cursor()
                c.execute('INSERT INTO citas (cliente, telefono, fecha, hora, servicio) VALUES (?,?,?,?,?)',
                          (nombre, tel, str(fecha), str(hora), servicio))
                conn.commit()
                conn.close()
                st.success(f"✅ Cita registrada para {nombre}")
                st.balloons()
            else:
                st.error("⚠️ Por favor completa los campos de nombre y teléfono.")

# PESTAÑA 2: AGENDA
with tab2:
    st.write("### Citas Programadas")
    conn = conectar_db()
    df = pd.read_sql_query('SELECT * FROM citas ORDER BY fecha ASC, hora ASC', conn)
    conn.close()

    if not df.empty:
        # Añadir link de WhatsApp
        df['Acción'] = df.apply(generar_link_whatsapp, axis=1)
        
        st.data_editor(
            df[['cliente', 'servicio', 'fecha', 'hora', 'Acción']],
            column_config={
                "Acción": st.column_config.LinkColumn("Enviar Recordatorio", display_text="📲 Enviar WA"),
                "fecha": "Día",
                "hora": "Horario"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No hay citas programadas aún.")

# PESTAÑA 3: REPORTES Y LIMPIEZA
with tab3:
    st.write("### Resumen de Negocio")
    if not df.empty:
        total_citas = len(df)
        st.metric("Total de Citas", total_citas)
        
        st.write("---")
        if st.button("🗑️ Limpiar Citas Pasadas"):
            # Aquí podrías programar borrar citas de fechas anteriores
            st.warning("Función de limpieza en desarrollo.")
    else:

        st.write("No hay datos para mostrar.")

