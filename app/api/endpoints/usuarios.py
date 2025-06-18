from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.usuario import UsuarioModel
from app.schemas.usuario import UsuarioCrear, UsuarioPublic
from app.core.security import obtener_contraseña_hash
from app.services.email_service import send_email_smtp

router = APIRouter()

@router.post("/crear", status_code=201, response_model=UsuarioPublic)
async def crear_usuario(usuario: UsuarioCrear, db: Session = Depends(get_db)):
    try:
        if db.query(UsuarioModel).filter(UsuarioModel.usuario == usuario.usuario).first():
            raise HTTPException(status_code=400, detail="Este nombre de usuario ya está en uso.")

        if db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first():
            raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado.")

        nuevo_usuario = UsuarioModel(
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            usuario=usuario.usuario,
            contraseña_hash=obtener_contraseña_hash(usuario.contraseña)
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

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
            pass 

        return nuevo_usuario 
    
    except HTTPException: 
        raise
    except Exception as e: 
        db.rollback() 
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al procesar tu registro. Inténtalo más tarde.")

@router.get("/verificar/{usuario}", response_model=UsuarioPublic)
async def verificar_usuario(usuario: str, db: Session = Depends(get_db)):
    usuario_existente = db.query(UsuarioModel).filter(
        UsuarioModel.usuario == usuario
    ).first()

    if not usuario_existente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    return usuario_existente
    