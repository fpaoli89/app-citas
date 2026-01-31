import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN DE MARCA ---
NOMBRE_NEGOCIO = "Lo del Fer" 
COLOR_PRIMARIO = "#E91E63"
PASSWORD_CORRECTA = "admin2024"  # <--- CAMBIA TU CONTRASEÑA AQUÍ

st.set_page_config(page_title=NOMBRE_NEGOCIO, page_icon="✨", layout="centered")

# --- ESTILOS ---
st.markdown(f"""
    <style>
    .stButton>button {{
        width: 100%;
        border-radius: 20px;
        background-color: {COLOR_PRIMARIO};
        color: white;
    }}
    .login-box {{
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect('database_citas.db', check_same_thread=False)

def inicializar_db():
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS citas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, telefono TEXT, fecha DATE, hora TEXT, servicio TEXT)''')
    conn.commit()
    conn.close()

def generar_link_whatsapp(fila):
    tel = "".join(filter(str.isdigit, str(fila['telefono'])))
    mensaje = f"👋 Hola *{fila['cliente']}*, recordatorio de cita en *{NOMBRE_NEGOCIO}* para el día {fila['fecha']} a las {fila['hora']}."
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

# --- LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    st.title(f"🔐 Acceso a {NOMBRE_NEGOCIO}")
    with st.container():
        clave = st.text_input("Introduce la contraseña para gestionar las citas", type="password")
        if st.button("Entrar"):
            if clave == PASSWORD_CORRECTA:
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

# --- CONTENIDO DE LA APP (Solo si está autenticado) ---
if not st.session_state['autenticado']:
    login()
else:
    # Botón para cerrar sesión en la barra lateral
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    inicializar_db()
    st.title(f"✨ {NOMBRE_NEGOCIO}")
    
    tab1, tab2 = st.tabs(["📝 Registrar Cita", "📅 Ver Agenda"])

    with tab1:
        st.subheader("Nueva Cita")
        with st.form("registro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre del Cliente")
            tel = col2.text_input("WhatsApp (con código de país)")
            fecha = col1.date_input("Fecha", min_value=datetime.today())
            hora = col2.time_input("Hora")
            servicio = st.selectbox("Servicio", ["Corte", "Manicura", "Masajes", "Otro"])
            
            if st.form_submit_button("Guardar Cita"):
                if nombre and tel:
                    conn = conectar_db()
                    conn.execute('INSERT INTO citas (cliente, telefono, fecha, hora, servicio) VALUES (?,?,?,?,?)',
                                 (nombre, tel, str(fecha), str(hora), servicio))
                    conn.commit()
                    st.success(f"✅ ¡Cita guardada para {nombre}!")
                else:
                    st.warning("⚠️ Nombre y teléfono son obligatorios.")

    with tab2:
        st.subheader("Agenda de Citas")
        df = pd.read_sql_query('SELECT * FROM citas ORDER BY fecha, hora', conectar_db())
        if not df.empty:
            df['WhatsApp'] = df.apply(generar_link_whatsapp, axis=1)
            st.data_editor(
                df[['cliente', 'servicio', 'fecha', 'hora', 'WhatsApp']], 
                column_config={
                    "WhatsApp": st.column_config.LinkColumn("Enviar", display_text="📲 Enviar Recordatorio")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No hay citas registradas.")
