# Importamos las bibliotecas necesarias para enviar correos electrónicos
import smtplib  # Biblioteca para conectarse al servidor SMTP
# Importaciones necesarias de FastAPI y otras bibliotecas
from fastapi import FastAPI, Depends, HTTPException, status # Corregido: HttpException -> HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel # Para definir modelos de datos
from datetime import datetime, timedelta # Para manejar fechas y tiempos, especialmente para la expiración del token
from jose import JWTError, jwt # Para crear y verificar JSON Web Tokens (JWT)
from passlib.context import CryptContext # Para el hashing seguro de contraseñas
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String
# Importamos la contraseña de aplicación desde el archivo envs.py
from envs import APP_PASSWORD
# Importamos clases para crear mensajes de texto y mensajes multiparte
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --- Configuración de Seguridad y JWT ---
# Clave secreta para firmar los JWT. ¡Debe ser secreta y compleja en producción!
SECRET_KEY = "c67d978e20f38a9a00db5e4e60de978d93e0e3031b18e6c248e928bd3b9fad5b"
# Algoritmo utilizado para la firma de JWT
ALGORITHM = "HS256"
# Tiempo de expiración para los tokens de acceso en minutos
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Simulación de Base de Datos ---
# En una aplicación real, esto se conectaría a una base de datos (SQL, NoSQL, etc.)
# Aquí simulamos una base de datos de usuarios en un diccionario.
db = {
    "users": {
        "natalia": {
            "username": "natalia", # Nombre de usuario único
            "full_name": "Natalia Ejemplo", # Nombre completo del usuario
            "email": "natalia@example.com", # Email del usuario
            "hashed_password": "$2b$12$3.isCzlQdBsGkfMP1JHhHuJK0xSajNlx21BA2sBbLDYa8Y/Owl056"
            # Ejemplo: "hashed_password": "$2b$12$somehashvalue..."
        },
        "jairo": {
            "username": "jairo",
            "full_name": "Jairo Ejemplo",
            "email": "jairo@example.com",
            "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", # Contraseña ya hasheada
            "disabled": False, # Indica si el usuario está deshabilitado
        },
    }
}

# --- Modelos Pydantic (para validación y serialización de datos) ---

# Modelo para la respuesta del token
class Token(BaseModel):
    access_token: str  # El token de acceso JWT
    token_type: str    # Tipo de token (generalmente "bearer")

# Modelo para los datos contenidos dentro del token JWT
class TokenData(BaseModel):
    username: str | None = None # Nombre de usuario extraído del token

# Modelo base para la información del usuario
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    password: str | None = None # Contraseña en texto plano, no se almacena en la base de datos
    disabled: bool | None = None # Si el usuario está o no activo

# Modelo para el usuario tal como se almacena en la "base de datos" (incluye la contraseña hasheada)
class UserInDB(User):
    hashed_password: str

# --- Configuración de Hashing de Contraseñas ---
# Se utiliza bcrypt para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Configuración de OAuth2 ---
# Define el esquema de seguridad OAuth2, especificando la URL del endpoint de token
oath_2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# --- Funciones Auxiliares ---


# Configuración del correo electrónico
# Dirección de correo del remitente (debe ser una cuenta de Gmail válida)
sender = 'losdelfondo7moetp@gmail.com'
# Lista de destinatarios que recibirán el correo
recipients = [sender, 'noahchamo@gmail.com']


# --- Configuración de Seguridad y JWT ---
# Clave secreta para firmar los JWT. ¡Debe ser secreta y compleja en producción!
SECRET_KEY = "c67d978e20f38a9a00db5e4e60de978d93e0e3031b18e6c248e928bd3b9fad5b"
# Algoritmo utilizado para la firma de JWT
ALGORITHM = "HS256"
# Tiempo de expiración para los tokens de acceso en minutos
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Simulación de Base de Datos ---
# En una aplicación real, esto se conectaría a una base de datos (SQL, NoSQL, etc.)
# Aquí simulamos una base de datos de usuarios en un diccionario.
db = {
    "users": {
        "natalia": {
            "username": "natalia", # Nombre de usuario único
            "full_name": "Natalia Ejemplo", # Nombre completo del usuario
            "email": "natalia@example.com", # Email del usuario
            "hashed_password": "$2b$12$3.isCzlQdBsGkfMP1JHhHuJK0xSajNlx21BA2sBbLDYa8Y/Owl056"
            # Ejemplo: "hashed_password": "$2b$12$somehashvalue..."
        },
        "jairo": {
            "username": "jairo",
            "full_name": "Jairo Ejemplo",
            "email": "jairo@example.com",
            "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", # Contraseña ya hasheada
            "disabled": False, # Indica si el usuario está deshabilitado
        },
    }
}

# --- Modelos Pydantic (para validación y serialización de datos) ---

# Modelo para la respuesta del token
class Token(BaseModel):
    access_token: str  # El token de acceso JWT
    token_type: str    # Tipo de token (generalmente "bearer")

# Modelo para los datos contenidos dentro del token JWT
class TokenData(BaseModel):
    username: str | None = None # Nombre de usuario extraído del token

# Modelo base para la información del usuario
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    password: str | None = None # Contraseña en texto plano, no se almacena en la base de datos
    disabled: bool | None = None # Si el usuario está o no activo

# Modelo para el usuario tal como se almacena en la "base de datos" (incluye la contraseña hasheada)
class UserInDB(User):
    hashed_password: str

