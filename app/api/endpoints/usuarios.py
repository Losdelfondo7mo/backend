from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# import logging # Logging puede ser útil para el seguimiento de errores y eventos.

from app.db.session import get_db # Dependencia para obtener la sesión de la base de datos.
from app.models.usuario import UsuarioModel # Modelo SQLAlchemy para la entidad Usuario.
from app.schemas.usuario import UsuarioCrear, UsuarioPublic # Esquemas Pydantic para la creación y visualización de usuarios.
from app.core.security import obtener_contraseña_hash # Función para hashear contraseñas de forma segura.
from app.services.email_service import send_email_smtp # Servicio para el envío de correos electrónicos.

# Configuración de logging (opcional, pero recomendado para producción)
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/crear", status_code=201, response_model=UsuarioPublic)
async def crear_usuario(usuario: UsuarioCrear, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.

    Realiza las siguientes acciones:
    - Verifica si el nombre de usuario o el correo electrónico ya están en uso.
    - Hashea la contraseña antes de almacenarla.
    - Envía un correo electrónico de bienvenida al nuevo usuario.

    Parámetros:
        usuario (UsuarioCrear): Datos del nuevo usuario (nombre, email, contraseña, etc.).
        db (Session): Sesión de SQLAlchemy para interactuar con la base de datos.

    Excepciones:
        HTTPException (400): Si el nombre de usuario o email ya existen.
        HTTPException (500): Para errores inesperados durante el proceso de creación.

    Retorna:
        UsuarioPublic: Los datos públicos del usuario recién creado (sin la contraseña).
    """
    try:
        # Comprueba si ya existe un usuario con el mismo nombre de usuario.
        if db.query(UsuarioModel).filter(UsuarioModel.usuario == usuario.usuario).first():
            raise HTTPException(status_code=400, detail="Este nombre de usuario ya está en uso.")

        # Comprueba si ya existe un usuario con el mismo correo electrónico.
        if db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first():
            raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado.")

        # Crea una nueva instancia del modelo Usuario con los datos proporcionados.
        nuevo_usuario = UsuarioModel(
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            usuario=usuario.usuario,
            contraseña_hash=obtener_contraseña_hash(usuario.contraseña) # Hashea la contraseña.
        )

        db.add(nuevo_usuario) # Agrega el nuevo usuario a la sesión de la base de datos.
        db.commit() # Confirma la transacción para guardar el usuario.
        db.refresh(nuevo_usuario) # Actualiza la instancia con datos generados por la BD (como el ID).

        # Prepara y envía un correo de bienvenida.
        subject = "¡Bienvenid@ a Nuestra Plataforma!"
        body = f"""
        <html>
        <body>
            <h2>¡Hola, {usuario.usuario}!</h2>
            <p>Te damos la bienvenida. Tu cuenta ha sido creada con éxito.</p>
            <p>¡Esperamos que disfrutes de nuestros servicios!</p>
            <br>
            <p>Atentamente,</p>
            <p>El Equipo de la Plataforma</p>
        </body>
        </html>
        """
        try:
            send_email_smtp([usuario.email], subject, body)
        except Exception as email_exc:
            # logger.error(f"Fallo al enviar email de bienvenida a {usuario.email}: {email_exc}")
            # Se decide no interrumpir el registro si solo falla el envío del correo.
            pass 

        # Devuelve los datos del usuario creado, utilizando el esquema UsuarioPublic para no exponer el hash de la contraseña.
        return nuevo_usuario 
    
    except HTTPException: 
        # Si es una excepción HTTP ya controlada (ej. usuario duplicado), la relanza.
        raise
    except Exception as e: 
        # Para cualquier otro error inesperado, revierte la transacción y registra el error.
        db.rollback() 
        # logger.error(f"Error inesperado al crear el usuario {usuario.usuario}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al procesar tu registro. Inténtalo más tarde.")

@router.get("/verificar/{usuario}", response_model=UsuarioPublic)
async def verificar_usuario(usuario: str, db: Session = Depends(get_db)):
    """
    Obtiene y devuelve la información pública de un usuario específico por su nombre de usuario.
    Importante: Este endpoint NO devuelve el hash de la contraseña.

    Parámetros:
        usuario (str): El nombre de usuario a buscar.
        db (Session): Sesión de SQLAlchemy para la base de datos.

    Excepciones:
        HTTPException (404): Si el usuario no se encuentra.

    Retorna:
        UsuarioPublic: La información pública del usuario encontrado.
    """
    usuario_existente = db.query(UsuarioModel).filter(
        UsuarioModel.usuario == usuario
    ).first()

    if not usuario_existente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    # Pydantic se encarga de la conversión al modelo de respuesta UsuarioPublic,
    # asegurando que solo se expongan los campos definidos en ese esquema.
    return usuario_existente
    