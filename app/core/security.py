from passlib.context import CryptContext # Utilizado para el hashing seguro de contraseñas.
from datetime import datetime, timedelta # Necesario para establecer la expiración de los tokens.
from jose import jwt, JWTError # Para crear y decodificar JSON Web Tokens (JWT).
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Esquema de seguridad para obtener tokens Bearer de las cabeceras.

from app.config.settings import settings # Acceso a la configuración de la aplicación (SECRET_KEY, ALGORITHM, etc.).
from app.schemas.token import TokenData # Esquema Pydantic para los datos contenidos en el token.
from app.models.usuario import UsuarioModel # Modelo SQLAlchemy para la entidad Usuario.
from sqlalchemy.orm import Session # Para el tipado y la inyección de la sesión de base de datos.
from app.db.session import get_db # Dependencia para obtener la sesión de la base de datos.

# Configura el contexto de Passlib para el hashing de contraseñas.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define el esquema OAuth2 para la obtención de tokens. 'tokenUrl' debe apuntar al endpoint de login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verificar_contraseña(contraseña_plana: str, contraseña_hash: str) -> bool:
    """
    Compara una contraseña en texto plano con su versión hasheada almacenada.

    Parámetros:
        contraseña_plana (str): La contraseña ingresada por el usuario (sin hashear).
        contraseña_hash (str): La contraseña hasheada guardada en la base de datos.

    Retorna:
        bool: True si las contraseñas coinciden, False en caso contrario.
    """
    return pwd_context.verify(contraseña_plana, contraseña_hash)

def obtener_contraseña_hash(contraseña: str) -> str:
    """
    Genera un hash seguro para una contraseña proporcionada.

    Parámetros:
        contraseña (str): La contraseña en texto plano que se va a hashear.

    Retorna:
        str: La representación hasheada de la contraseña.
    """
    return pwd_context.hash(contraseña)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Crea un nuevo token de acceso JWT.

    Parámetros:
        data (dict): Diccionario con los datos a incluir en el payload del token (ej. {'sub': 'username'}).
        expires_delta (timedelta, opcional): Tiempo de vida específico para este token.
                                            Si es None, se usa el valor de la configuración.

    Retorna:
        str: El token JWT codificado como una cadena de texto.
    """
    to_encode = data.copy() # Evita modificar el diccionario original.
    # Determina el tiempo de expiración del token.
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire}) # Agrega la marca de tiempo de expiración al payload.
    
    # Codifica el payload en un token JWT usando la clave secreta y el algoritmo definidos.
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UsuarioModel:
    """
    Dependencia de FastAPI para obtener el usuario actual a partir de un token JWT.

    Decodifica el token, extrae el nombre de usuario (del campo 'sub') y recupera
    el usuario correspondiente de la base de datos.

    Parámetros:
        token (str): El token JWT extraído de la cabecera de autorización.
        db (Session): Sesión de SQLAlchemy para la base de datos.

    Excepciones:
        HTTPException (401): Si el token es inválido, ha expirado, o el usuario no se encuentra.

    Retorna:
        UsuarioModel: La instancia del modelo Usuario correspondiente al token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el token usando la clave secreta y el algoritmo.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub") # 'sub' (subject) es el identificador del usuario en el token.
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username) # Valida los datos del token con el esquema Pydantic.
    except JWTError:
        # Si hay cualquier error durante la decodificación (ej. firma inválida, token expirado).
        raise credentials_exception
    
    # Busca al usuario en la base de datos.
    user = db.query(UsuarioModel).filter(UsuarioModel.usuario == token_data.username).first()
    if user is None:
        # Si el usuario extraído del token no existe en la base de datos.
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UsuarioModel = Depends(get_current_user)) -> UsuarioModel:
    """
    Dependencia para obtener el usuario actual que también está activo.
    Actualmente, solo devuelve el usuario obtenido por `get_current_user`.
    Se podría extender para verificar un campo `is_active` en el modelo `UsuarioModel`.

    Parámetros:
        current_user (UsuarioModel): El usuario obtenido de la dependencia `get_current_user`.

    Excepciones:
        HTTPException (400): Si se implementa la lógica de 'is_active' y el usuario está inactivo.

    Retorna:
        UsuarioModel: El usuario activo.
    """
    # Ejemplo de cómo se podría verificar si el usuario está activo:
    # if not current_user.is_active: # Asumiendo que UsuarioModel tiene un atributo 'is_active'.
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return current_user