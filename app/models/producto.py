from sqlalchemy import Column, Integer, String, Float, Text
from app.db.base import Base # Importa la clase Base para la declaración de modelos.

class Producto(Base):
    """
    Modelo SQLAlchemy que representa la tabla 'productos' en la base de datos.
    Define la estructura y los tipos de datos para la información de los productos.
    """
    __tablename__ = "productos" # Nombre de la tabla en la base de datos.
    
    id = Column(Integer, primary_key=True, index=True) # Identificador único para cada producto, indexado para búsquedas rápidas.
    nombre = Column(String(100), nullable=False) # Nombre del producto, no puede ser nulo. Ajustado a 100 caracteres.
    descripcion = Column(Text, nullable=True) # Descripción detallada del producto, puede ser nula.
    precio = Column(Float, nullable=False) # Precio del producto, no puede ser nulo.
    stock = Column(Integer, nullable=False) # Cantidad disponible en inventario, no puede ser nula.
    imagen_url = Column(String(255), nullable=True) # URL de la imagen del producto, puede ser nula.
    categoria = Column(String(50), nullable=True) # Categoría a la que pertenece el producto, puede ser nula. Ajustado a 50 caracteres.