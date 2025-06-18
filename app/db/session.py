
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings # Importa la configuración de la aplicación, que incluye la URL de la BD.

# Crea el 'engine' de SQLAlchemy, que es el punto de entrada a la base de datos.
# Utiliza la URL de la base de datos definida en la configuración.
# 'connect_args' puede usarse para pasar parámetros específicos al driver de la base de datos.
# Aquí, se configura 'client_encoding' a 'utf8' para PostgreSQL, asegurando la correcta
# manipulación de caracteres Unicode.
# 'echo=False' controla si SQLAlchemy debe registrar todas las sentencias SQL que ejecuta.
# Ponerlo a True es útil para depuración, pero puede ser verboso en producción.
engine = create_engine(
    settings.database_url,
    connect_args={
        # Para PostgreSQL, la opción de codificación se pasa a menudo así:
        "options": "-c client_encoding=utf8"
    },
    echo=False # Cambiar a True para ver las consultas SQL generadas por SQLAlchemy.
)

# Crea 'SessionLocal', una fábrica para crear nuevas instancias de sesión de SQLAlchemy.
# Estas sesiones son la interfaz para todas las operaciones de base de datos.
# 'autocommit=False' y 'autoflush=False' son configuraciones estándar que dan más control
# sobre cuándo se envían los cambios a la base de datos (generalmente con db.commit()).
# 'bind=engine' asocia esta fábrica de sesiones con nuestro motor de base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Generador de dependencias de FastAPI para gestionar sesiones de base de datos por solicitud.

    Esta función crea una nueva sesión de base de datos (`db`) para cada solicitud entrante
    y se asegura de que la sesión se cierre correctamente después de que la solicitud haya sido procesada,
    incluso si ocurren errores durante el manejo de la solicitud.

    Uso:
        En los endpoints de FastAPI, se inyecta como una dependencia:
        `async def mi_endpoint(db: Session = Depends(get_db)):`

    Yields:
        Session: Una instancia de sesión de SQLAlchemy lista para ser usada.
    """
    db = SessionLocal() # Crea una nueva sesión de base de datos.
    try:
        yield db # Proporciona la sesión al código del endpoint.
    finally:
        db.close() # Cierra la sesión cuando el endpoint ha terminado, liberando la conexión.