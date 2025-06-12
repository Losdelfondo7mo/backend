from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.producto import Producto
from app.schemas.producto import ProductoCrear, ProductoMostrar

router = APIRouter()

@router.post("/", response_model=ProductoMostrar, status_code=201)
def crear_producto(producto: ProductoCrear, db: Session = Depends(get_db)):
    nuevo_producto = Producto(**producto.dict())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@router.get("/", response_model=List[ProductoMostrar])
def listar_productos(db: Session = Depends(get_db)):
    productos = db.query(Producto).all()
    return productos

@router.get("/{producto_id}", response_model=ProductoMostrar)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{producto_id}", response_model=ProductoMostrar)
def actualizar_producto(producto_id: int, producto_actualizado: ProductoCrear, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in producto_actualizado.dict().items():
        setattr(producto, key, value)
    
    db.commit()
    db.refresh(producto)
    return producto

@router.delete("/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto)
    db.commit()
    return