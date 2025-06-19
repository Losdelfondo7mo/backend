from fastapi import APIRouter, HTTPException, Depends, status, Form, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, Dict, Any
from pydantic import ValidationError
from app.db.session import get_db
from app.models.usuario import UsuarioModel
from app.core.security import verificar_contraseña, create_access_token, obtener_contraseña_hash
from app.services.oauth_service import oauth_service
from app.services.email_service import send_email_smtp
from app.schemas.oauth import OAuthCallback, OAuthLoginResponse, OAuthProvider
from app.schemas.token import Token
from app.schemas.usuario import UsuarioLogin, UsuarioCrear, UsuarioPublic
from app.config.settings import settings
from typing import List
import secrets

router = APIRouter()
@router.post("/register", status_code=201, response_model=UsuarioPublic)
async def register_user(
    request: Request,
    db: Session = Depends(get_db),
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None)
):
    """
    Endpoint flexible que acepta tanto datos JSON como formulario.
    """
    try:
        # Intentar obtener datos del cuerpo JSON si no se proporcionaron en el formulario
        if username is None and email is None and password is None:
            # Si no hay datos de formulario, intentamos leer JSON
            json_data = await request.json()
            
            # Mapear campos JSON a los nombres esperados por UsuarioCrear
            usuario_data = {
                "usuario": json_data.get("username") or json_data.get("usuario"),
                "email": json_data.get("email"),
                "contraseña": json_data.get("password") or json_data.get("contraseña"),
                "nombre": json_data.get("first_name") or json_data.get("nombre"),
                "apellido": json_data.get("last_name") or json_data.get("apellido")
            }
        else:
            # Si hay datos de formulario, los usamos
            usuario_data = {
                "usuario": username,
                "email": email,
                "contraseña": password,
                "nombre": first_name,
                "apellido": last_name
            }
        
        # Validar que los campos requeridos estén presentes
        if not usuario_data["usuario"] or not usuario_data["email"] or not usuario_data["contraseña"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Se requieren los campos username/usuario, email y password/contraseña"
            )
        
        # Crear objeto UsuarioCrear
        try:
            usuario = UsuarioCrear(**usuario_data)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        # Lógica de creación de usuario (copiada de crear_usuario)
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
    
    except HTTPException: 
        raise
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud: {str(e)}"
        )

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

@router.post("/login", response_model=Token)
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
        "rol": usuario_db.rol,  # Añadido para que el frontend lo reciba
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

@router.post("/oauth/{provider}/callback", response_model=OAuthLoginResponse)
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    db: Session = Depends(get_db)
):
    """Manejar callback OAuth y autenticar/crear usuario"""
    try:
        # Intercambiar código por token
        token_data = await oauth_service.exchange_code_for_token(provider, callback_data.code)
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
                # Actualizar usuario existente con información OAuth
                existing_user.oauth_provider = provider
                existing_user.oauth_id = user_info['id']
                existing_user.avatar_url = user_info.get('avatar_url')
                db.commit()
                is_new_user = False
            else:
                # Crear nuevo usuario
                new_user = UsuarioModel(
                    nombre_usuario=user_info['name'],
                    email=user_info['email'],
                    oauth_provider=provider,
                    oauth_id=user_info['id'],
                    avatar_url=user_info.get('avatar_url'),
                    es_activo=True,
                    es_admin=False
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
        jwt_token = create_access_token(data={"sub": existing_user.nombre_usuario})
        
        return OAuthLoginResponse(
            access_token=jwt_token,
            user_id=existing_user.id,
            username=existing_user.nombre_usuario,
            email=existing_user.email,
            is_new_user=is_new_user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en autenticación OAuth: {str(e)}"
        )

