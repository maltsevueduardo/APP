import streamlit as st
import pandas as pd
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date
import os

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y LOGO
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Seguimiento de Obra", layout="centered")

# Asegúrate de subir un archivo 'logo.png' a tu repositorio de GitHub
try:
    st.image("logo.png", width=250)
except:
    st.warning("⚠️ Logo no encontrado. Sube una imagen llamada 'logo.png' al repositorio.")

st.title("App de Seguimiento de Obra")

# -----------------------------------------------------------------------------
# INICIALIZACIÓN DE VARIABLES EN MEMORIA (Session State)
# -----------------------------------------------------------------------------
# Esto permite que los datos no se borren al interactuar con la app
if 'registros' not in st.session_state:
    st.session_state['registros'] = []

# -----------------------------------------------------------------------------
# FORMULARIO DE ENTRADA DE DATOS
# -----------------------------------------------------------------------------
st.header("Nuevo Registro")

# Listas de opciones
lista_tareas = [
    "Trazado y marcado de cajas, tubos y cuadros",
    "Ejecución rozas en paredes y techos",
    "Montaje de soportes",
    "Colocación tubos y conductos",
    "Tendido de cables",
    "Identificación y etiquetado",
    "Conexionado de cables en bornes o regletas",
    "Instalación y conexionado de mecanismos",
    "Fijación de carril DIN y mecanismos en cuadro eléctrico",
    "Cableado interno del cuadro eléctrico",
    "Configuración de equipos domóticos y/o automáticos",
    "Conexionado de sensores/actuadores de equipos domóticos/automáticos",
    "Pruebas de continuidad",
    "Pruebas de aislamiento",
    "Verificación de tierras",
    "Programación del automatismo",
    "Pruebas de funcionamiento"
]

lista_estados = [
    "Avance de la tarea en torno al 25% aprox.",
    "Avance de la tarea en torno al 50% aprox.",
    "Avance de la tarea en torno al 75% aprox.",
    "OK, finalizado sin errores",
    "Finalizado, pero con errores pendientes de corregir",
    "Finalizado y corregidos los errores"
]

with st.form("formulario_obra"):
    tarea = st.selectbox("Selecciona la tarea de la obra:", lista_tareas)
    estado = st.selectbox("Estado de la tarea:", lista_estados)
    trabajador = st.text_input("Nombre del trabajador:")
    fecha = st.date_input("Fecha del informe:", date.today())
    
    submit_button = st.form_submit_button(label="Añadir al informe")

if submit_button:
    if trabajador.strip() == "":
        st.error("Por favor, indica el nombre del trabajador.")
    else:
        # Guardar el registro en la memoria temporal
        st.session_state['registros'].append({
            "Fecha": fecha.strftime("%d/%m/%Y"),
            "Trabajador": trabajador,
            "Tarea": tarea,
            "Estado": estado
        })
        st.success("✅ Registro añadido correctamente.")

# -----------------------------------------------------------------------------
# VISUALIZACIÓN Y GESTIÓN DE DATOS (EXCEL Y CORREO)
# -----------------------------------------------------------------------------
if st.session_state['registros']:
    st.divider()
    st.subheader("Registros Actuales")
    
    # Crear un DataFrame de Pandas con los registros
    df = pd.DataFrame(st.session_state['registros'])
    st.dataframe(df, use_container_width=True)
    
    # Crear el archivo Excel en memoria
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Seguimiento')
    excel_data = buffer.getvalue()
    
    col1, col2 = st.columns(2)
    
    # Botón para descargar el Excel
    with col1:
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_data,
            file_name="informe_obra.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Botón y lógica para enviar por correo
    with col2:
        if st.button("✉️ Enviar a la empresa"):
            try:
                # Configuración del correo (Se obtienen de los secrets de Streamlit)
                remitente = st.secrets["email"]["remitente"]
                password = st.secrets["email"]["password"]
                destinatario = st.secrets["email"]["destinatario"]
                
                # Creación del mensaje
                msg = MIMEMultipart()
                msg['From'] = remitente
                msg['To'] = destinatario
                msg['Subject'] = f"Informe de Obra - {date.today().strftime('%d/%m/%Y')}"
                
                cuerpo = "Adjunto se remite el informe de seguimiento de obra generado desde la app."
                msg.attach(MIMEText(cuerpo, 'plain'))
                
                # Adjuntar el archivo Excel
                adjunto = MIMEBase('application', 'octet-stream')
                adjunto.set_payload(excel_data)
                encoders.encode_base64(adjunto)
                adjunto.add_header('Content-Disposition', 'attachment; filename="informe_obra.xlsx"')
                msg.attach(adjunto)
                
                # Conexión al servidor SMTP (Ejemplo con Gmail)
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(remitente, password)
                server.send_message(msg)
                server.quit()
                
                st.success(f"📧 Excel enviado correctamente a {destinatario}")
                
            except Exception as e:
                st.error("❌ Hubo un error al enviar el correo. Verifica las credenciales en st.secrets.")
                st.exception(e)
