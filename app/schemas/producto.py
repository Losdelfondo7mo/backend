from pydantic import BaseModel, ConfigDict
from typing import Optional, List
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
    categoria: str  # Nuevo campo para recibir el nombre de la categoría

class ProductoMostrar(ProductoBase):
    id: int
    categoria: Optional[str] = None  # Añadimos el campo para mostrar el nombre de la categoría
    
    model_config = ConfigDict(from_attributes=True)

class ProductoItem(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int

class ProductoPedidoCrear(BaseModel):
    usuario: str
    productos: List[ProductoItem]
    total: float
 