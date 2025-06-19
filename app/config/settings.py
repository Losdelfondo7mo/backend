from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # --- Configuración General de la Aplicación ---
    app_name: str = "API Olimpiadas"
    app_version: str = "1.0.0"
    
    # --- Configuración del Servicio de Correo Electrónico ---
    app_password: str  # Sin valor por defecto - debe venir de env
    sender_email: str = 'losdelfondo7moetp@gmail.com'
    recipients: List[str] = ['losdelfondo7moetp@gmail.com', 'noahchamo@gmail.com']
    
    # --- Configuración de la Base de Datos ---
    database_url: str  # Sin valor por defecto - debe venir de env
    
    # --- Configuración JWT ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str  # Sin valor por defecto - debe venir de env
    ALGORITHM: str = "HS256"
    
    # --- Configuración OAuth ---
    google_client_id: str  # Sin valor por defecto - debe venir de env
    google_client_secret: str  # Sin valor por defecto - debe venir de env
    github_client_id: str  # Sin valor por defecto - debe venir de env
    github_client_secret: str  # Sin valor por defecto - debe venir de env
    discord_client_id: str  # Sin valor por defecto - debe venir de env
    discord_client_secret: str  # Sin valor por defecto - debe venir de env
    
    oauth_redirect_base_url: str 
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    
    access_token_expire_minutes: int = 30
    gmail_scopes: List[str] = ["https://www.googleapis.com/auth/gmail.send"]

# Función para obtener la configuración
def get_settings():
    return Settings()

# Crea una instancia global de la configuración para que pueda ser importada y utilizada
# fácilmente en otros módulos de la aplicación.
settings = Settings()