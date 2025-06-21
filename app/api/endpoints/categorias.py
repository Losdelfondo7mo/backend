from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.categoria import CategoriaModel
from app.schemas.categoria import CategoriaCrear, CategoriaMostrar
# Comentamos las importaciones de autenticación que no vamos a usar
# from app.core.security import get_current_active_user, get_current_admin_user
from app.models.usuario import UsuarioModel

router = APIRouter()

@router.post("/", response_model=CategoriaMostrar, status_code=201)
def crear_categoria(categoria: CategoriaCrear, db: Session = Depends(get_db)):
    """
    Crea una nueva categoría.
    Ya no requiere autenticación de administrador.
    """
    db_categoria = CategoriaModel(nombre=categoria.nombre)
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

@router.get("/", response_model=List[CategoriaMostrar])
def listar_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaModel).offset(skip).limit(limit).all()
    return categorias

@router.get("/{categoria_id}", response_model=CategoriaMostrar)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaModel).filter(CategoriaModel.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria