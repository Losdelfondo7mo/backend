from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import get_db # Dependencia para obtener la sesión de la base de datos.
from app.models.producto import Producto # Modelo SQLAlchemy para la tabla de productos.
from app.schemas.producto import ProductoCrear, ProductoMostrar, ProductoPedidoCrear, ProductoItem # Esquemas Pydantic para la validación y serialización de datos de productos.
# Comentamos la importación de autenticación que no vamos a usar
# from app.core.security import get_current_active_user # Dependencia para obtener el usuario autenticado y activo.
from app.models.usuario import UsuarioModel # Modelo de Usuario, usado aquí para el tipado del usuario actual.
from app.models.categoria import CategoriaModel  # Añade esta importación al inicio del archivo

router = APIRouter() # Crea un router para los endpoints relacionados con productos.

# Nuevo endpoint específico para crear productos - eliminamos el requisito de autenticación
@router.post("/crear", response_model=ProductoMostrar, status_code=201)
def crear_producto_endpoint(producto_pedido: ProductoPedidoCrear, db: Session = Depends(get_db)):
    """
    Endpoint específico para crear un nuevo producto basado en un pedido.
    Recibe información de usuario, productos y total.
    """
    # Verificar que el total coincide con la suma de precios * cantidades
    total_calculado = sum(item.precio * item.cantidad for item in producto_pedido.productos)
    if total_calculado != producto_pedido.total:
        raise HTTPException(status_code=400, detail="El total no coincide con la suma de los productos")
    
    # Por ahora, solo tomamos el primer producto de la lista para crear
    # En un caso real, probablemente querrías crear un pedido con múltiples productos
    if not producto_pedido.productos:
        raise HTTPException(status_code=400, detail="No se proporcionaron productos")
    
    item = producto_pedido.productos[0]
    
    # Verificar si el producto ya existe
    producto_existente = db.query(Producto).filter(Producto.id == item.id).first()
    if producto_existente:
        # Actualizar producto existente
        producto_existente.nombre = item.nombre
        producto_existente.precio = item.precio
        db.commit()
        db.refresh(producto_existente)
        return producto_existente
    else:
        # Obtener una categoría existente o crear una por defecto
        categoria = db.query(CategoriaModel).first()
        if not categoria:
            # Si no hay categorías, crear una por defecto
            categoria = CategoriaModel(nombre="General")
            db.add(categoria)
            db.commit()
            db.refresh(categoria)
        
        # Crear nuevo producto
        nuevo_producto = Producto(
            nombre=item.nombre,
            precio=item.precio,
            disponibilidad=True,
            categoria_id=categoria.id  # Asignar el ID de la categoría
        )
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        return nuevo_producto

@router.get("/", response_model=List[ProductoMostrar])
def listar_productos(db: Session = Depends(get_db)):
    """
    Recupera una lista de todos los productos disponibles.

    Parámetros:
        db (Session): Sesión de SQLAlchemy para la base de datos.

    Retorna:
        List[ProductoMostrar]: Una lista de productos.
    """
    productos = db.query(Producto).all()
    return productos

@router.get("/{producto_id}", response_model=ProductoMostrar)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un producto específico mediante su ID.

    Parámetros:
        producto_id (int): El ID del producto a buscar.
        db (Session): Sesión de SQLAlchemy para la base de datos.

    Excepciones:
        HTTPException (404): Si no se encuentra ningún producto con el ID proporcionado.

    Retorna:
        ProductoMostrar: Los detalles del producto encontrado.
    """
    producto = db.query(Producto).filter(Producto.id == producto_id).first() # Busca el producto por su ID.
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{producto_id}", response_model=ProductoMostrar)
def actualizar_producto(producto_id: int, producto_actualizado: ProductoCrear, db: Session = Depends(get_db)):
    """
    Actualiza la información de un producto existente, identificado por su ID.
    Ya no requiere autenticación.

    Parámetros:
        producto_id (int): El ID del producto a actualizar.
        producto_actualizado (ProductoCrear): Los nuevos datos para el producto.
        db (Session): Sesión de SQLAlchemy para la base de datos.

    Excepciones:
        HTTPException (404): Si el producto no se encuentra.

    Retorna:
        ProductoMostrar: El producto con la información actualizada.
    """
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Itera sobre los datos del producto actualizado y los asigna al modelo existente.
    for key, value in producto_actualizado.model_dump().items():
        setattr(producto, key, value)
    
    db.commit() # Guarda los cambios en la base de datos.
    db.refresh(producto) # Refresca la instancia del producto.
    return producto

@router.delete("/{producto_id}", status_code=204) # HTTP 204 indica éxito sin contenido de respuesta.
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    """
    Elimina un producto de la base de datos utilizando su ID.
    Ya no requiere autenticación.

    Parámetros:
        producto_id (int): El ID del producto a eliminar.
        db (Session): Sesión de SQLAlchemy para la base de datos.

    Excepciones:
        HTTPException (404): Si el producto no se encuentra.
    """
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto) # Elimina el producto de la sesión.
    db.commit() # Confirma la eliminación en la base de datos.
    return # No se devuelve contenido con el código de estado 204.