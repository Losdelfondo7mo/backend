# Este archivo __init__.py facilita la importación de funciones o clases de servicio.
# Permite importar directamente desde 'app.services'.
# Ejemplo: from app.services import send_email_smtp

from .email_service import send_email_smtp, send_email_gmail_api #, obtener_mensaje_registro, obtener_mensaje_compra
# Las funciones obtener_mensaje_* podrían ser privadas del módulo email_service si solo se usan allí.