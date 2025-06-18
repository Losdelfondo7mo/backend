# Este archivo __init__.py facilita la importación de los modelos SQLAlchemy.
# Permite importar modelos directamente desde 'app.models' en lugar de especificar la ruta completa del módulo.
# Ejemplo: from app.models import UsuarioModel, Producto

from .usuario import UsuarioModel # Modelo para la tabla de usuarios.
from .producto import Producto    # Modelo para la tabla de productos.