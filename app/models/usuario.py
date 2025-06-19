from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class UsuarioModel(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    usuario = Column(String(50), unique=True, nullable=False, index=True)
    contraseña_hash = Column(String, nullable=True)  # Hacer nullable para usuarios OAuth
    rol = Column(String(20), nullable=False, default="usuario")
    
    # Campos para OAuth
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', 'discord'
    oauth_id = Column(String(100), nullable=True)  # ID del usuario en el proveedor OAuth
    avatar_url = Column(Text, nullable=True)  # URL del avatar del usuario
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    ventas = relationship("Venta", back_populates="usuario")
    
    # Nuevos campos OAuth
    oauth_provider = Column(String, nullable=True)  # 'google', 'github', 'discord', etc.
    oauth_id = Column(String, nullable=True)  # ID del usuario en el proveedor OAuth
    avatar_url = Column(Text, nullable=True)  # URL del avatar del usuario