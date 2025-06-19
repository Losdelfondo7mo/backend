from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.base import Base

class VisitaModel(Base):
    """
    Modelo SQLAlchemy para trackear las visitas al sitio.
    """
    __tablename__ = "visitas"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv4 o IPv6
    user_agent = Column(Text, nullable=True)  # Información del navegador
    fecha_visita = Column(DateTime, default=datetime.utcnow, nullable=False)
    pagina_visitada = Column(String(255), nullable=True)  # URL visitada
    usuario_id = Column(Integer, nullable=True)  # Si el usuario está logueado