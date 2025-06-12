from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from app.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contraseña(contraseña_plana: str, contraseña_hash: str):
    return pwd_context.verify(contraseña_plana, contraseña_hash)

def obtener_contraseña_hash(contraseña: str):
    return pwd_context.hash(contraseña)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt