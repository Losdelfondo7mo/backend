from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UsuarioModel(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(15), nullable=False)
    apellido = Column(String(15), nullable=False)
    email = Column(String(30), unique=True, nullable=False)
    usuario = Column(String(20), unique=True, nullable=False)
    contraseña_hash = Column(String(60), nullable=False)