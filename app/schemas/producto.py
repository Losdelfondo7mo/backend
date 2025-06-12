from pydantic import BaseModel
from typing import Optional

class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    imagen_url: Optional[str] = None
    categoria: Optional[str] = None

class ProductoCrear(ProductoBase):
    pass

class ProductoMostrar(ProductoBase):
    id: int
    
    class Config:
        orm_mode = True