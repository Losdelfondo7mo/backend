from sqlalchemy.orm import declarative_base

# 'Base' es la clase fundamental de la cual todos los modelos ORM de SQLAlchemy heredarán.
# Permite a SQLAlchemy mapear las clases Python a tablas de la base de datos.
Base = declarative_base()

# Cuando definas tus modelos (ej. Usuario, Producto), harás algo como:
# class Usuario(Base):
#     __tablename__ = "usuarios"
#     # ... define columnas ...

