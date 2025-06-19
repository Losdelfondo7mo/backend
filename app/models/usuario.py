from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class UsuarioModel(Base):
    """
    Modelo SQLAlchemy que representa la tabla 'usuarios' en la base de datos.
    Almacena la información de los usuarios registrados en el sistema.
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    usuario = Column(String(50), unique=True, nullable=False, index=True)
    contraseña_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="usuario")
    
    ventas = relationship("Venta", back_populates="usuario")