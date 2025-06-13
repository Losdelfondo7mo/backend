from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductoBase(BaseModel):
    nombre: str
    descripcion: str | None = None
    precio: float
    stock: int
    imagen_url: str | None = None
    categoria: str | None = None

class ProductoCrear(ProductoBase):
    pass

class ProductoMostrar(ProductoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    # Eliminar esta clase Config
    # class Config:
    #     orm_mode = True