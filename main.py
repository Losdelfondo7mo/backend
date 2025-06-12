from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from typing import Optional
import os
from dotenv import load_dotenv
import mysql.connector
from fastapi.middleware .cors import CORSMiddleware 
from sqlalchemy import Column, Integer, String

'''
app = FastAPI() # aca estoy definiendo las fastAPI

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

template = Jinja2Templates(directory="./view")#todas las plantillas de jinja se guardan ahi

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

@app.get("/") # aca se define en las rutas
async def root( ):
    return {"message": "hola"}

@app.get('/signup', response_class="HTMLResponse")
async def signup(req: Request):
    return template.TemplateResponse('signup.html', {'request':req})

@app.post("/register")
async def register_user(user: UserCreate):
    # Validar que el email tenga formato correcto
    
    # Validar longitud mínima de contraseñ
    
    # Datos del usuario para guardar
    user_data = {
        "lastname": user.lastname,
        "firstname": user.firstname,
        "country": user.country,
        "username": user.username,
        "password_user": user.password_user
        
    }
    
    # Aquí iría la lógica para guardar en la base de datos
    # Por simplicidad, simulamos la operación
    print("Usuario creado:", user_data)
    
    return {
        "message": "Usuario creado exitosamente",
        "username": user.username
    }#aca es donde debo comentar de  nuevo'''


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, create_engine, Text, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext

# aca va la configuración de conexión a MySQL
DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# aca vamos haciendo el modelo que va a tener la base de datos
class UsuarioModel(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(15), nullable=False)
    apellido = Column(String(15), nullable=False)
    email = Column(String(30), unique=True, nullable=False)
    usuario = Column(String(20), unique=True, nullable=False)
    contraseña_hash = Column(String(50), nullable=False)


# ahora vamos a intentar hacer lo mismpo pero para los productos 
class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(25), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    imagen_url = Column(String(255))
    categoria = Column(String(10))

# aca se crea las tablas en la BS
Base.metadata.create_all(bind=engine)

# iniciamos la api
app = FastAPI()

# hacemos una seguridad de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# esquema para los --usuarios -- 
class UsuarioCrear(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    usuario: str
    contraseña: str

class UsuarioVerificar(BaseModel):
    usuario: str

def verificar_contraseña(contraseña_plana: str, contraseña_hash: str):
    return pwd_context.verify(contraseña_plana, contraseña_hash)

def obtener_contraseña_hash(contraseña: str):
    return pwd_context.hash(contraseña)

# aca estamos creando los usuarios 
@app.post("/usuarios/crear", status_code=201)
async def crear_usuario(usuario: UsuarioCrear):
    db = SessionLocal()

    try:
        # verificamossi ya existe el usuario o email
        if db.query(UsuarioModel).filter(UsuarioModel.usuario == usuario.usuario).first():
            raise HTTPException(status_code=400, detail="Este usuario ya existe")

        if db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first():
            raise HTTPException(status_code=400, detail="Este email ya está registrado")

        # se crea un usuario nuevo
        nuevo_usuario = UsuarioModel(
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            usuario=usuario.usuario,
            contraseña_hash=obtener_contraseña_hash(usuario.contraseña)
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        return {"mensaje": "Usuario creado exitosamente"} # lo que devuelve si todo va bien
    
    finally:
        db.close()

# verificamos si rl usuario ya existe 
@app.get("/usuarios/verificar/{usuario}")
async def verificar_usuario(usuario: str):
    db = SessionLocal()
    try:
        usuario_existente = db.query(UsuarioModel).filter(
            UsuarioModel.usuario == usuario
        ).first()

        if not usuario_existente:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        return {
            "usuario": usuario_existente.usuario,
            "contraseña": usuario_existente.contraseña_hash,
            "nombre": f"{usuario_existente.nombre} {usuario_existente.apellido}",
            "email": usuario_existente.email
        }
    finally:
        db.close()




#--PRODUCTOOOOSSSS--

#aca crearia los productos pero esto lo deberia hacer una ADMIN
class ProductoCrear(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    imagen_url: Optional[str] = None
    categoria: Optional[str] = None

#lo que se va a mostrar

class ProductoMostrar(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    stock: int
    imagen_url: Optional[str]
    categoria: Optional[str]

    class Config:
        orm_mode = True

#ENDPOINTS
#ESTE ES PARA CREAR 
@app.post("/productos/", response_model=ProductoMostrar, status_code=201)
def crear_producto(producto: ProductoCrear):
    db = SessionLocal()
    nuevo_producto = Producto(**producto.dict())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

#mostrar los productos
@app.get("/productos/", response_model=list[ProductoMostrar])
def listar_productos():
    db = SessionLocal()
    productos = db.query(Producto).all()
    return productos

#buscar por id
@app.get("/productos/{producto_id}", response_model=ProductoMostrar)
def obtener_producto(producto_id: int):
    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

# actualizar los productos 
@app.put("/productos/{producto_id}", response_model=ProductoMostrar)
def actualizar_producto(producto_id: int, producto_actualizado: ProductoCrear):
    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in producto_actualizado.dict().items():
        setattr(producto, key, value)
    
    db.commit()
    db.refresh(producto)
    return producto

#aca borramos los productos 
@app.delete("/productos/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int):
    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto)
    db.commit()
    return

