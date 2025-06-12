import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import APP_PASSWORD, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SENDER_EMAIL, GMAIL_SCOPES

# --- Configuración de seguridad ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funciones de autenticación ---
def verificar_contraseña(contraseña_plana: str, contraseña_hash: str):
    return pwd_context.verify(contraseña_plana, contraseña_hash)

def obtener_contraseña_hash(contraseña: str):
    return pwd_context.hash(contraseña)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Funciones de correo electrónico ---
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

def send_email_smtp(recipients, subject, body):
    """Envía correo usando SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipients, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

def send_email_gmail_api(to_email, subject, body):
    """Envía correo usando Gmail API"""
    try:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", GMAIL_SCOPES)
        creds = flow.run_local_server(port=0)
        service = build("gmail", "v1", credentials=creds)
        
        message = MIMEText(body, 'html')
        message["to"] = to_email
        message["subject"] = subject
        
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        
        message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f'Mensaje enviado a {to_email} Message Id: {message["id"]}')
        return True
    except HttpError as error:
        print(f'Error occurred: {error}')
        return False