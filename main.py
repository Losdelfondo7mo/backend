from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.base import UsuarioModel, Producto  # Importar modelos para crear tablas
from app.db.session import engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

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

