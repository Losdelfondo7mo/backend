from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    DENEGADO = "denegado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

class ProductoItem(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int

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

# Modificamos PedidoCrear para aceptar una lista de productos
class PedidoCrear(BaseModel):
    productos: List[ProductoItem]
    total: Optional[float] = None
    usuario_id: Optional[int] = None

# Esquema para editar pedidos
class PedidoEditar(BaseModel):
    # Datos del producto
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    disponibilidad: Optional[bool] = None
    nombre: Optional[str] = None
    precio: Optional[float] = None
    cantidad: Optional[int] = None

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
