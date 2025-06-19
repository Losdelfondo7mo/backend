from fastapi import APIRouter
from app.api.endpoints import productos, usuarios, auth

api_router = APIRouter()

# Incluye el router para los endpoints de usuarios.
# Todas las rutas definidas en 'usuarios.router' tendrán el prefijo "/usuarios"
# y se agruparán bajo la etiqueta "usuarios" en la documentación de OpenAPI (Swagger).
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])

# Incluye el router para los endpoints de productos.
api_router.include_router(productos.router, prefix="/productos", tags=["productos"])

# Incluye el router para los endpoints de autenticación.
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])