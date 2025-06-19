from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.usuario import UsuarioModel
from app.models.visita import VisitaModel
from app.schemas.usuario import (
    UsuarioCrear, UsuarioPublic, CambiarContraseña, 
    EstadisticasUsuarios, EstadisticasVisitas, AdminCrear
)
from app.core.security import obtener_contraseña_hash, verificar_contraseña
from app.services.email_service import send_email_smtp

router = APIRouter()



@router.get("/verificar/{usuario}", response_model=UsuarioPublic)
async def verificar_usuario(usuario: str, db: Session = Depends(get_db)):
    usuario_existente = db.query(UsuarioModel).filter(
        UsuarioModel.usuario == usuario
    ).first()

    if not usuario_existente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    return usuario_existente

@router.put("/cambiar-contraseña/{usuario_id}", status_code=200)
async def cambiar_contraseña(usuario_id: int, datos: CambiarContraseña, db: Session = Depends(get_db)):
    """
    Endpoint para cambiar la contraseña de un usuario.
    """
    try:
        # Buscar el usuario
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
        # Verificar contraseña actual
        if not verificar_contraseña(datos.contraseña_actual, usuario.contraseña_hash):
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta.")
        
        # Verificar que las nuevas contraseñas coincidan
        if datos.contraseña_nueva != datos.confirmar_contraseña:
            raise HTTPException(status_code=400, detail="Las nuevas contraseñas no coinciden.")
        
        # Verificar que la nueva contraseña sea diferente a la actual
        if verificar_contraseña(datos.contraseña_nueva, usuario.contraseña_hash):
            raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual.")
        
        # Actualizar contraseña
        usuario.contraseña_hash = obtener_contraseña_hash(datos.contraseña_nueva)
        db.commit()
        
        return {"message": "Contraseña actualizada exitosamente."}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al cambiar la contraseña.")

