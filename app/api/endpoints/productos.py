from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
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

# Endpoint modificado para aceptar ProductoCrear directamente
@router.post("/crear", response_model=ProductoMostrar, status_code=201)
def crear_producto_endpoint(producto: ProductoCrear, db: Session = Depends(get_db)):
    """
    Endpoint para crear un nuevo producto.
    Recibe información del producto incluyendo nombre, descripción, precio, disponibilidad y categoría.
    """
    # Buscar o crear la categoría
    categoria = None
    if producto.categoria:
        # Buscar si la categoría ya existe
        categoria = db.query(CategoriaModel).filter(CategoriaModel.nombre == producto.categoria).first()
        
        # Si no existe, crearla
        if not categoria:
            categoria = CategoriaModel(nombre=producto.categoria)
            db.add(categoria)
            db.commit()
            db.refresh(categoria)
    else:
        # Si no se proporciona categoría, usar una por defecto
        categoria = db.query(CategoriaModel).first()
        if not categoria:
            categoria = CategoriaModel(nombre="General")
            db.add(categoria)
            db.commit()
            db.refresh(categoria)
    
    # Crear nuevo producto
    nuevo_producto = Producto(
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio,
        disponibilidad=producto.disponibilidad if producto.disponibilidad is not None else True,
        categoria_id=categoria.id
    )
    
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    
    return nuevo_producto

# Mantener el endpoint original para compatibilidad con el formato anterior
@router.post("/crear_pedido", response_model=ProductoMostrar, status_code=201)
def crear_producto_pedido(producto_pedido: ProductoPedidoCrear, db: Session = Depends(get_db)):
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
        List[ProductoMostrar]: Una lista de productos con información de categoría.
    """
    # Usamos join para cargar la relación con categoría
    productos = db.query(Producto).options(joinedload(Producto.categoria)).all()
    
    # Creamos una lista de diccionarios con la información necesaria
    resultado = []
    for producto in productos:
        # Creamos una copia del producto para no modificar el objeto original
        producto_dict = {
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": producto.precio,
            "disponibilidad": producto.disponibilidad,
            "categoria_id": producto.categoria_id,
            "categoria": producto.categoria.nombre if producto.categoria else None
        }
        resultado.append(producto_dict)
    
    return resultado

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
        ProductoMostrar: Los detalles del producto encontrado con información de categoría.
    """
    producto = db.query(Producto).options(joinedload(Producto.categoria)).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Creamos un diccionario con la información necesaria
    producto_dict = {
        "id": producto.id,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "precio": producto.precio,
        "disponibilidad": producto.disponibilidad,
        "categoria_id": producto.categoria_id,
        "categoria": producto.categoria.nombre if producto.categoria else None
    }
    
    return producto_dict

@router.put("/{producto_id}", response_model=ProductoMostrar)
def actualizar_producto(producto_id: int, producto_actualizado: ProductoCrear, db: Session = Depends(get_db)):
    """
    Actualiza un producto existente utilizando su ID.
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
    
    # Manejar el campo categoria especialmente
    datos_actualizados = producto_actualizado.model_dump()
    if 'categoria' in datos_actualizados and datos_actualizados['categoria']:
        from app.models.categoria import CategoriaModel
        
        # Buscar o crear la categoría
        categoria = db.query(CategoriaModel).filter(CategoriaModel.nombre == datos_actualizados['categoria']).first()
        if not categoria:
            categoria = CategoriaModel(nombre=datos_actualizados['categoria'])
            db.add(categoria)
            db.flush()
        
        # Asignar el ID de la categoría al producto
        producto.categoria_id = categoria.id
        
        # Eliminar el campo categoria para que no intente asignarlo directamente
        del datos_actualizados['categoria']
    
    # Actualizar los demás campos
    for key, value in datos_actualizados.items():
        if hasattr(producto, key):
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