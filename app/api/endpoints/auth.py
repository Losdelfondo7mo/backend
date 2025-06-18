from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db  # Proporciona la sesión de base de datos para las operaciones.
from app.models.usuario import UsuarioModel # Modelo de datos para la entidad Usuario.
from app.core.security import verificar_contraseña, create_access_token # Funciones para la gestión de contraseñas y tokens JWT.
from app.schemas.token import Token  # Esquema Pydantic para la estructura de la respuesta del token.
from app.config.settings import settings # Accede a la configuración global, como la duración del token.

router = APIRouter() # Define un nuevo router para agrupar los endpoints de autenticación.

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Autentica a un usuario existente y emite un token de acceso JWT.

    Este endpoint espera los datos de inicio de sesión (`username` y `password`)
    enviados como 'form data', gracias a `OAuth2PasswordRequestForm`.

    Parámetros:
        form_data (OAuth2PasswordRequestForm): Contiene el nombre de usuario y la contraseña.
        db (Session): Sesión de SQLAlchemy para interactuar con la base de datos.

    Excepciones:
        HTTPException (401): Si el nombre de usuario no existe o la contraseña es incorrecta.

    Retorna:
        Token: Un objeto con el `access_token` y el `token_type` (bearer).
    """
    # Busca al usuario por su nombre de usuario en la base de datos.
    usuario_db = db.query(UsuarioModel).filter(UsuarioModel.usuario == form_data.username).first()
    
    # Verifica si el usuario existe y si la contraseña proporcionada es correcta.
    if not usuario_db or not verificar_contraseña(form_data.password, usuario_db.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos.", # Mensaje genérico para no revelar detalles.
            headers={"WWW-Authenticate": "Bearer"}, # Indica el esquema de autenticación esperado.
        )
    
    # Calcula el tiempo de expiración para el token de acceso desde la configuración.
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Genera un nuevo token de acceso JWT, incluyendo el nombre de usuario como 'subject' (sub).
    access_token = create_access_token(
        data={"sub": usuario_db.usuario}, expires_delta=access_token_expires
    )
    # Devuelve el token generado.
    return {"access_token": access_token, "token_type": "bearer"}

