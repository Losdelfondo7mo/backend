from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

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
    
    model_config = ConfigDict(from_attributes=True)

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