from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, date, timedelta

from app.db.session import get_db
from app.models.pedido import PedidoModel, EstadoPedido
from app.models.detalle_pedido import DetallePedidoModel
from app.models.producto import Producto
from app.models.usuario import UsuarioModel
from app.schemas.pedido import PedidoCrear, PedidoMostrar, EstadisticasPedidos, PedidoConfirmar, DetallePedidoMostrar
from app.core.security import get_current_active_user, get_current_admin_user
from app.services.email_service import send_email_smtp

router = APIRouter()

@router.post("/", response_model=PedidoMostrar, status_code=201)
def crear_pedido(pedido: PedidoCrear, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Registra un nuevo pedido en el sistema como pendiente.
    """
    # Generar número de pedido único
    import random
    import string
    n_pedido = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Calcular monto total
    monto_total = 0
    for detalle in pedido.detalles:
        # Verificar que el producto existe
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {detalle.producto_id} no encontrado"
            )
        
        # Verificar disponibilidad si es necesario
        if hasattr(producto, 'disponibilidad') and not producto.disponibilidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto {producto.nombre} no está disponible"
            )
        
        monto_total += detalle.cantidad * detalle.precio_unitario
    
    # Crear el pedido
    nuevo_pedido = PedidoModel(
        n_pedido=n_pedido,
        usuario_id=current_user.id,
        monto_total=monto_total,
        estado=EstadoPedido.PENDIENTE,
        correo_enviado=False
    )
    
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    
    # Crear los detalles del pedido
    for detalle in pedido.detalles:
        nuevo_detalle = DetallePedidoModel(
            pedido_id=nuevo_pedido.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario
        )
        db.add(nuevo_detalle)
    
    db.commit()
    db.refresh(nuevo_pedido)
    
    return nuevo_pedido

@router.get("/pendientes", response_model=List[PedidoMostrar])
def listar_pedidos_pendientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_admin_user)):
    """
    Lista todos los pedidos pendientes. Solo para administradores.
    """
    pedidos = db.query(PedidoModel).filter(PedidoModel.estado == EstadoPedido.PENDIENTE).offset(skip).limit(limit).all()
    return pedidos

@router.put("/confirmar/{pedido_id}", response_model=PedidoMostrar)
def confirmar_pedido(pedido_id: int, confirmacion: PedidoConfirmar, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_admin_user)):
    """
    Confirma o deniega un pedido. Solo para administradores.
    """
    # Buscar el pedido
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
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
        pedido.estado = EstadoPedido.CONFIRMADO
        pedido.fecha_confirmacion = datetime.utcnow()
        
        # Enviar correo de confirmación
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
        if usuario and usuario.email:
            background_tasks.add_task(
                send_email_smtp,
                email_to=usuario.email,
                subject="Pedido Confirmado",
                html_content=f"<p>Su pedido #{pedido.n_pedido} ha sido confirmado.</p>"
            )
            pedido.correo_enviado = True
    else:
        # Denegar pedido
        pedido.estado = EstadoPedido.DENEGADO
        
        # Enviar correo de denegación
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
        if usuario and usuario.email:
            background_tasks.add_task(
                send_email_smtp,
                email_to=usuario.email,
                subject="Pedido Denegado",
                html_content=f"<p>Lo sentimos, su pedido #{pedido.n_pedido} ha sido denegado.</p>"
            )
            pedido.correo_enviado = True
    
    db.commit()
    db.refresh(pedido)
    return pedido

@router.get("/mis-pedidos", response_model=List[PedidoMostrar])
def mis_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Lista todos los pedidos del usuario actual.
    """
    pedidos = db.query(PedidoModel).filter(PedidoModel.usuario_id == current_user.id).offset(skip).limit(limit).all()
    return pedidos

@router.get("/estadisticas", response_model=EstadisticasPedidos)
def estadisticas_pedidos(db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_admin_user)):
    """
    Obtiene estadísticas de pedidos. Solo para administradores.
    """
    # Total de pedidos
    total_pedidos = db.query(func.count(PedidoModel.id)).scalar()
    
    # Ingresos totales
    ingresos_totales = db.query(func.sum(PedidoModel.monto_total)).filter(
        PedidoModel.estado == EstadoPedido.CONFIRMADO
    ).scalar() or 0
    
    # Pedido promedio
    pedido_promedio = db.query(func.avg(PedidoModel.monto_total)).filter(
        PedidoModel.estado == EstadoPedido.CONFIRMADO
    ).scalar() or 0
    
    # Producto más vendido
    subquery = db.query(
        DetallePedidoModel.producto_id,
        func.sum(DetallePedidoModel.cantidad).label('total_vendido')
    ).join(
        PedidoModel, PedidoModel.id == DetallePedidoModel.pedido_id
    ).filter(
        PedidoModel.estado == EstadoPedido.CONFIRMADO
    ).group_by(
        DetallePedidoModel.producto_id
    ).subquery()
    
    producto_mas_vendido_id = db.query(subquery.c.producto_id).order_by(
        desc(subquery.c.total_vendido)
    ).first()
    
    producto_mas_vendido = None
    if producto_mas_vendido_id:
        producto = db.query(Producto).filter(Producto.id == producto_mas_vendido_id[0]).first()
        if producto:
            producto_mas_vendido = producto.nombre
    
    # Pedidos de hoy
    hoy = date.today()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    fin_dia = datetime.combine(hoy, datetime.max.time())
    
    pedidos_hoy = db.query(func.count(PedidoModel.id)).filter(
        PedidoModel.fecha >= inicio_dia,
        PedidoModel.fecha <= fin_dia
    ).scalar()
    
    ingresos_hoy = db.query(func.sum(PedidoModel.monto_total)).filter(
        PedidoModel.fecha >= inicio_dia,
        PedidoModel.fecha <= fin_dia,
        PedidoModel.estado == EstadoPedido.CONFIRMADO
    ).scalar() or 0
    
    return EstadisticasPedidos(
        total_pedidos=total_pedidos,
        ingresos_totales=ingresos_totales,
        pedido_promedio=pedido_promedio,
        producto_mas_vendido=producto_mas_vendido,
        pedidos_hoy=pedidos_hoy,
        ingresos_hoy=ingresos_hoy
    )