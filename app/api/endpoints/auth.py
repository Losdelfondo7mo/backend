from fastapi import APIRouter, HTTPException, Depends, status, Form, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, Dict, Any
from pydantic import ValidationError
from app.db.session import get_db
from app.models.usuario import UsuarioModel
from app.core.security import verificar_contraseña, create_access_token, obtener_contraseña_hash, get_current_user
from app.services.oauth_service import oauth_service
from app.services.email_service import send_email_smtp
from app.schemas.oauth import OAuthCallback, OAuthLoginResponse, OAuthProvider
from app.schemas.token import Token, TokenWithUserData
from app.schemas.usuario import UsuarioLogin, UsuarioCrear, UsuarioPublic
from app.config.settings import settings
from typing import List
import secrets
from fastapi.responses import RedirectResponse
from app.core.security import obtener_contraseña_hash
from app.schemas.usuario import UsuarioMostrar

router = APIRouter()
@router.post("/crear", status_code=201, response_model=UsuarioPublic)
async def crear_usuario(
    usuario: UsuarioCrear,
    db: Session = Depends(get_db)
):
    """
    Endpoint que acepta solo datos en formato JSON
    """
    # Lógica de creación de usuario
    if db.query(UsuarioModel).filter(UsuarioModel.usuario == usuario.usuario).first():
        raise HTTPException(status_code=400, detail="Este nombre de usuario ya está en uso.")

    if db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado.")

    nuevo_usuario = UsuarioModel(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        usuario=usuario.usuario,
        contraseña_hash=obtener_contraseña_hash(usuario.contraseña),
        rol="usuario"  # Forzar rol como 'usuario' para mayor seguridad
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

@router.post("/login", response_model=TokenWithUserData)
async def login_for_access_token(login_data: UsuarioLogin, db: Session = Depends(get_db)):
    usuario_db = db.query(UsuarioModel).filter(UsuarioModel.usuario == login_data.usuario).first()
    
    if not usuario_db or not verificar_contraseña(login_data.contraseña, usuario_db.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario_db.usuario}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario_db.usuario,
        "rol": usuario_db.rol,
        "email": usuario_db.email,
        "nombre": usuario_db.nombre,
        "apellido": usuario_db.apellido,
        "id": usuario_db.id
    }

@router.post("/token", response_model=Token)
async def login_oauth(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario_db = db.query(UsuarioModel).filter(UsuarioModel.usuario == form_data.username).first()
    
    if not usuario_db or not verificar_contraseña(form_data.password, usuario_db.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario_db.usuario}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "usuario": usuario_db.usuario  # Añadido para que el frontend lo reciba
    }

@router.get("/oauth/providers", response_model=List[OAuthProvider])
async def get_oauth_providers():
    """Obtener lista de proveedores OAuth disponibles"""
    providers = [
        OAuthProvider(
            name="google",
            display_name="Google",
            authorization_url=oauth_service.get_authorization_url("google")
        ),
        OAuthProvider(
            name="github",
            display_name="GitHub",
            authorization_url=oauth_service.get_authorization_url("github")
        ),
        OAuthProvider(
            name="discord",
            display_name="Discord",
            authorization_url=oauth_service.get_authorization_url("discord")
        )
    ]
    return providers

