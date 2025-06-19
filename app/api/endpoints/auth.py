from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.usuario import UsuarioModel
from app.core.security import verify_password, create_access_token
from app.services.oauth_service import oauth_service
from app.schemas.oauth import OAuthCallback, OAuthLoginResponse, OAuthProvider
from typing import List
import secrets

router = APIRouter()

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
    return {"access_token": access_token, "token_type": "bearer"}

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

