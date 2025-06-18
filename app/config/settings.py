from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Define la configuración de la aplicación utilizando Pydantic BaseSettings.
    Permite cargar configuraciones desde variables de entorno y archivos .env.
    """
    # --- Configuración General de la Aplicación ---
    app_name: str = "API Olimpiadas"  # Nombre descriptivo de la aplicación.
    app_version: str = "1.0.0"  # Versión actual de la API.
    
    # --- Configuración del Servicio de Correo Electrónico (SMTP con Gmail) ---
    # IMPORTANTE: Para 'app_password', se recomienda usar una contraseña de aplicación generada por Google,
    # no la contraseña principal de la cuenta de Gmail.
    app_password: str = 'ykhj uzeu yztv pmfe'  # Contraseña de aplicación para la cuenta de envío.
    sender_email: str = 'losdelfondo7moetp@gmail.com'  # Dirección de correo electrónico desde la que se enviarán los correos.
    recipients: List[str] = ['losdelfondo7moetp@gmail.com', 'noahchamo@gmail.com'] # Lista de destinatarios para notificaciones o pruebas.
    
    # --- Configuración de la Base de Datos ---
    # URL de conexión para la base de datos PostgreSQL. Sigue el formato estándar:
    # postgresql://usuario:contraseña@host:puerto/nombre_basedatos
    database_url: str = "postgresql://losdelfondosql_user:PvDDXaQUDSmRWaa4yL3Fq2zC1BkmRtAn@dpg-d16b2kumcj7s73bv3peg-a.oregon-postgres.render.com:5432/losdelfondosql?client_encoding=utf8"
    
    # --- Configuración de JSON Web Tokens (JWT) para Autenticación ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Duración (en minutos) de la validez de un token de acceso.
    SECRET_KEY: str = "K#@p2X!vR7zY$qE9&bN*sW" # ¡CRÍTICO! Clave secreta para firmar los JWT. DEBE CAMBIARSE y gestionarse de forma segura (ej. variable de entorno).
    ALGORITHM: str = "HS256" # Algoritmo utilizado para la firma de los JWT (ej. HS256, RS256).
    
    # Configuración del modelo Pydantic para cargar variables de entorno.
    model_config = {
        "env_file": ".env", # Nombre del archivo .env a cargar (si existe).
        "env_file_encoding": "utf-8" # Codificación del archivo .env.
    }
    
    # Nota: 'access_token_expire_minutes' parece ser un duplicado de 'ACCESS_TOKEN_EXPIRE_MINUTES'.
    # Considerar eliminar uno para evitar confusión, a menos que tenga un propósito específico.
    access_token_expire_minutes: int = 30 
    
    # --- Configuración de API de Gmail (si se usa OAuth2 para enviar correos) ---
    # Alcances (scopes) que la aplicación solicitará para acceder a la API de Gmail.
    # 'gmail.send' permite enviar correos en nombre del usuario autenticado.
    gmail_scopes: List[str] = ["https://www.googleapis.com/auth/gmail.send"]

# Crea una instancia global de la configuración para que pueda ser importada y utilizada
# fácilmente en otros módulos de la aplicación.
settings = Settings()