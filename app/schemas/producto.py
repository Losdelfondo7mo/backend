from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    # correo: Optional[str] = None  # Campo eliminado
    # tipo: Optional[str] = None     # Campo eliminado
    disponibilidad: Optional[bool] = True  # Campo opcional
    categoria_id: Optional[int] = None  # Campo opcional

class ProductoCrear(ProductoBase):
    pass

class ProductoMostrar(ProductoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
 