from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

Base = declarative_base()

# --- Modelos SQLAlchemy (Base de datos) ---
class UsuarioModel(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(15), nullable=False)
    apellido = Column(String(15), nullable=False)
    email = Column(String(30), unique=True, nullable=False)
    usuario = Column(String(20), unique=True, nullable=False)
    contraseña_hash = Column(String(50), nullable=False)

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(25), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    imagen_url = Column(String(255))
    categoria = Column(String(10))

# --- Modelos Pydantic (Validación y serialización) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    password: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str
    model_config = ConfigDict(from_attributes=True)

class UsuarioCrear(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    usuario: str
    contraseña: str

class UsuarioVerificar(BaseModel):
    usuario: str

class ProductoCrear(BaseModel):
    nombre: str
    descripcion: str | None = None
    precio: float
    stock: int
    imagen_url: str | None = None
    categoria: str | None = None

class ProductoMostrar(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    precio: float
    stock: int
    imagen_url: str | None
    categoria: str | None

    model_config = ConfigDict(from_attributes=True)
    class Config:
        orm_mode = True