# ... existing code ...

import mercadopago
from fastapi import BackgroundTasks, APIRouter, Depends, HTTPException, status, Request
from models.models import PedidoModel, DetallePedidoModel, Producto

# Add this to your environment variables or settings.py
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

@router.post("/webhook")
async def webhook_notification(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Get the notification data
    data = await request.json()
    
    # Initialize the Mercado Pago SDK
    sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
    
    # Process different notification types
    if "type" in data and data["type"] == "payment":
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
            # Send confirmation email
            background_tasks.add_task(
                send_email_smtp,
                pedido.usuario.email if pedido.usuario else "anonymous@example.com",
                "Pago confirmado",
                f"Tu pago para el pedido #{pedido.n_pedido} ha sido confirmado."
            )
        elif payment["status"] == "rejected":
            pedido.estado = EstadoPedido.DENEGADO
        elif payment["status"] == "in_process" or payment["status"] == "pending":
            pedido.estado = EstadoPedido.PENDIENTE
        
        db.commit()
    
    return {"status": "success"}

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
            "description": producto.descripcion,
            "quantity": detalle.cantidad,
            "currency_id": "MXN",  # Change according to your currency
            "unit_price": float(detalle.precio_unitario)
        })
    
    # Get the base URL for callbacks
    base_url = str(request.base_url).rstrip('/')
    
    # Create preference data
    preference_data = {
        "items": items,
        "external_reference": str(pedido.n_pedido),
        "back_urls": {
            "success": f"{base_url}/api/pedidos/pago-exitoso/{pedido_id}",
            "failure": f"{base_url}/api/pedidos/pago-fallido/{pedido_id}",
            "pending": f"{base_url}/api/pedidos/pago-pendiente/{pedido_id}"
        },
        "notification_url": f"{base_url}/api/pedidos/webhook",
        "auto_return": "approved"
    }
    
    # Create the preference
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    
    return {
        "id": preference["id"],
        "init_point": preference["init_point"],
        "sandbox_init_point": preference["sandbox_init_point"]
    }


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