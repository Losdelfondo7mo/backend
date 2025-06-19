from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    DENEGADO = "denegado"
    ENTREGADO = "entregado"

class DetallePedidoBase(BaseModel):
    cantidad: int
    precio_unitario: float
    producto_id: int

class DetallePedidoCrear(DetallePedidoBase):
    pass

class DetallePedidoMostrar(DetallePedidoBase):
    id: int
    pedido_id: int
    
    model_config = ConfigDict(from_attributes=True)

class PedidoBase(BaseModel):
    n_pedido: str
    usuario_id: int

class PedidoCrear(PedidoBase):
    detalles: List[DetallePedidoCrear]

class PedidoMostrar(PedidoBase):
    id: int
    estado: EstadoPedido
    fecha: datetime
    monto_total: float
    correo_enviado: bool
    detalles: List[DetallePedidoMostrar] = []
    
    model_config = ConfigDict(from_attributes=True)

class PedidoConfirmar(BaseModel):
    confirmar: bool  # True para confirmar, False para denegar
    
class EstadisticasPedidos(BaseModel):
    total_pedidos: int
    ingresos_totales: float
    pedido_promedio: float
    producto_mas_vendido: Optional[str] = None
    pedidos_hoy: int
    ingresos_hoy: float