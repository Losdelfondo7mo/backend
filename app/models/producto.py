from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    correo = Column(String(100), nullable=True)
    tipo = Column(String(50), nullable=True)
    disponibilidad = Column(Boolean, default=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    # Se eliminó imagen_url ya que no existe en la base de datos
    # Se eliminó fecha ya que no existe en la base de datos
    
    # Relaciones
    categoria = relationship("CategoriaModel", back_populates="productos")
    detalles_pedido = relationship("DetallePedidoModel", back_populates="producto")
    # Se eliminó la columna categoria duplicada
    # Se eliminó la relación con ventas