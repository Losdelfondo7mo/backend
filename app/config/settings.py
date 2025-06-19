from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # --- Configuración General de la Aplicación ---
    app_name: str = "API Olimpiadas"
    app_version: str = "1.0.0"
    
    # --- Configuración del Servicio de Correo Electrónico ---
    app_password: str  # Remove default, use env var
    sender_email: str = 'losdelfondo7moetp@gmail.com'
    recipients: List[str] = ['losdelfondo7moetp@gmail.com', 'noahchamo@gmail.com']
    
    # --- Configuración de la Base de Datos ---
    database_url: str  # Remove default, use env var
    
    # --- Configuración JWT ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str  # Remove default, use env var
    ALGORITHM: str = "HS256"
    
    # --- Configuración OAuth ---
    google_client_id: str  # Remove default, use env var
    google_client_secret: str  # Remove default, use env var
    github_client_id: str  # Remove default, use env var
    github_client_secret: str  # Remove default, use env var
    discord_client_id: str  # Remove default, use env var
    discord_client_secret: str  # Remove default, use env var
    
    oauth_redirect_base_url: str = "http://localhost:8000"
    
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