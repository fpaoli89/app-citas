import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN ---
NOMBRE_NEGOCIO = "Lo del Fer" 
COLOR_PRIMARIO = "#E91E63"
PASSWORD_CORRECTA = "admin2024"
# Asegúrate de que esta URL sea la de tu Excel
URL_SHEET = "https://docs.google.com/spreadsheets/d/TU_ID_AQUÍ/edit"

st.set_page_config(page_title=NOMBRE_NEGOCIO, page_icon="✂️", layout="centered")

# --- ESTILOS ---
st.markdown(f"""
    <style>
    .stButton>button {{
        width: 100%;
        border-radius: 20px;
        background-color: {COLOR_PRIMARIO};
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    try:
        # ttl=0 para datos en tiempo real
        df = conn.read(spreadsheet=URL_SHEET, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=["cliente", "telefono", "fecha", "hora", "servicio"])
        
        # Seleccionamos solo las 5 columnas de interés
        df = df.iloc[:, 0:5].dropna(how="all")
        
        # LIMPIEZA DE TELÉFONO: Convertir a string y quitar el ".0"
        df['telefono'] = df['telefono'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        return df
    except:
        return pd.DataFrame(columns=["cliente", "telefono", "fecha", "hora", "servicio"])

def generar_link_whatsapp(fila):
    # Limpiamos el teléfono de cualquier caracter no numérico para el link
    tel_limpio = "".join(filter(str.isdigit, str(fila['telefono'])))
    mensaje = f"👋 Hola *{fila['cliente']}*, recordatorio de cita en *{NOMBRE_NEGOCIO}* para el día {fila['fecha']} a las {fila['hora']}."
    return f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje)}"

# --- LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title(f"🔐 Acceso a {NOMBRE_NEGOCIO}")
    clave = st.text_input("Contraseña de administrador", type="password")
    if st.button("Entrar"):
        if clave == PASSWORD_CORRECTA:
            st.session_state['autenticado'] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")
else:
    # --- APP PRINCIPAL (AUTENTICADO) ---
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    st.title(f"✨ {NOMBRE_NEGOCIO}")
    tab1, tab2 = st.tabs(["📝 Registrar Cita", "📅 Ver Agenda"])

    with tab1:
        st.subheader("Nueva Cita")
        with st.form("registro", clear_on_submit=True):
            nombre = st.text_input("Nombre del Cliente")
            tel = st.text_input("WhatsApp (ej: 54911...)")
            col1, col2 = st.columns(2)
            fecha = col1.date_input("Fecha", min_value=datetime.today())
            hora = col2.time_input("Hora")
            servicio = st.selectbox("Servicio", ["Corte", "Barba", "Corte + Barba", "Color", "Otro"])
            
            if st.form_submit_button("Guardar Cita"):
                if nombre and tel:
                    # 1. Obtener datos actuales limpios
                    df_actual = leer_datos()
                    
                    # 2. Limpiar el teléfono ingresado (quitar .0 si se coló)
                    tel_final = str(tel).replace(".0", "")
                    
                    # 3. Crear nueva fila
                    nueva_cita = pd.DataFrame([{
                        "cliente": nombre, 
                        "telefono": tel_final, 
                        "fecha": str(fecha), 
                        "hora": str(hora), 
                        "servicio": servicio
                    }])
                    
                    # 4. Combinar y asegurar orden de columnas
                    df_final = pd.concat([df_actual, nueva_cita], ignore_index=True)
                    df_final = df_final[["cliente", "telefono", "fecha", "hora", "servicio"]]
                    
                    # 5. Forzar a que la columna teléfono sea texto para el Excel
                    df_final['telefono'] = df_final['telefono'].astype(str)
                    
                    # 6. Actualizar Google Sheets
                    conn.update(spreadsheet=URL_SHEET, data=df_final)
                    
                    st.success(f"✅ ¡Cita de {nombre} guardada!")
                    st.balloons()
                else:
                    st.warning("⚠️ Completa nombre y teléfono.")

    with tab2:
        st.subheader("Agenda de Turnos")
        df_agenda = leer_datos()
        
        # Eliminar filas vacías
        df_agenda = df_agenda[df_agenda['cliente'].notna()]

        if not df_agenda.empty:
            # Crear columna de WhatsApp con el link limpio
            df_agenda['WhatsApp'] = df_agenda.apply(generar_link_whatsapp, axis=1)
            
            # Ordenar por fecha y hora
            df_agenda = df_agenda.sort_values(by=['fecha', 'hora'])
            
            st.data_editor(
                df_agenda,
                column_config={
                    "WhatsApp": st.column_config.LinkColumn("Enviar", display_text="📲 Avisar"),
                    "fecha": "Día",
                    "hora": "Hora"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No hay citas registradas.")
