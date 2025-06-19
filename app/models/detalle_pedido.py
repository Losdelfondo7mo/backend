from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class DetallePedidoModel(Base):
    __tablename__ = "detalles_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    
    # Relaciones
    pedido = relationship("PedidoModel", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_pedido")