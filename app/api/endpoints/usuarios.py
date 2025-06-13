from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.usuario import UsuarioModel
from app.schemas.usuario import UsuarioCrear
from app.core.security import obtener_contraseña_hash
from app.services.email_service import send_email_smtp

router = APIRouter()

@router.post("/crear", status_code=201)
async def crear_usuario(usuario: UsuarioCrear, db: Session = Depends(get_db)):
    try:
        # Verificar si ya existe el usuario o email
        if db.query(UsuarioModel).filter(UsuarioModel.usuario == usuario.usuario).first():
            raise HTTPException(status_code=400, detail="Este usuario ya existe")

        if db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first():
            raise HTTPException(status_code=400, detail="Este email ya está registrado")

        # Crear usuario nuevo
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

        # Enviar correo de bienvenida
        subject = "¡Bienvenid@! Registro Exitoso"
        body = f'''
        <html>
        <body>
            <h2>¡Bienvenid@, {usuario.usuario}!</h2>
            <p>Gracias por registrarte en nuestro servicio. Tu cuenta ha sido creada exitosamente.</p>
            <p>Ahora puedes disfrutar de todas las características y beneficios de nuestra plataforma.</p>
            <p>Si tienes alguna pregunta, no dudes en contactar a nuestro equipo de soporte.</p>
            <br>
            <p>Saludos cordiales,</p>
            <p>El Equipo</p>
        </body>
        </html>
        '''
        send_email_smtp([usuario.email], subject, body)

        return {"mensaje": "Usuario creado exitosamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verificar/{usuario}")
async def verificar_usuario(usuario: str, db: Session = Depends(get_db)):
    usuario_existente = db.query(UsuarioModel).filter(
        UsuarioModel.usuario == usuario
    ).first()

    if not usuario_existente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {
        "usuario": usuario_existente.usuario,
        "contraseña": usuario_existente.contraseña_hash,
        "nombre": f"{usuario_existente.nombre} {usuario_existente.apellido}",
        "email": usuario_existente.email
    }
    