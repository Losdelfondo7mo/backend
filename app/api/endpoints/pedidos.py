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

@router.post("/crear", response_model=PedidoMostrar, status_code=201)
def crear_pedido(pedido: PedidoCrear, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Registra un nuevo pedido en el sistema como pendiente.
    Acepta una lista de productos con id, nombre, precio y cantidad.
    Puede recibir usuario_id o nombre de usuario (campo 'usuario').
    """
    # Generar número de pedido único
    import random
    import string
    n_pedido = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Verificar si el usuario existe, primero por ID y luego por nombre de usuario
    usuario = None
    if pedido.usuario_id:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
    
    # Si no se encontró por ID pero se proporcionó un nombre de usuario, buscar por nombre
    if not usuario and pedido.usuario:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.usuario == pedido.usuario).first()
    
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
    
    # Calcular monto total si no se proporciona
    monto_total = pedido.total if pedido.total is not None else sum(item.precio * item.cantidad for item in pedido.productos)
    
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
    
    # Crear los detalles del pedido para cada producto
    for item in pedido.productos:
        # Verificar si el producto existe
        producto = db.query(Producto).filter(Producto.id == item.id).first()
        
        if not producto:
            # Si el producto no existe, crearlo
            # Obtener una categoría por defecto
            categoria = db.query(CategoriaModel).first()
            if not categoria:
                categoria = CategoriaModel(nombre="General")
                db.add(categoria)
                db.flush()
            
            producto = Producto(
                id=item.id,
                nombre=item.nombre,
                precio=item.precio,
                disponibilidad=True,
                categoria_id=categoria.id
            )
            db.add(producto)
            db.flush()
        
        # Crear el detalle del pedido
        nuevo_detalle = DetallePedidoModel(
            pedido_id=nuevo_pedido.id,
            producto_id=producto.id,
            cantidad=item.cantidad,
            precio_unitario=item.precio
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
                recipients=[usuario.email],  # Changed from email_to to recipients as a list
                subject="Pedido Confirmado",
                body_html=f"<p>Su pedido #{pedido.n_pedido} ha sido confirmado.</p>"  # Changed from html_content to body_html
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
                recipients=[usuario.email],  # Changed from email_to to recipients as a list
                subject="Pedido Denegado",
                body_html=f"<p>Lo sentimos, su pedido #{pedido.n_pedido} ha sido denegado.</p>"  # Changed from html_content to body_html
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
    try:
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
        
        # Actualizar el estado usando el modelo ORM directamente
        # Esto evita problemas con la conversión de enums
        from sqlalchemy import update
        stmt = update(PedidoModel).where(PedidoModel.id == pedido_id).values(
            estado=EstadoPedido.CANCELADO,
            correo_enviado=True
        )
        db.execute(stmt)
        
        # Enviar correo de cancelación
        usuario = db.query(UsuarioModel).filter(UsuarioModel.id == pedido.usuario_id).first()
        if usuario and usuario.email:
            background_tasks.add_task(
                send_email_smtp,
                recipients=[usuario.email],  # Cambio: email_to → recipients como lista
                subject="Pedido Cancelado",
                body_html=f"<p>Su pedido #{pedido.n_pedido} ha sido cancelado.</p>"  # Cambio: html_content → body_html
            )
        
        # Hacer commit de los cambios
        db.commit()
        # Refrescar el pedido para obtener los cambios
        pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
        return pedido
    except Exception as e:
        # Hacer rollback en caso de error
        db.rollback()
        # Registrar el error para depuración
        print(f"Error al cancelar pedido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar el pedido: {str(e)}"
        )

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

@router.get("/todos", response_model=List[PedidoMostrar])
def listar_todos_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lista todos los pedidos (pendientes, aprobados y cancelados).
    Para uso del panel de administración.
    """
    pedidos = db.query(PedidoModel).offset(skip).limit(limit).all()
    return pedidos

# Añadir estas importaciones al inicio del archivo
import os
import mercadopago
from fastapi import Request
from app.core.settings import MERCADOPAGO_ACCESS_TOKEN

@router.post("/crear-preferencia/{pedido_id}", response_model=dict)
async def crear_preferencia_pago(pedido_id: int, request: Request, db: Session = Depends(get_db)):
    # Get the pedido from database
    pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Log token (be careful with sensitive info)
    print(f"Using Mercado Pago token: {MERCADOPAGO_ACCESS_TOKEN[:5]}...")
    
    # Get the detalles of the pedido
    detalles = db.query(DetallePedidoModel).filter(DetallePedidoModel.pedido_id == pedido_id).all()
    
    # Initialize the Mercado Pago SDK
    sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
    
    # Prepare items for the preference
    items = []
    for detalle in detalles:
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        items.append({
            "id": str(producto.id),
            "title": producto.nombre,
            "description": producto.descripcion if hasattr(producto, 'descripcion') else "",
            "quantity": detalle.cantidad,
            "currency_id": "MXN",  # Change according to your currency
            "unit_price": float(detalle.precio_unitario)
        })
    
    # Get the base URL for callbacks
    # Reemplazar esto
    base_url = str(request.base_url).rstrip('/')
    
    # Por esto
    base_url_api = str(request.base_url).rstrip('/')  # Para la API/webhook
    base_url_frontend = "https://los-del-fondo-7mo.web.app"  # Tu URL de Firebase
    
    # Y luego modificar la configuración
    preference_data = {
        "items": items,
        "external_reference": str(pedido.n_pedido),
        "back_urls": {
            "success": f"{base_url_frontend}/pago-exitoso/{pedido_id}",
            "failure": f"{base_url_frontend}/pago-fallido/{pedido_id}",
            "pending": f"{base_url_frontend}/pago-pendiente/{pedido_id}"
        },
        "notification_url": f"{base_url_api}/api/pedidos/webhook",
        "auto_return": "approved"
    }
    
    # Create the preference
    try:
        preference_response = sdk.preference().create(preference_data)
        print(f"Preference response: {preference_response}")
        
        if "response" not in preference_response:
            print(f"Error: 'response' key not found in preference_response: {preference_response}")
            raise HTTPException(status_code=500, detail="Error creating Mercado Pago preference: Invalid response format")
        
        preference = preference_response["response"]
        print(f"Preference data: {preference}")
        
        # Check if required keys exist
        if "id" not in preference:
            print(f"Error: 'id' key not found in preference: {preference}")
            raise HTTPException(status_code=500, detail="Error creating Mercado Pago preference: Missing ID")
        
        if "init_point" not in preference:
            print(f"Error: 'init_point' key not found in preference: {preference}")
            raise HTTPException(status_code=500, detail="Error creating Mercado Pago preference: Missing init_point")
        
        if "sandbox_init_point" not in preference:
            print(f"Error: 'sandbox_init_point' key not found in preference: {preference}")
            raise HTTPException(status_code=500, detail="Error creating Mercado Pago preference: Missing sandbox_init_point")
        
        return {
            "id": preference["id"],
            "init_point": preference["init_point"],
            "sandbox_init_point": preference["sandbox_init_point"]
        }
    except Exception as e:
        print(f"Error creating Mercado Pago preference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Mercado Pago preference: {str(e)}")

@router.post("/webhook")
async def webhook_notification(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Get the notification data
    data = await request.json()
    
    # Initialize the Mercado Pago SDK
    sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
    
    # Process different notification types
    if "type" in data:
        if data["type"] == "payment":
            payment_id = data["data"]["id"]
            
            # Get payment information
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info["response"]
            
            # Get the external reference (pedido number)
            external_reference = payment["external_reference"]
            
            # Find the pedido by n_pedido
            pedido = db.query(PedidoModel).filter(PedidoModel.n_pedido == external_reference).first()
            if not pedido:
                return {"status": "error", "message": "Pedido not found"}
            
            # Update pedido status based on payment status
            if payment["status"] == "approved":
                pedido.estado = EstadoPedido.CONFIRMADO
                pedido.fecha_confirmacion = datetime.utcnow()
                # Send confirmation email
                background_tasks.add_task(
                    send_email_smtp,
                    recipients=[pedido.usuario.email] if pedido.usuario and hasattr(pedido.usuario, 'email') else ["anonymous@example.com"],
                    subject="Pago confirmado",
                    body_html=f"Tu pago para el pedido #{pedido.n_pedido} ha sido confirmado."
                )
            elif payment["status"] == "rejected":
                pedido.estado = EstadoPedido.DENEGADO
            elif payment["status"] == "in_process" or payment["status"] == "pending":
                pedido.estado = EstadoPedido.PENDIENTE
            
            db.commit()
        elif data["type"] == "merchant_order":
            # Obtener el ID de la orden
            order_id = data["data"]["id"]
            
            # Obtener información de la orden
            order_info = sdk.merchant_order().get(order_id)
            order = order_info["response"]
            
            # Obtener la referencia externa (número de pedido)
            external_reference = order["external_reference"]
            
            # Encontrar el pedido por n_pedido
            pedido = db.query(PedidoModel).filter(PedidoModel.n_pedido == external_reference).first()
            if not pedido:
                return {"status": "error", "message": "Pedido not found"}
            
            # Actualizar el estado del pedido según el estado de la orden
            if order["order_status"] == "paid":
                pedido.estado = EstadoPedido.CONFIRMADO
                pedido.fecha_confirmacion = datetime.utcnow()
                
                # Actualizar información adicional si está disponible
                if "last_updated" in order:
                    try:
                        # Convertir la fecha de string a datetime
                        from dateutil import parser
                        pedido.fecha_actualizacion = parser.parse(order["last_updated"])
                    except Exception as e:
                        print(f"Error parsing date: {str(e)}")
                
                # Actualizar información del comprador si está disponible
                if "payer" in order and pedido.usuario:
                    payer = order["payer"]
                    if "email" in payer and payer["email"] and not pedido.usuario.email.startswith("anonimo_"):
                        pedido.usuario.email = payer["email"]
                
                # Enviar correo de confirmación
                background_tasks.add_task(
                    send_email_smtp,
                    recipients=[pedido.usuario.email] if pedido.usuario and hasattr(pedido.usuario, 'email') else ["anonymous@example.com"],
                    subject="Pago confirmado",
                    body_html=f"Tu pago para el pedido #{pedido.n_pedido} ha sido confirmado."
                )
            elif order["order_status"] == "payment_required":
                pedido.estado = EstadoPedido.PENDIENTE
            elif order["order_status"] == "reverted":
                pedido.estado = EstadoPedido.DENEGADO
            
            db.commit()
    
    return {"status": "success"}

@router.get("/pago-exitoso/{pedido_id}")
async def pago_exitoso(pedido_id: int, db: Session = Depends(get_db)):
    # This endpoint will be called when payment is successful
    # You can update the pedido status here if needed
    return {"status": "success", "message": "Pago exitoso"}

@router.get("/pago-fallido/{pedido_id}")
async def pago_fallido(pedido_id: int, db: Session = Depends(get_db)):
    # This endpoint will be called when payment fails
    return {"status": "error", "message": "Pago fallido"}

@router.get("/pago-pendiente/{pedido_id}")
async def pago_pendiente(pedido_id: int, db: Session = Depends(get_db)):
    # This endpoint will be called when payment is pending
    return {"status": "pending", "message": "Pago pendiente"}
