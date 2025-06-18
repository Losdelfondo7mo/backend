from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Middleware para gestionar Cross-Origin Resource Sharing (CORS).

from app.api.router import api_router # Router principal que agrupa todos los endpoints de la API.
from app.db.base import Base # Clase base para los modelos SQLAlchemy, usada para crear tablas.
from app.db.session import engine # Motor de SQLAlchemy para la conexión con la base de datos.
from app.config.settings import settings # Configuración de la aplicación (nombre, versión, etc.).

# --- Creación de Tablas en la Base de Datos ---
# Esta línea crea todas las tablas definidas en tus modelos SQLAlchemy (aquellas que heredan de 'Base')
# si aún no existen en la base de datos conectada por 'engine'.
# En un entorno de producción más robusto, se suelen utilizar herramientas de migración como Alembic
# para gestionar los cambios en el esquema de la base de datos de forma versionada.
Base.metadata.create_all(bind=engine)

# --- Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title=settings.app_name, # Título de la API, aparecerá en la documentación (Swagger UI).
    version=settings.app_version, # Versión de la API.
    # description="Descripción detallada de tu API.", # Opcional: añade una descripción.
    # openapi_url="/api/v1/openapi.json" # Opcional: personaliza la URL del esquema OpenAPI.
)

# --- Configuración de CORS (Cross-Origin Resource Sharing) ---
# Define qué orígenes (dominios frontend) tienen permitido hacer solicitudes a esta API.
# Es una medida de seguridad importante para aplicaciones web.
origins = [
    "http://localhost:4200",  # Común para desarrollo local con Angular.
    "http://localhost:3000",  # Común para desarrollo local con React.
    "http://localhost:8080",  # Otro puerto común para desarrollo frontend.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Lista de orígenes permitidos. Usa ["*"] para permitir todos (no recomendado para producción).
    allow_credentials=True, # Permite que las solicitudes incluyan credenciales (ej. cookies, cabeceras de autorización).
    allow_methods=["*"],    # Métodos HTTP permitidos (ej. GET, POST, PUT, DELETE). ["*"] permite todos.
    allow_headers=["*"],    # Cabeceras HTTP permitidas en las solicitudes. ["*"] permite todas.
)
# --- Fin de Configuración de CORS ---

# --- Inclusión del Router Principal de la API ---
# Todas las rutas definidas en 'api_router' (y sus sub-routers) se añadirán a la aplicación
# bajo el prefijo "/api". Por ejemplo, un endpoint "/usuarios/crear" en el router de usuarios
# será accesible en "/api/usuarios/crear".
app.include_router(api_router, prefix="/api")

# --- Punto de Entrada para Ejecución Directa (Opcional) ---
# Esto permite ejecutar la aplicación directamente con `python main.py` usando Uvicorn.
# Uvicorn es un servidor ASGI rápido, ideal para FastAPI.
if __name__ == "__main__":
    import uvicorn
    # 'host="0.0.0.0"' hace que el servidor sea accesible desde otras máquinas en la red.
    # 'port=8000' es el puerto estándar, pero puede cambiarse.
    # 'reload=True' (no puesto aquí) es útil durante el desarrollo para recargar automáticamente
    # el servidor cuando se detectan cambios en el código.
    uvicorn.run(app, host="0.0.0.0", port=8000)

