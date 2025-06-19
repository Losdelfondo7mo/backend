from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Venta(Base):
    """
    Modelo SQLAlchemy que representa la tabla 'ventas' en la base de datos.
    Define la estructura para registrar las ventas realizadas.
    """
    __tablename__ = "ventas"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    fecha_venta = Column(DateTime, default=datetime.utcnow, nullable=False)
    metodo_pago = Column(String(50), nullable=True)
    
    # Relaciones
    producto = relationship("Producto", back_populates="ventas")
    usuario = relationship("UsuarioModel", back_populates="ventas")