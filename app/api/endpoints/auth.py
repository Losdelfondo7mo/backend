from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.models.usuario import UsuarioModel
from app.core.security import verificar_contraseña, create_access_token
from app.schemas.token import Token
from app.config.settings import settings
from models import UsuarioLogin

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

