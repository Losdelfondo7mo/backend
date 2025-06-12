import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config.settings import settings

# Método para enviar correo usando SMTP (más simple)
def send_email_smtp(recipients, subject, body_html):
    msg = MIMEText(body_html, 'html')
    msg['Subject'] = subject
    msg['From'] = settings.sender_email
    msg['To'] = ", ".join(recipients)
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(settings.sender_email, settings.app_password)
        server.sendmail(settings.sender_email, recipients, msg.as_string())

# Método para enviar correo usando Gmail API (más avanzado)
def send_email_gmail_api(recipients, subject, body_html):
    try:
        # Autenticación con OAuth2
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", settings.gmail_scopes)
        creds = flow.run_local_server(port=0)
        
        # Construir servicio
        service = build("gmail", "v1", credentials=creds)
        
        # Crear mensaje
        message = MIMEText(body_html, 'html')
        message["to"] = ", ".join(recipients)
        message["subject"] = subject
        
        # Codificar mensaje
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        
        # Enviar mensaje
        message = (service.users().messages().send(userId="me", body=create_message).execute())
        return message
    except HttpError as error:
        print(f'Error al enviar correo: {error}')
        return None

# Plantillas de correo
def obtener_mensaje_registro(username):
    subject = '¡Bienvenid@! Registro Exitoso'
    body = f'''
    <html>
    <body>
        <h2>¡Bienvenid@, {username}!</h2>
        <p>Gracias por registrarte en nuestro servicio. Tu cuenta ha sido creada exitosamente.</p>
        <p>Ahora puedes disfrutar de todas las características y beneficios de nuestra plataforma.</p>
        <p>Si tienes alguna pregunta, no dudes en contactar a nuestro equipo de soporte.</p>
        <br>
        <p>Saludos cordiales,</p>
        <p>El Equipo</p>
    </body>
    </html>
    '''
    return subject, body

def obtener_mensaje_compra(username, product, order_id):
    subject = 'Confirmación de Compra'
    body = f'''
    <html>
    <body>
        <h2>¡Gracias por tu compra, {username}!</h2>
        <p>Nos complace confirmar que tu pedido de <strong>{product}</strong> ha sido procesado exitosamente.</p>
        <p>Detalles del pedido:</p>
        <ul>
            <li>ID de Pedido: {order_id}</li>
            <li>Producto: {product}</li>
        </ul>
        <p>Puedes seguir el estado de tu pedido en el panel de control de tu cuenta.</p>
        <br>
        <p>¡Gracias por comprar con nosotros!</p>
        <p>El Equipo</p>
    </body>
    </html>
    '''
    return subject, body