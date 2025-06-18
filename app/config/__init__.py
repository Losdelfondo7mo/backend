# Importa la instancia de configuración 'settings' para que esté disponible
# directamente desde el paquete 'app.config'.
# Esto permite un acceso más sencillo a la configuración desde otros módulos.
# Ejemplo de uso: from app.config import settings
from .settings import settings

# Define qué símbolos se exportarán cuando se utilice 'from app.config import *'.
# En este caso, solo se exporta la instancia 'settings'.
__all__ = ["settings"]