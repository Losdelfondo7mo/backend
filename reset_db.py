import sys
import os

# Añadir el directorio actual al path para poder importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, MetaData
from app.db.base import Base
from app.config.settings import settings
from app.db.session import engine

# Importar todos los modelos para que SQLAlchemy los conozca
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# Definir la nueva estructura de modelos
class CategoriaModel(Base):
    __tablename__ = "categorias"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)
    
    # Relaciones
    productos = relationship("ProductoModel", back_populates="categoria")

class ProductoModel(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    correo = Column(String(100), nullable=True)  # Nuevo campo según las imágenes
    tipo = Column(String(50), nullable=True)     # Nuevo campo según las imágenes
    disponibilidad = Column(Boolean, default=True)  # Nuevo campo según las imágenes
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    
    # Relaciones
    categoria = relationship("CategoriaModel", back_populates="productos")
    detalles_pedido = relationship("DetallePedidoModel", back_populates="producto")

class UsuarioModel(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    usuario = Column(String(50), unique=True, nullable=False, index=True)
    contraseña_hash = Column(String, nullable=True)
    rol = Column(String(20), nullable=False, default="usuario")
    
    # Campos OAuth (mantenidos de la estructura actual)
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Campos de auditoría (mantenidos de la estructura actual)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    pedidos = relationship("PedidoModel", back_populates="usuario")

class EstadoPedido(enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    DENEGADO = "denegado"
    ENTREGADO = "entregado"

class PedidoModel(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    n_pedido = Column(String(20), unique=True, nullable=False)  # Número de pedido según las imágenes
    estado = Column(Enum(EstadoPedido), default=EstadoPedido.PENDIENTE, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    monto_total = Column(Float, nullable=False)
    correo_enviado = Column(Boolean, default=False)  # Según las imágenes
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relaciones
    usuario = relationship("UsuarioModel", back_populates="pedidos")
    detalles = relationship("DetallePedidoModel", back_populates="pedido")

class DetallePedidoModel(Base):
    __tablename__ = "detalles_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    
    # Relaciones
    pedido = relationship("PedidoModel", back_populates="detalles")
    producto = relationship("ProductoModel", back_populates="detalles_pedido")

# Mantener el modelo de visitas que ya existe
class VisitaModel(Base):
    __tablename__ = "visitas"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv4 o IPv6
    user_agent = Column(Text, nullable=True)  # Información del navegador
    fecha_visita = Column(DateTime, default=datetime.utcnow, nullable=False)
    pagina_visitada = Column(String(255), nullable=True)  # URL visitada
    usuario_id = Column(Integer, nullable=True)  # Si el usuario está logueado

def reset_database():
    # Crear un objeto MetaData para manejar la eliminación de tablas
    metadata = MetaData()
    metadata.reflect(bind=engine)  # Obtener todas las tablas existentes
    
    # Eliminar todas las tablas existentes
    print("Eliminando todas las tablas existentes...")
    metadata.drop_all(engine)
    print("Tablas eliminadas correctamente.")
    
    # Crear todas las tablas nuevamente con la estructura actualizada
    print("Creando nuevas tablas con la estructura actualizada...")
    Base.metadata.create_all(engine)
    print("Tablas creadas correctamente.")
    
    print("\nLa base de datos ha sido reiniciada con éxito.")
    print("Estructura de tablas creada:")
    print("- categorias")
    print("- productos")
    print("- usuarios")
    print("- pedidos")
    print("- detalles_pedido")
    print("- visitas")

if __name__ == "__main__":
    # Pedir confirmación antes de resetear la base de datos
    print("¡ADVERTENCIA! Este script eliminará TODOS los datos de la base de datos.")
    print(f"Base de datos: {settings.database_url}")
    confirmation = input("¿Estás seguro de que deseas continuar? (s/n): ")
    
    if confirmation.lower() == 's':
        reset_database()
    else:
        print("Operación cancelada.")