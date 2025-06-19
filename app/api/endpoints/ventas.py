from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, date

from app.db.session import get_db
from app.models.venta import Venta
from app.models.producto import Producto
from app.models.usuario import UsuarioModel
from app.schemas.venta import VentaCrear, VentaMostrar, EstadisticasVentas
from app.core.security import get_current_active_user

router = APIRouter()

@router.post("/", response_model=VentaMostrar, status_code=201)
def registrar_venta(venta: VentaCrear, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Registra una nueva venta en el sistema.
    """
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.id == venta.producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Verificar stock disponible
    if producto.stock < venta.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Disponible: {producto.stock}"
        )
    
    # Calcular total
    total = venta.cantidad * venta.precio_unitario
    
    # Crear la venta
    nueva_venta = Venta(
        producto_id=venta.producto_id,
        usuario_id=current_user.id,
        cantidad=venta.cantidad,
        precio_unitario=venta.precio_unitario,
        total=total,
        metodo_pago=venta.metodo_pago
    )
    
    # Actualizar stock del producto
    producto.stock -= venta.cantidad
    
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)
    
    return nueva_venta

@router.get("/", response_model=List[VentaMostrar])
def listar_ventas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Lista todas las ventas registradas.
    """
    ventas = db.query(Venta).offset(skip).limit(limit).all()
    return ventas

@router.get("/mis-ventas", response_model=List[VentaMostrar])
def listar_mis_ventas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Lista las ventas realizadas por el usuario actual.
    """
    ventas = db.query(Venta).filter(Venta.usuario_id == current_user.id).offset(skip).limit(limit).all()
    return ventas

@router.get("/estadisticas", response_model=EstadisticasVentas)
def obtener_estadisticas_ventas(db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Obtiene estadísticas generales de ventas.
    """
    # Total de ventas
    total_ventas = db.query(Venta).count()
    
    # Ingresos totales
    ingresos_totales = db.query(func.sum(Venta.total)).scalar() or 0.0
    
    # Venta promedio
    venta_promedio = ingresos_totales / total_ventas if total_ventas > 0 else 0.0
    
    # Producto más vendido
    producto_mas_vendido_query = (
        db.query(Producto.nombre, func.sum(Venta.cantidad).label('total_vendido'))
        .join(Venta)
        .group_by(Producto.id, Producto.nombre)
        .order_by(desc('total_vendido'))
        .first()
    )
    producto_mas_vendido = producto_mas_vendido_query[0] if producto_mas_vendido_query else None
    
    # Ventas de hoy
    hoy = date.today()
    ventas_hoy = db.query(Venta).filter(func.date(Venta.fecha_venta) == hoy).count()
    
    # Ingresos de hoy
    ingresos_hoy = (
        db.query(func.sum(Venta.total))
        .filter(func.date(Venta.fecha_venta) == hoy)
        .scalar() or 0.0
    )
    
    return EstadisticasVentas(
        total_ventas=total_ventas,
        ingresos_totales=ingresos_totales,
        venta_promedio=venta_promedio,
        producto_mas_vendido=producto_mas_vendido,
        ventas_hoy=ventas_hoy,
        ingresos_hoy=ingresos_hoy
    )

@router.get("/ingresos-por-periodo")
def obtener_ingresos_por_periodo(fecha_inicio: str, fecha_fin: str, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Obtiene los ingresos en un período específico.
    Formato de fechas: YYYY-MM-DD
    """
    try:
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    
    ingresos = (
        db.query(func.sum(Venta.total))
        .filter(func.date(Venta.fecha_venta) >= inicio)
        .filter(func.date(Venta.fecha_venta) <= fin)
        .scalar() or 0.0
    )
    
    ventas_count = (
        db.query(func.count(Venta.id))
        .filter(func.date(Venta.fecha_venta) >= inicio)
        .filter(func.date(Venta.fecha_venta) <= fin)
        .scalar() or 0
    )
    
    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ingresos_totales": ingresos,
        "total_ventas": ventas_count,
        "promedio_por_venta": ingresos / ventas_count if ventas_count > 0 else 0.0
    }