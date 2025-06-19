from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    DENEGADO = "denegado"
    ENTREGADO = "entregado"

class VentaBase(BaseModel):
    """
    Esquema base para una venta.
    """
    producto_id: int
    cantidad: int
    precio_unitario: float
    metodo_pago: Optional[str] = None

class VentaCrear(VentaBase):
    """
    Esquema para crear una nueva venta.
    """
    pass

class VentaMostrar(VentaBase):
    """
    Esquema para mostrar información de una venta.
    """
    id: int
    usuario_id: int
    total: float
    fecha_venta: datetime
    estado: EstadoPedido
    fecha_confirmacion: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class PedidoConfirmar(BaseModel):
    """
    Esquema para confirmar o denegar un pedido.
    """
    confirmar: bool  # True para confirmar, False para denegar
    
class EstadisticasVentas(BaseModel):
    """
    Esquema para mostrar estadísticas de ventas.
    """
    total_ventas: int
    ingresos_totales: float
    venta_promedio: float
    producto_mas_vendido: Optional[str] = None
    ventas_hoy: int
    ingresos_hoy: float