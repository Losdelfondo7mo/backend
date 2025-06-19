from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    correo: Optional[str] = None  # Nuevo campo
    tipo: Optional[str] = None     # Nuevo campo
    disponibilidad: Optional[bool] = True  # Nuevo campo
    categoria_id: int

class ProductoCrear(ProductoBase):
    pass

class ProductoMostrar(ProductoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    # Eliminar esta clase Config
    # class Config:
    #     orm_mode = True