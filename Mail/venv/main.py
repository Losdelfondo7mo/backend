# Importamos las bibliotecas necesarias para enviar correos electrónicos
import smtplib  # Biblioteca para conectarse al servidor SMTP

# Importamos la contraseña de aplicación desde el archivo envs.py
from envs import APP_PASSWORD
# Importamos clases para crear mensajes de texto y mensajes multiparte
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración del correo electrónico
# Dirección de correo del remitente (debe ser una cuenta de Gmail válida)
sender = 'losdelfondo7moetp@gmail.com'
# Lista de destinatarios que recibirán el correo
recipients = [sender, 'noahchamo@gmail.com']

# Definición de plantillas de mensajes para diferentes propósitos

# Función para crear mensaje de registro exitoso
# Parámetros:
#   - username: nombre del usuario que se registró
# Retorna: asunto y cuerpo del mensaje en formato HTML
def obtener_mensaje_registro(username):
    subject = '¡Bienvenid@! Registro Exitoso'  # Asunto del correo
    # Cuerpo del mensaje en formato HTML usando f-strings para insertar el nombre de usuario
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
    return subject, body  # Retornamos una tupla con el asunto y cuerpo

# Función para crear mensaje de confirmación de compra
# Parámetros:
#   - username: nombre del usuario que realizó la compra
#   - product: nombre del producto comprado
#   - order_id: identificador único de la orden
# Retorna: asunto y cuerpo del mensaje en formato HTML
def obtener_mensaje_compra(username, product, order_id):
    subject = 'Confirmación de Compra'  # Asunto del correo
    # Cuerpo del mensaje en formato HTML con detalles de la compra
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
    return subject, body  # Retornamos una tupla con el asunto y cuerpo

# Función para crear mensaje de notificación de envío
# Parámetros:
#   - username: nombre del usuario destinatario
#   - order_id: identificador único de la orden
#   - estimated_delivery: fecha estimada de entrega
# Retorna: asunto y cuerpo del mensaje en formato HTML
def obtener_mensaje_envio(username, order_id, estimated_delivery):
    subject = 'Tu Paquete Está Listo para Enviar'  # Asunto del correo
    # Cuerpo del mensaje en formato HTML con detalles del envío
    body = f'''
    <html>
    <body>
        <h2>¡Buenas noticias, {username}!</h2>
        <p>Tu paquete está a punto de ser enviado.</p>
        <p>Detalles del envío:</p>
        <ul>
            <li>ID de Pedido: {order_id}</li>
            <li>Fecha estimada de entrega: {estimated_delivery}</li>
        </ul>
        <p>Recibirás un número de seguimiento una vez que tu paquete esté en camino.</p>
        <br>
        <p>¡Gracias por tu paciencia!</p>
        <p>El Equipo</p>
    </body>
    </html>
    '''
    return subject, body  # Retornamos una tupla con el asunto y cuerpo

# Función principal para enviar correos electrónicos HTML
# Parámetros:
#   - subject: asunto del correo
#   - body: cuerpo del mensaje en formato HTML
#   - sender: dirección de correo del remitente
#   - recipients: lista de destinatarios
def enviar_correo(subject, body, sender, recipients):
    # Creamos un mensaje multiparte para soportar contenido HTML
    msg = MIMEMultipart()
    # Configuramos los encabezados del correo
    msg['Subject'] = subject  # Asunto
    msg['From'] = sender      # Remitente
    msg['To'] = ', '.join(recipients)  # Convertimos la lista de destinatarios a string separado por comas
    
    # Adjuntamos el contenido HTML al mensaje
    html_part = MIMEText(body, 'html')  # Creamos la parte HTML del mensaje
    msg.attach(html_part)  # La adjuntamos al mensaje multiparte
    
    # Enviamos el correo electrónico usando el protocolo SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:  # Conexión segura al servidor SMTP de Gmail
        server.login(sender, APP_PASSWORD)  # Autenticación con credenciales
        server.sendmail(sender, recipients, msg.as_string())  # Envío del mensaje
        server.quit()  # Cerramos la conexión
    print(f'Correo enviado: {subject}')  # Confirmación en consola

# Ejemplos de uso - descomenta el que quieras enviar

# Enviar confirmación de registro
# Paso 1: Definimos el nombre de usuario
username = "Ivana Rojas(hola profe :D)"
# Paso 2: Obtenemos el asunto y cuerpo del mensaje usando la función correspondiente
sub, msg = obtener_mensaje_registro(username)
# Paso 3: Enviamos el correo con los datos obtenidos
enviar_correo(sub, msg, sender, recipients)

# Enviar confirmación de compra
# Descomenta estas líneas para enviar un correo de confirmación de compra
username = "Ivana Rojas"  # Nombre del usuario
product = "Suscripción Premium"  # Producto comprado
order_id = "ORD-12345"  # ID de la orden
sub, msg = obtener_mensaje_compra(username, product, order_id)  # Generamos el mensaje
enviar_correo(sub, msg, sender, recipients)  # Enviamos el correo

# Enviar notificación de envío
# Descomenta estas líneas para enviar un correo de notificación de envío
username = "Ivana Rojas"  # Nombre del usuario
order_id = "ORD-12345"  # ID de la orden
estimated_delivery = "15 de junio de 2023"  # Fecha estimada de entrega
sub, msg = obtener_mensaje_envio(username, order_id, estimated_delivery)  # Generamos el mensaje
enviar_correo(sub, msg, sender, recipients)  # Enviamos el correo