@router.get("/estadisticas", response_model=EstadisticasUsuarios)
async def obtener_estadisticas_usuarios(db: Session = Depends(get_db)):
    """
    Endpoint para obtener estadísticas de usuarios registrados.
    """
    try:
        # Total de usuarios
        total_usuarios = db.query(UsuarioModel).count()
        
        # Usuarios por rol
        administradores = db.query(UsuarioModel).filter(UsuarioModel.rol == "administrador").count()
        usuarios_regulares = db.query(UsuarioModel).filter(UsuarioModel.rol == "usuario").count()
        
        usuarios_activos = total_usuarios
        
        return EstadisticasUsuarios(
            total_usuarios=total_usuarios,
            usuarios_activos=usuarios_activos,
            administradores=administradores,
            usuarios_regulares=usuarios_regulares
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas de usuarios.")

@router.get("/visitas/estadisticas", response_model=EstadisticasVisitas)
async def obtener_estadisticas_visitas(db: Session = Depends(get_db)):
    """
    Endpoint para obtener estadísticas de visitas al sitio.
    """
    try:
        # Total de visitas
        total_visitas = db.query(VisitaModel).count()
        
        # Visitas de hoy
        hoy = datetime.utcnow().date()
        visitas_hoy = db.query(VisitaModel).filter(
            func.date(VisitaModel.fecha_visita) == hoy
        ).count()
        
        # Visitas de esta semana (últimos 7 días)
        hace_una_semana = datetime.utcnow() - timedelta(days=7)
        visitas_esta_semana = db.query(VisitaModel).filter(
            VisitaModel.fecha_visita >= hace_una_semana
        ).count()
        
        # Visitas de este mes (últimos 30 días)
        hace_un_mes = datetime.utcnow() - timedelta(days=30)
        visitas_este_mes = db.query(VisitaModel).filter(
            VisitaModel.fecha_visita >= hace_un_mes
        ).count()
        
        return EstadisticasVisitas(
            total_visitas=total_visitas,
            visitas_hoy=visitas_hoy,
            visitas_esta_semana=visitas_esta_semana,
            visitas_este_mes=visitas_este_mes
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas de visitas.")

@router.post("/registrar-visita", status_code=201)
async def registrar_visita(ip_address: str, user_agent: str = None, pagina_visitada: str = None, usuario_id: int = None, db: Session = Depends(get_db)):
    """
    Endpoint para registrar una nueva visita al sitio.
    """
    try:
        nueva_visita = VisitaModel(
            ip_address=ip_address,
            user_agent=user_agent,
            pagina_visitada=pagina_visitada,
            usuario_id=usuario_id
        )
        
        db.add(nueva_visita)
        db.commit()
        
        return {"message": "Visita registrada exitosamente."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al registrar la visita.")

@router.post("/crear-admin", status_code=201, response_model=UsuarioPublic)
async def crear_administrador(admin: AdminCrear, db: Session = Depends(get_db)):
    """
    Endpoint específico para crear un usuario administrador.
    Este endpoint está separado del endpoint de creación de usuarios regulares
    para mayor seguridad y control.
    """
    try:
        # Verificar si el nombre de usuario ya existe
        if db.query(UsuarioModel).filter(UsuarioModel.usuario == admin.usuario).first():
            raise HTTPException(status_code=400, detail="Este nombre de usuario ya está en uso.")

        # Verificar si el email ya existe
        if db.query(UsuarioModel).filter(UsuarioModel.email == admin.email).first():
            raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado.")

        # Crear el nuevo administrador
        nuevo_admin = UsuarioModel(
            nombre=admin.nombre,
            apellido=admin.apellido,
            email=admin.email,
            usuario=admin.usuario,
            contraseña_hash=obtener_contraseña_hash(admin.contraseña),
            rol="administrador"  # Forzar el rol como administrador
        )

        db.add(nuevo_admin)
        db.commit()
        db.refresh(nuevo_admin)

        # Enviar email de bienvenida específico para administradores
        subject = "¡Bienvenid@ como Administrador!"
        body = f"""
        <html>
        <body>
            <h2>¡Hola, {admin.usuario}!</h2>
            <p>Tu cuenta de <strong>administrador</strong> ha sido creada con éxito.</p>
            <p>Ahora tienes acceso completo a todas las funcionalidades administrativas de la plataforma.</p>
            <p><strong>Responsabilidades del administrador:</strong></p>
            <ul>
                <li>Gestión de usuarios</li>
                <li>Acceso a estadísticas del sistema</li>
                <li>Configuración de la plataforma</li>
            </ul>
            <br>
            <p>Atentamente,</p>
            <p>El Sistema de la Plataforma</p>
        </body>
        </html>
        """
        
        try:
            send_email_smtp([admin.email], subject, body)
        except Exception as email_exc:
            # Si falla el envío del email, no afecta la creación del usuario
            pass 

        return nuevo_admin 
    
    except HTTPException: 
        raise
    except Exception as e: 
        db.rollback() 
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al crear el administrador. Inténtalo más tarde.")


@router.get("/administradores", response_model=list[UsuarioPublic])
async def listar_administradores(db: Session = Depends(get_db)):
    """
    Endpoint para listar todos los usuarios administradores.
    """
    try:
        administradores = db.query(UsuarioModel).filter(
            UsuarioModel.rol == "administrador"
        ).all()
        
        return administradores
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener la lista de administradores.")

@router.delete("/admin/{usuario_id}", status_code=200)
async def eliminar_administrador(usuario_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para eliminar un administrador (cambiar su rol a usuario regular).
    No elimina el usuario, solo cambia su rol.
    """
    try:
        admin = db.query(UsuarioModel).filter(
            UsuarioModel.id == usuario_id,
            UsuarioModel.rol == "administrador"
        ).first()
        
        if not admin:
            raise HTTPException(status_code=404, detail="Administrador no encontrado.")
        
        # Cambiar rol a usuario regular en lugar de eliminar
        admin.rol = "usuario"
        db.commit()
        
        return {"message": f"El usuario {admin.usuario} ya no es administrador."}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud.")
    
    