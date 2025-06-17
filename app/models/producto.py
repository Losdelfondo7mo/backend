from sqlalchemy import Column, Integer, String, Float, Text
from app.db.base import Base

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(25), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    imagen_url = Column(String(255))
    categoria = Column(String(10))