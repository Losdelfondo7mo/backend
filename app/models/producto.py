from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Producto(Base):
    """
    Modelo SQLAlchemy que representa la tabla 'productos' en la base de datos.
    Define la estructura y los tipos de datos para la información de los productos.
    """
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    imagen_url = Column(String(255), nullable=True)
    categoria = Column(String(50), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=True)
    
    # Relación con ventas
    ventas = relationship("Venta", back_populates="producto")