# --- Configuración de Hashing de Contraseñas ---
# Se utiliza bcrypt para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Configuración de OAuth2 ---
# Define el esquema de seguridad OAuth2, especificando la URL del endpoint de token
oath_2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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

# --- Instancia de la Aplicación FastAPI ---
app = FastAPI()

# --- Funcionalidad Registrar Usuario ---
@app.post("/registro/", response_model=User)
async def registrar_usuario(user: User):
    # Verifica si el usuario ya existe en la base de datos
    if user.username in db['users']:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    # Hashea la contraseña del usuario
    hashed_password = obtener_hash_contrasena(user.password)

    # Crea un nuevo usuario en la base de datos
    nuevo_usuario = UserInDB(**user.dict(), hashed_password=hashed_password)
    db['users'][user.username] = nuevo_usuario.dict()

    # Retorna el usuario creado
    return nuevo_usuario

# --- Funcionalidad Login ---
@app.post("/login/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Autentica al usuario usando los datos del formulario (username y password)
    user = autenticar_usuario(db, form_data.username, form_data.password)
    if not user: # Si la autenticación falla
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )



# --- Funciones de Utilidad para Autenticación y Usuarios ---

# Verifica si una contraseña en texto plano coincide con una contraseña hasheada
def verificar_contraseña(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Genera un hash de una contraseña en texto plano
def obtener_hash_contraseña(password):
    return pwd_context.hash(password)

# Obtiene un usuario de la "base de datos" por su nombre de usuario
def obtener_usuario(db_users, username: str):
    if username in db_users: # Verifica si el usuario existe en el diccionario de usuarios
        user_data = db_users[username] # Obtiene los datos del usuario
        return UserInDB(**user_data) # Retorna un objeto UserInDB con los datos
    return None # Retorna None si el usuario no se encuentra

# Autentica a un usuario comparando el nombre de usuario y la contraseña proporcionados
def autenticar_usuario(db_auth, username: str, password: str):
    user = obtener_usuario(db_auth['users'], username) # Intenta obtener el usuario
    if not user: # Si el usuario no existe
        return False
    if not user.hashed_password: # Si el usuario existe pero no tiene contraseña hasheada (ej. no completó registro)
        # Podrías lanzar una excepción específica o manejarlo de otra forma
        # Por ahora, para el flujo de login, si no hay hash, no se puede verificar.
        return False
    if not verificar_contraseña(password, user.hashed_password): # Si la contraseña no coincide
        return False
    return user # Retorna el objeto UserInDB si la autenticación es exitosa

# Crea un nuevo token de acceso JWT
def crear_token_acceso(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy() # Copia los datos para no modificar el original
    if expires_delta: # Si se proporciona un tiempo de expiración personalizado
        expire = datetime.utcnow() + expires_delta
    else: # Sino, usa un tiempo de expiración por defecto (15 minutos)
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire}) # Añade la fecha de expiración al payload del token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # Codifica el token
    return encoded_jwt

# --- Funciones de Dependencia para Rutas Protegidas ---

# Obtiene el usuario actual a partir del token JWT proporcionado en la cabecera Authorization
async def obtener_usuario_actual(token: str = Depends(oath_2_scheme)):
    # Excepción estándar para credenciales inválidas
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el token para obtener el payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # "sub" es el campo estándar para el sujeto (usuario)
        if username is None: # Si no hay nombre de usuario en el token
            raise credentials_exception
        token_data = TokenData(username=username) # Valida los datos del token con el modelo Pydantic
    except JWTError: # Si ocurre un error durante la decodificación del JWT
        raise credentials_exception
    
    user = obtener_usuario(db['users'], username=token_data.username) # Obtiene el usuario de la "base de datos"
    if user is None: # Si el usuario extraído del token no existe en la "base de datos"
        raise credentials_exception
    return user # Retorna el objeto UserInDB

# Obtiene el usuario actual que además está activo (no deshabilitado)
async def obtener_usuario_activo_actual(usuario_actual: User = Depends(obtener_usuario_actual)):
    if usuario_actual.disabled: # Verifica si el campo 'disabled' del usuario es True
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return usuario_actual # Retorna el usuario si está activo

# --- Endpoints de la API ---

# Endpoint para el login y obtención de token de acceso
@app.post("/token", response_model=Token)
async def iniciar_sesion_para_token_acceso(form_data: OAuth2PasswordRequestForm = Depends()):
    # Autentica al usuario usando los datos del formulario (username y password)
    user = autenticar_usuario(db, form_data.username, form_data.password)
    if not user: # Si la autenticación falla
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},            
        )
    
    # Define el tiempo de expiración del token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Crea el token de acceso para el usuario autenticado
    access_token = crear_token_acceso(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # Retorna el token de acceso y el tipo de token
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint protegido para obtener la información del usuario actual
@app.get("/users/me/", response_model=User)
async def leer_usuarios_yo(usuario_actual: User = Depends(obtener_usuario_activo_actual)):
    # Esta función depende de `obtener_usuario_activo_actual`,
    # lo que significa que solo usuarios autenticados y activos pueden acceder.
    return usuario_actual # Retorna la información del usuario logueado

# Endpoint protegido de ejemplo para obtener items del usuario actual
@app.get("/users/me/items/")
async def leer_items_propios(usuario_actual: User = Depends(obtener_usuario_activo_actual)):
    # Similar al anterior, requiere un usuario autenticado y activo.
    # Aquí se simula que se retornan items pertenecientes al usuario.
    return [{"item_id": "portal_gun", "owner": usuario_actual.username}]


