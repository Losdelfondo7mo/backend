from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    usuario: str

class UsuarioCrear(UsuarioBase):
    contraseña: str

class UsuarioVerificar(BaseModel):
    usuario: str
    contraseña: str

class Usuario(UsuarioBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    # Eliminar esta clase Config
    # class Config:
    #     orm_mode = True