from pydantic import BaseModel, ConfigDict
from typing import Optional # Para campos opcionales.

class ProductoBase(BaseModel):
    """
    Esquema base para un producto. Contiene los campos comunes
    que se utilizan tanto para la creación como para la visualización de productos.
    """
    nombre: str
    descripcion: Optional[str] = None # La descripción es opcional.
    precio: float
    stock: int
    imagen_url: Optional[str] = None # La URL de la imagen es opcional.
    categoria: Optional[str] = None # La categoría es opcional.

class ProductoCrear(ProductoBase):
    """
    Esquema utilizado para crear un nuevo producto.
    Hereda todos los campos de `ProductoBase`.
    No añade campos adicionales, pero se define para claridad semántica.
    """
    pass # No se necesitan campos adicionales para la creación más allá de los base.

class ProductoMostrar(ProductoBase):
    """
    Esquema utilizado para mostrar la información de un producto.
    Hereda de `ProductoBase` y añade el `id` del producto, que se genera
    en la base de datos.
    """
    id: int # El ID del producto, asignado por la base de datos.
    
    # Configuración para Pydantic v2. 'from_attributes=True' permite que el modelo
    # se cree a partir de atributos de un objeto ORM (modo ORM).
    model_config = ConfigDict(from_attributes=True)
    # Eliminar esta clase Config
    # class Config:
    #     orm_mode = True