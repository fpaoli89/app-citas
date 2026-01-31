import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN ---
NOMBRE_NEGOCIO = "Lo del Fer" 
COLOR_PRIMARIO = "#E91E63"
PASSWORD_CORRECTA = "admin2024"
# PEGA AQUÍ LA URL DE TU GOOGLE SHEET
URL_SHEET = "https://docs.google.com/spreadsheets/d/1OBbIxv645l674Fkw57LdBa5DIEHBLXnf47w1RK7fs8k/edit?gid=0#gid=0" 

st.set_page_config(page_title=NOMBRE_NEGOCIO, page_icon="✨")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
   return conn.read(ttl=0)

def generar_link_whatsapp(fila):
    tel = "".join(filter(str.isdigit, str(fila['telefono'])))
    mensaje = f"👋 Hola *{fila['cliente']}*, recordatorio de cita en *{NOMBRE_NEGOCIO}* para el día {fila['fecha']} a las {fila['hora']}."
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

# --- LOGIN (Igual que antes) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acceso")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if clave == PASSWORD_CORRECTA:
            st.session_state['autenticado'] = True
            st.rerun()
else:
    st.title(f"✨ {NOMBRE_NEGOCIO}")
    tab1, tab2 = st.tabs(["📝 Registrar", "📅 Agenda"])

    with tab1:
        with st.form("registro", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            tel = st.text_input("WhatsApp")
            fecha = st.date_input("Fecha", min_value=datetime.today())
            hora = st.time_input("Hora")
            servicio = st.selectbox("Servicio", ["Corte", "Manicura", "Masajes", "Otro"])
            
            if st.form_submit_button("Guardar Cita"):
                if nombre and tel:
                    # Leer datos actuales
                    df_actual = leer_datos()
                    # Crear nueva fila
                    nueva_cita = pd.DataFrame([{
                        "cliente": nombre, "telefono": tel, 
                        "fecha": str(fecha), "hora": str(hora), "servicio": servicio
                    }])
                    # Combinar y guardar
                    df_final = pd.concat([df_actual, nueva_cita], ignore_index=True)
                    conn.update(data=df_final)
                    st.success("✅ ¡Guardado en Google Sheets!")
                else:
                    st.error("Faltan datos")

    with tab2:
        df = leer_datos()
        if not df.empty and df.iloc[0,0] is not None:
            df['WhatsApp'] = df.apply(generar_link_whatsapp, axis=1)
            st.data_editor(df, use_container_width=True)
        else:
            st.info("No hay citas.")