@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str):
    """Iniciar flujo OAuth para el proveedor especificado"""
    try:
        authorization_url = oauth_service.get_authorization_url(provider)
        return {"authorization_url": authorization_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/oauth/{provider}/callback", response_class=RedirectResponse)
async def oauth_callback(
    provider: str,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Manejar callback OAuth y autenticar/crear usuario"""
    import logging
    logging.info(f"OAuth callback recibido: provider={provider}, code={code[:10]}...")
    try:
        # Intercambiar código por token
        token_data = await oauth_service.exchange_code_for_token(provider, code)
        access_token = token_data['access_token']
        
        # Obtener información del usuario
        user_info = await oauth_service.get_user_info(provider, access_token)
        
        # Buscar usuario existente por OAuth ID o email
        existing_user = db.query(UsuarioModel).filter(
            (UsuarioModel.oauth_provider == provider) & 
            (UsuarioModel.oauth_id == user_info['id'])
        ).first()
        
        if not existing_user:
            # Buscar por email si no existe por OAuth ID
            existing_user = db.query(UsuarioModel).filter(
                UsuarioModel.email == user_info['email']
            ).first()
            
            if existing_user:
                # Si existe usuario con el mismo email pero sin OAuth
                if not existing_user.oauth_provider:
                    # Redirigir a página de vinculación
                    redirect_url = f"https://los-del-fondo-7mo.web.app/auth/link-account?email={user_info['email']}&provider={provider}"
                    return RedirectResponse(url=redirect_url)
                else:
                    # Actualizar información OAuth
                    existing_user.oauth_provider = provider
                    existing_user.oauth_id = user_info['id']
                    existing_user.avatar_url = user_info.get('avatar_url')
                    db.commit()
                    is_new_user = False
            else:
                # Crear nuevo usuario
                new_user = UsuarioModel(
                    nombre=user_info['name'],
                    apellido="",
                    usuario=user_info['email'].split('@')[0],
                    email=user_info['email'],
                    oauth_provider=provider,
                    oauth_id=user_info['id'],
                    avatar_url=user_info.get('avatar_url'),
                    is_active=True,
                    rol="usuario"
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                existing_user = new_user
                is_new_user = True
        else:
            # Actualizar avatar si cambió
            if user_info.get('avatar_url') != existing_user.avatar_url:
                existing_user.avatar_url = user_info.get('avatar_url')
                db.commit()
            is_new_user = False
        
        # Crear token JWT
        jwt_token = create_access_token(data={"sub": existing_user.usuario})
        
        # Redireccionar al frontend con el token como parámetro
        redirect_url = f"https://los-del-fondo-7mo.web.app/productos?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logging.error(f"Error en OAuth callback: {str(e)}")
        # Redireccionar a la página de error en el frontend
        return RedirectResponse(url=f"https://los-del-fondo-7mo.web.app/error-login?error={str(e)}")


@router.post("/perfil", response_model=TokenWithUserData)
async def login_with_user_data(login_data: UsuarioLogin, db: Session = Depends(get_db)):
    """
    Endpoint para iniciar sesión y obtener un token JWT junto con los datos del usuario.
    Devuelve el token de acceso, tipo de token, y datos básicos del usuario sin información sensible.
    """
    usuario_db = db.query(UsuarioModel).filter(UsuarioModel.usuario == login_data.usuario).first()
    
    if not usuario_db or not verificar_contraseña(login_data.contraseña, usuario_db.contraseña_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario_db.usuario}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario_db.usuario,
        "rol": usuario_db.rol,
        "email": usuario_db.email,
        "nombre": usuario_db.nombre,
        "apellido": usuario_db.apellido,
        "id": usuario_db.id
    }

@router.get("/me", response_model=UsuarioPublic)
async def get_current_user_info(current_user: UsuarioModel = Depends(get_current_user)):
    """Obtener información del usuario actual autenticado"""
    return current_user


@router.post("/link-oauth")
async def link_oauth_account(
    link_data: dict,
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vincular cuenta OAuth con cuenta existente"""
    try:
        provider = link_data.get('provider')
        if not provider:
            raise HTTPException(status_code=400, detail="Provider requerido")
        
        # Actualizar usuario con información OAuth
        current_user.oauth_provider = provider
        # Nota: oauth_id se actualizará en el próximo login OAuth
        db.commit()
        
        return {"message": "Cuenta vinculada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al vincular cuenta: {str(e)}")


@router.post("/create-password-oauth")
async def create_password_oauth(
    password_data: dict,
    db: Session = Depends(get_db)
):
    """Crear contraseña para usuario OAuth existente"""
    try:
        email = password_data.get('email')
        password = password_data.get('password')
        provider = password_data.get('provider')
        
        if not all([email, password, provider]):
            raise HTTPException(status_code=400, detail="Email, password y provider requeridos")
        
        # Buscar usuario por email
        user = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Actualizar contraseña
        user.contraseña = obtener_contraseña_hash(password)
        user.oauth_provider = provider
        db.commit()
        
        # Crear token JWT
        jwt_token = create_access_token(data={"sub": user.usuario})
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "message": "Contraseña creada exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear contraseña: {str(e)}")
from app.core.security import get_password_hash
from app.schemas.usuario import UsuarioMostrar

