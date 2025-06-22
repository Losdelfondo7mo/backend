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
from app.models.categoria import CategoriaModel
from app.schemas.pedido import PedidoCrear, PedidoMostrar, EstadisticasPedidos, PedidoConfirmar, DetallePedidoMostrar
# Comentamos las importaciones de autenticación que no vamos a usar
# from app.core.security import get_current_active_user, get_current_admin_user
from app.services.email_service import send_email_smtp

router = APIRouter()

@router.post("/", response_model=PedidoMostrar, status_code=201)
def crear_pedido(pedido: PedidoCrear, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Registra un nuevo pedido en el sistema como pendiente.
    Acepta directamente los datos del producto (nombre, precio, categoría, etc.)
    """
    # Generar número de pedido único
    import random
    import string
    n_pedido = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Verificar si el usuario existe, si no, crear un usuario anónimo
    usuario = None
    if pedido.usuario_id:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
    
    if not usuario:
        # Crear un usuario anónimo
        usuario = UsuarioModel(
            nombre="Anónimo",
            apellido="Anónimo",
            email=f"anonimo_{n_pedido}@example.com",  # Email único
            usuario=f"anonimo_{n_pedido}",  # Usuario único
            rol="usuario"
        )
        db.add(usuario)
        db.flush()  # Esto asigna un ID al usuario sin hacer commit
    
    # Buscar o crear la categoría
    categoria = None
    if pedido.categoria:
        categoria = db.query(CategoriaModel).filter(CategoriaModel.nombre == pedido.categoria).first()
        if not categoria:
            categoria = CategoriaModel(nombre=pedido.categoria)
            db.add(categoria)
            db.flush()
    else:
        # Si no se proporciona categoría, usar una por defecto
        categoria = db.query(CategoriaModel).first()
        if not categoria:
            categoria = CategoriaModel(nombre="General")
            db.add(categoria)
            db.flush()
    
    # Buscar si el producto ya existe o crear uno nuevo
    producto = db.query(Producto).filter(
        Producto.nombre == pedido.nombre,
        Producto.precio == pedido.precio
    ).first()
    
    if not producto:
        # Crear el producto
        producto = Producto(
            nombre=pedido.nombre,
            descripcion=pedido.descripcion,
            precio=pedido.precio,
            disponibilidad=pedido.disponibilidad if pedido.disponibilidad is not None else True,
            categoria_id=categoria.id
        )
        db.add(producto)
        db.flush()
    
    # Calcular monto total
    cantidad = pedido.cantidad or 1
    monto_total = pedido.precio * cantidad
    
    # Crear el pedido
    nuevo_pedido = PedidoModel(
        n_pedido=n_pedido,
        usuario_id=usuario.id,
        monto_total=monto_total,
        estado=EstadoPedido.PENDIENTE,
        correo_enviado=False
    )
    
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    
    # Crear el detalle del pedido
    nuevo_detalle = DetallePedidoModel(
        pedido_id=nuevo_pedido.id,
        producto_id=producto.id,
        cantidad=cantidad,
        precio_unitario=pedido.precio
    )
    db.add(nuevo_detalle)
    
    db.commit()
    db.refresh(nuevo_pedido)
    
    return nuevo_pedido

@router.get("/pendientes", response_model=List[PedidoMostrar])
def listar_pedidos_pendientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lista todos los pedidos pendientes.
    Ya no requiere autenticación de administrador.
    """
    pedidos = db.query(PedidoModel).filter(PedidoModel.estado == EstadoPedido.PENDIENTE).offset(skip).limit(limit).all()
    return pedidos

@router.put("/confirmar/{pedido_id}", response_model=PedidoMostrar)
def confirmar_pedido(pedido_id: int, confirmacion: PedidoConfirmar, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Confirma o deniega un pedido.
    Ya no requiere autenticación de administrador.
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
def mis_pedidos(usuario_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lista todos los pedidos de un usuario específico.
    Ya no requiere autenticación, pero ahora requiere el usuario_id como parámetro.
    """
    pedidos = db.query(PedidoModel).filter(PedidoModel.usuario_id == usuario_id).offset(skip).limit(limit).all()
    return pedidos

@router.get("/estadisticas", response_model=EstadisticasPedidos)
def estadisticas_pedidos(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de pedidos.
    Ya no requiere autenticación de administrador.
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

@router.put("/cancelar/{pedido_id}", response_model=PedidoMostrar)
def cancelar_pedido(pedido_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Cancela un pedido pendiente.
    Ya no requiere autenticación.
    """
    # Buscar el pedido
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar que el pedido está en un estado que puede ser cancelado
    if pedido.estado != EstadoPedido.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden cancelar pedidos pendientes"
        )
    
    # Cancelar pedido
    pedido.estado = EstadoPedido.CANCELADO
    
    # Enviar correo de cancelación
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
    if usuario and usuario.email:
        background_tasks.add_task(
            send_email_smtp,
            email_to=usuario.email,
            subject="Pedido Cancelado",
            html_content=f"<p>Su pedido #{pedido.n_pedido} ha sido cancelado.</p>"
        )
        pedido.correo_enviado = True
    
    db.commit()
    db.refresh(pedido)
    return pedido

@router.delete("/{pedido_id}", status_code=204)
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """
    Elimina un pedido completamente de la base de datos.
    Ya no requiere autenticación de administrador.
    """
    # Buscar el pedido
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Eliminar el pedido (los detalles se eliminarán en cascada)
    db.delete(pedido)
    db.commit()
    
    return None

# Añadir esta importación al inicio del archivo
from app.schemas.pedido import PedidoEditar

# Añadir este nuevo endpoint después de los existentes
@router.put("/{pedido_id}", response_model=PedidoMostrar)
def editar_pedido(pedido_id: int, pedido_actualizado: PedidoEditar, db: Session = Depends(get_db)):
    """
    Edita un pedido existente y su producto asociado.
    Solo se pueden editar pedidos en estado PENDIENTE.
    """
    # Buscar el pedido
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Verificar que el pedido está en estado pendiente
    if pedido.estado != EstadoPedido.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden editar pedidos pendientes"
        )
    
    # Obtener el detalle del pedido (asumimos que solo hay uno por la estructura simplificada)
    detalle = db.query(DetallePedidoModel).filter(DetallePedidoModel.pedido_id == pedido_id).first()
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detalle de pedido no encontrado"
        )
    
    # Obtener el producto asociado al detalle
    producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Actualizar la categoría si se proporciona
    if pedido_actualizado.categoria:
        from app.models.categoria import CategoriaModel
        
        # Buscar o crear la categoría
        categoria = db.query(CategoriaModel).filter(CategoriaModel.nombre == pedido_actualizado.categoria).first()
        if not categoria:
            categoria = CategoriaModel(nombre=pedido_actualizado.categoria)
            db.add(categoria)
            db.flush()
            
        # Actualizar la categoría del producto
        producto.categoria_id = categoria.id
    
    # Actualizar los campos del producto si se proporcionan
    if pedido_actualizado.nombre is not None:
        producto.nombre = pedido_actualizado.nombre
    
    if pedido_actualizado.descripcion is not None:
        producto.descripcion = pedido_actualizado.descripcion
    
    if pedido_actualizado.disponibilidad is not None:
        producto.disponibilidad = pedido_actualizado.disponibilidad
    
    # Actualizar el precio y recalcular el monto total si es necesario
    precio_actualizado = False
    if pedido_actualizado.precio is not None and pedido_actualizado.precio != detalle.precio_unitario:
        detalle.precio_unitario = pedido_actualizado.precio
        producto.precio = pedido_actualizado.precio
        precio_actualizado = True
    
    # Actualizar la cantidad y recalcular el monto total si es necesario
    cantidad_actualizada = False
    if pedido_actualizado.cantidad is not None and pedido_actualizado.cantidad != detalle.cantidad:
        detalle.cantidad = pedido_actualizado.cantidad
        cantidad_actualizada = True
    
    # Recalcular el monto total si cambió el precio o la cantidad
    if precio_actualizado or cantidad_actualizada:
        pedido.monto_total = detalle.precio_unitario * detalle.cantidad
    
    # Guardar los cambios
    db.commit()
    db.refresh(pedido)
    
    return pedido