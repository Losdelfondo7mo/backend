from sqlalchemy import Column, Integer, String
from app.db.base import Base # Importa la clase Base para la declaración de modelos.

class UsuarioModel(Base):
    """
    Modelo SQLAlchemy que representa la tabla 'usuarios' en la base de datos.
    Almacena la información de los usuarios registrados en el sistema.
    """
    __tablename__ = "usuarios" # Nombre de la tabla en la base de datos.
    
    id = Column(Integer, primary_key=True, index=True) # Identificador único del usuario, indexado.
    nombre = Column(String(50), nullable=False) # Nombre del usuario. Ajustado a 50 caracteres.
    apellido = Column(String(50), nullable=False) # Apellido del usuario. Ajustado a 50 caracteres.
    email = Column(String(100), unique=True, nullable=False, index=True) # Correo electrónico del usuario, debe ser único y está indexado. Ajustado a 100 caracteres.
    usuario = Column(String(50), unique=True, nullable=False, index=True) # Nombre de usuario para login, debe ser único y está indexado. Ajustado a 50 caracteres.
    contraseña_hash = Column(String(255), nullable=False) # Hash de la contraseña del usuario. Longitud aumentada para hashes modernos.