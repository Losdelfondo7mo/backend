from fastapi import APIRouter
from app.api.endpoints import productos, usuarios

api_router = APIRouter()

api_router.include_router(productos.router, prefix="/productos", tags=["productos"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])