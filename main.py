from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.base import UsuarioModel, Producto  # Importar modelos para crear tablas
from sqlalchemy.ext.declarative import declarative_base
import logging

Base = declarative_base()

# Intentar crear tablas en la base de datos
try:
    from app.db.session import engine
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created successfully")
except Exception as e:
    logging.warning(f"Could not create database tables: {e}")
    logging.warning("Server will start without database connection")

app = FastAPI(title="API Olimpiadas", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Olimpiadas"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

