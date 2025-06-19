import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config.settings import settings

def send_email_smtp(recipients: list, subject: str, body_html: str):
    """
    Envía un correo electrónico utilizando SMTP, configurado para Gmail.

    Este método es más simple y no requiere el flujo OAuth2 completo, pero necesita
    que la "Verificación en dos pasos" esté activada en la cuenta de Gmail y
    una "Contraseña de aplicación" generada para ser usada en `settings.app_password`.

    Parámetros:
        recipients (list): Lista de direcciones de correo de los destinatarios.
        subject (str): Asunto del correo electrónico.
        body_html (str): Contenido del correo en formato HTML.
    """
    msg = MIMEText(body_html, 'html') # Crea el objeto mensaje con contenido HTML.
    msg['Subject'] = subject
    msg['From'] = settings.sender_email
    msg['To'] = ", ".join(recipients) # Une la lista de destinatarios en una cadena.
    
    try:
        # Conecta con el servidor SMTP de Gmail.
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls() # Inicia TLS para una conexión segura.
            server.login(settings.sender_email, settings.app_password) # Autenticación.
            server.sendmail(settings.sender_email, recipients, msg.as_string()) # Envía el correo.
        # print(f"Correo SMTP enviado a {', '.join(recipients)} con asunto: {subject}")
    except Exception as e:
        print(f"Error al enviar correo SMTP: {e}")
        # Considerar relanzar la excepción o manejarla de forma más robusta.

def send_email_gmail_api(recipients: list, subject: str, body_html: str):
    """
    Envía un correo electrónico utilizando la API de Gmail con autenticación OAuth2.

    Este método es más seguro y recomendado por Google, pero requiere configurar
    credenciales de OAuth2 (archivo `credentials.json`) y que el usuario autorice
    la aplicación la primera vez.

    Parámetros:
        recipients (list): Lista de direcciones de correo de los destinatarios.
        subject (str): Asunto del correo electrónico.
        body_html (str): Contenido del correo en formato HTML.

    Retorna:
        dict: La respuesta de la API de Gmail si el envío es exitoso, o None si falla.
    """
    try:
        # Inicia el flujo de autenticación OAuth2 para obtener credenciales.
        # 'credentials.json' debe estar en el directorio raíz o en una ruta accesible.
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", settings.gmail_scopes)
        creds = flow.run_local_server(port=0) # Abre el navegador para la autorización del usuario.
        
        # Construye el objeto de servicio para interactuar con la API de Gmail.
        service = build("gmail", "v1", credentials=creds)
        
        # Crea el mensaje de correo.
        message = MIMEText(body_html, 'html')
        message["to"] = ", ".join(recipients)
        message["subject"] = subject
        
        # Codifica el mensaje en base64 URL-safe, como requiere la API.
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message_request = {'raw': encoded_message}
        
        # Envía el mensaje utilizando el servicio de la API.
        sent_message = (service.users().messages().send(userId="me", body=create_message_request).execute())
        # print(f"Correo API Gmail enviado a {', '.join(recipients)}. ID: {sent_message.get('id')}")
        return sent_message
    except HttpError as error:
        print(f'Error al enviar correo con Gmail API: {error}')
        return None
    except FileNotFoundError:
        print("Error: El archivo 'credentials.json' no fue encontrado. Necesario para Gmail API.")
        return None

# --- Plantillas de Correo (Ejemplos) ---
# Estas funciones generan el asunto y cuerpo para tipos comunes de correos.

def obtener_mensaje_registro(username: str) -> tuple[str, str]:
    """Genera el asunto y cuerpo HTML para un correo de bienvenida al registrarse."""
    subject = '¡Bienvenid@! Tu Registro Ha Sido Exitoso'
    body = f"""
    <html>
    <body>
        <h2>¡Bienvenid@, {username}!</h2>
        <p>Gracias por registrarte en nuestra plataforma. Tu cuenta ha sido creada exitosamente.</p>
        <p>Ya puedes acceder y disfrutar de todas las funcionalidades.</p>
        <p>Si tienes alguna pregunta, no dudes en contactar a nuestro equipo de soporte.</p>
        <br>
        <p>Saludos cordiales,</p>
        <p>El Equipo de la Plataforma</p>
    </body>
    </html>
    """
    return subject, body

def obtener_mensaje_compra(username: str, product_name: str, order_id: str) -> tuple[str, str]:
    """Genera el asunto y cuerpo HTML para un correo de confirmación de compra."""
    subject = 'Confirmación de Tu Compra'
    body = f"""
    <html>
    <body>
        <h2>¡Gracias por tu compra, {username}!</h2>
        <p>Nos complace confirmar que tu pedido de <strong>{product_name}</strong> ha sido procesado.</p>
        <p>Detalles del pedido:</p>
        <ul>
            <li>ID de Pedido: {order_id}</li>
            <li>Producto: {product_name}</li>
        </ul>
        <p>Puedes revisar el estado de tu pedido en tu panel de control.</p>
        <br>
        <p>¡Gracias por elegirnos!</p>
        <p>El Equipo de la Plataforma</p>
    </body>
    </html>
    """
    return subject, body