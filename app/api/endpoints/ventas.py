from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, date, timedelta
import asyncio

from app.db.session import get_db
from app.models.venta import Venta, EstadoPedido
from app.models.producto import Producto
from app.models.usuario import UsuarioModel
from app.schemas.venta import VentaCrear, VentaMostrar, EstadisticasVentas, PedidoConfirmar
from app.core.security import get_current_active_user
from app.services.email_service import send_email_smtp

router = APIRouter()

@router.post("/", response_model=VentaMostrar, status_code=201)
def registrar_venta(venta: VentaCrear, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Registra una nueva venta en el sistema como pedido pendiente.
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
    
    # Crear la venta como pedido pendiente
    nueva_venta = Venta(
        producto_id=venta.producto_id,
        usuario_id=current_user.id,
        cantidad=venta.cantidad,
        precio_unitario=venta.precio_unitario,
        total=total,
        metodo_pago=venta.metodo_pago,
        estado=EstadoPedido.PENDIENTE
    )
    
    # NO actualizar stock hasta que se confirme
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)
    
    return nueva_venta

@router.get("/pedidos-pendientes", response_model=List[VentaMostrar])
def listar_pedidos_pendientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Lista todos los pedidos pendientes. Solo para administradores.
    """
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver pedidos pendientes"
        )
    
    pedidos = db.query(Venta).filter(Venta.estado == EstadoPedido.PENDIENTE).offset(skip).limit(limit).all()
    return pedidos

@router.put("/confirmar-pedido/{pedido_id}", response_model=VentaMostrar)
def confirmar_pedido(pedido_id: int, confirmacion: PedidoConfirmar, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Confirma o deniega un pedido. Solo para administradores.
    """
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden confirmar pedidos"
        )
    
    # Buscar el pedido
    pedido = db.query(Venta).filter(Venta.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    if pedido.estado != EstadoPedido.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pedido ya ha sido procesado"
        )
    
    if confirmacion.confirmar:
        # Confirmar pedido
        producto = db.query(Producto).filter(Producto.id == pedido.producto_id).first()
        
        # Verificar stock nuevamente
        if producto.stock < pedido.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {producto.stock}"
            )
        
        # Actualizar stock y estado
        producto.stock -= pedido.cantidad
        pedido.estado = EstadoPedido.CONFIRMADO
        pedido.fecha_confirmacion = datetime.utcnow()
        
        # Enviar email de confirmación
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
        if usuario and usuario.email:
            background_tasks.add_task(
                enviar_email_confirmacion,
                usuario.email,
                usuario.nombre,
                producto.nombre,
                pedido.cantidad,
                pedido.total
            )
        
        # Programar entrega automática después de 10 segundos
        background_tasks.add_task(marcar_como_entregado, pedido_id, db)
        
    else:
        # Denegar pedido
        pedido.estado = EstadoPedido.DENEGADO
        pedido.fecha_confirmacion = datetime.utcnow()
    
    db.commit()
    db.refresh(pedido)
    
    return pedido

async def marcar_como_entregado(pedido_id: int, db: Session):
    """
    Marca un pedido como entregado después de 10 segundos.
    """
    await asyncio.sleep(10)
    
    pedido = db.query(Venta).filter(Venta.id == pedido_id).first()
    if pedido and pedido.estado == EstadoPedido.CONFIRMADO:
        pedido.estado = EstadoPedido.ENTREGADO
        pedido.fecha_entrega = datetime.utcnow()
        db.commit()

def enviar_email_confirmacion(email: str, nombre: str, producto: str, cantidad: int, total: float):
    """
    Envía email de confirmación de compra.
    """
    asunto = "¡Compra confirmada exitosamente!"
    mensaje = f"""
    Hola {nombre},
    
    Tu compra ha sido confirmada exitosamente:
    
    Producto: {producto}
    Cantidad: {cantidad}
    Total: ${total:.2f}
    
    Tu pedido será entregado en breve.
    
    ¡Gracias por tu compra!
    """
    
    try:
        send_email_smtp(email, asunto, mensaje)
    except Exception as e:
        print(f"Error enviando email: {e}")

@router.get("/mis-pedidos", response_model=List[VentaMostrar])
def listar_mis_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Lista los pedidos del usuario actual con todos los estados.
    """
    pedidos = db.query(Venta).filter(Venta.usuario_id == current_user.id).offset(skip).limit(limit).all()
    return pedidos

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
    Obtiene estadísticas generales de ventas confirmadas.
    """
    # Solo contar ventas confirmadas y entregadas
    total_ventas = db.query(Venta).filter(Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO])).count()
    
    # Ingresos totales solo de ventas confirmadas
    ingresos_totales = db.query(func.sum(Venta.total)).filter(Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO])).scalar() or 0.0
    
    # Venta promedio
    venta_promedio = ingresos_totales / total_ventas if total_ventas > 0 else 0.0
    
    # Producto más vendido
    producto_mas_vendido_query = (
        db.query(Producto.nombre, func.sum(Venta.cantidad).label('total_vendido'))
        .join(Venta)
        .filter(Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO]))
        .group_by(Producto.id, Producto.nombre)
        .order_by(desc('total_vendido'))
        .first()
    )
    producto_mas_vendido = producto_mas_vendido_query[0] if producto_mas_vendido_query else None
    
    # Ventas de hoy
    hoy = date.today()
    ventas_hoy = db.query(Venta).filter(
        func.date(Venta.fecha_venta) == hoy,
        Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO])
    ).count()
    
    # Ingresos de hoy
    ingresos_hoy = (
        db.query(func.sum(Venta.total))
        .filter(
            func.date(Venta.fecha_venta) == hoy,
            Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO])
        )
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
        .filter(
            func.date(Venta.fecha_venta) >= inicio,
            func.date(Venta.fecha_venta) <= fin,
            Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO])
        )
        .scalar() or 0.0
    )
    
    ventas_count = (
        db.query(func.count(Venta.id))
        .filter(
            func.date(Venta.fecha_venta) >= inicio,
            func.date(Venta.fecha_venta) <= fin,
            Venta.estado.in_([EstadoPedido.CONFIRMADO, EstadoPedido.ENTREGADO])
        )
        .scalar() or 0
    )
    
    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ingresos_totales": ingresos,
        "total_ventas": ventas_count,
        "promedio_por_venta": ingresos / ventas_count if ventas_count > 0 else 0.0
    }