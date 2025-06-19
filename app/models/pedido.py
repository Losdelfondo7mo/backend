from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum

class EstadoPedido(enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    DENEGADO = "denegado"
    ENTREGADO = "entregado"

class PedidoModel(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    n_pedido = Column(String(20), unique=True, nullable=False)  # Número de pedido
    estado = Column(Enum(EstadoPedido), default=EstadoPedido.PENDIENTE, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    monto_total = Column(Float, nullable=False)
    correo_enviado = Column(Boolean, default=False)  # Nuevo campo
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relaciones
    usuario = relationship("UsuarioModel", back_populates="pedidos")
    detalles = relationship("DetallePedidoModel", back_populates="pedido")