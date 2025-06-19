from fastapi import APIRouter
from app.api.endpoints import productos, usuarios, auth

api_router = APIRouter()

api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(productos.router, prefix="/productos", tags=["productos"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Añadir las nuevas rutas
from app.api.endpoints import categorias, pedidos

# Incluir los nuevos routers
api_router.include_router(categorias.router, prefix="/categorias", tags=["categorias"])
api_router.include_router(pedidos.router, prefix="/pedidos", tags=["pedidos"])

