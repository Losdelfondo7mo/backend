from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import get_db # Dependencia para obtener la sesión de la base de datos.
from app.models.producto import Producto # Modelo SQLAlchemy para la tabla de productos.
from app.schemas.producto import ProductoCrear, ProductoMostrar # Esquemas Pydantic para la validación y serialización de datos de productos.
from app.core.security import get_current_active_user # Dependencia para obtener el usuario autenticado y activo.
from app.models.usuario import UsuarioModel # Modelo de Usuario, usado aquí para el tipado del usuario actual.

router = APIRouter() # Crea un router para los endpoints relacionados con productos.

# Nuevo endpoint específico para crear productos
@router.post("/crear", response_model=ProductoMostrar, status_code=201)
def crear_producto_endpoint(producto: ProductoCrear, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Endpoint específico para crear un nuevo producto.
    Funciona igual que el endpoint POST / pero con una ruta más explícita.
    """
    nuevo_producto = Producto(**producto.model_dump())
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
def actualizar_producto(producto_id: int, producto_actualizado: ProductoCrear, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Actualiza la información de un producto existente, identificado por su ID.
    Requiere autenticación.

    Parámetros:
        producto_id (int): El ID del producto a actualizar.
        producto_actualizado (ProductoCrear): Los nuevos datos para el producto.
        db (Session): Sesión de SQLAlchemy para la base de datos.
        current_user (UsuarioModel): El usuario autenticado.

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
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), current_user: UsuarioModel = Depends(get_current_active_user)):
    """
    Elimina un producto de la base de datos utilizando su ID.
    Requiere autenticación.

    Parámetros:
        producto_id (int): El ID del producto a eliminar.
        db (Session): Sesión de SQLAlchemy para la base de datos.
        current_user (UsuarioModel): El usuario autenticado.

    Excepciones:
        HTTPException (404): Si el producto no se encuentra.
    """
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto) # Elimina el producto de la sesión.
    db.commit() # Confirma la eliminación en la base de datos.
    return # No se devuelve contenido con el código de estado 204.