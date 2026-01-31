import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN ---
NOMBRE_NEGOCIO = "Lo del Fer" 
COLOR_PRIMARIO = "#E91E63"
PASSWORD_CORRECTA = "admin2024"

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
# La conexión usa los Secrets configurados en Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    # ttl=0 para que no guarde caché y siempre traiga lo último de Google Sheets
    # .iloc[:, 0:5] fuerza a leer solo las primeras 5 columnas (A a E)
    try:
        df = conn.read(ttl=0)
        if df.empty:
            return pd.DataFrame(columns=["cliente", "telefono", "fecha", "hora", "servicio"])
        return df.iloc[:, 0:5].dropna(how="all")
    except:
        return pd.DataFrame(columns=["cliente", "telefono", "fecha", "hora", "servicio"])

def generar_link_whatsapp(fila):
    # Limpiar el teléfono para que solo tenga números
    tel = "".join(filter(str.isdigit, str(fila['telefono'])))
    mensaje = f"👋 Hola *{fila['cliente']}*, recordatorio de cita en *{NOMBRE_NEGOCIO}* para el día {fila['fecha']} a las {fila['hora']}."
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

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
    # --- APP PRINCIPAL ---
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
            servicio = st.selectbox("Servicio", ["Corte", "Manicura", "Masajes", "Barba", "Otro"])
            
            if st.form_submit_button("Guardar Cita"):
                if nombre and tel:
                    # 1. Obtener datos actuales
                    df_actual = leer_datos()
                    
                    # 2. Crear nueva fila
                    nueva_cita = pd.DataFrame([{
                        "cliente": nombre, 
                        "telefono": tel, 
                        "fecha": str(fecha), 
                        "hora": str(hora), 
                        "servicio": servicio
                    }])
                    
                    # 3. Concatenar (asegura que la nueva cita vaya abajo)
                    df_final = pd.concat([df_actual, nueva_cita], ignore_index=True)
                    
                    # 4. Limpiar columnas por seguridad antes de subir
                    df_final = df_final[["cliente", "telefono", "fecha", "hora", "servicio"]]
                    
                    # 5. Actualizar Google Sheets
                    conn.update(data=df_final)
                    
                    st.success(f"✅ ¡Cita de {nombre} guardada!")
                    st.balloons()
                else:
                    st.warning("⚠️ Por favor completa el nombre y el teléfono.")

    with tab2:
        st.subheader("Agenda de Clientes")
        df_agenda = leer_datos()
        
        # Filtrar filas vacías que puedan venir de la lectura
        df_agenda = df_agenda[df_agenda['cliente'].notna()]

        if not df_agenda.empty:
            # Agregar columna de WhatsApp
            df_agenda['WhatsApp'] = df_agenda.apply(generar_link_whatsapp, axis=1)
            
            st.data_editor(
                df_agenda,
                column_config={
                    "WhatsApp": st.column_config.LinkColumn("Enviar", display_text="📲 Enviar WhatsApp")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No hay citas registradas todavía.")
