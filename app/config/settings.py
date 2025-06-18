from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Configuración de la aplicación
    app_name: str = "API Olimpiadas"
    app_version: str = "1.0.0"
    
    # Configuración de correo
    app_password: str = 'ykhj uzeu yztv pmfe'
    sender_email: str = 'losdelfondo7moetp@gmail.com'
    recipients: List[str] = ['losdelfondo7moetp@gmail.com', 'noahchamo@gmail.com']
    
    # Configuración de base de datos
    database_url: str = "postgresql://losdelfondosql_user:PvDDXaQUDSmRWaa4yL3Fq2zC1BkmRtAn@dpg-d16b2kumcj7s73bv3peg-a.oregon-postgres.render.com:5432/losdelfondosql?client_encoding=utf8"
    
    # Configuración de JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # por ejemplo, 30 minutos
    SECRET_KEY: str = "tu_super_secreto_aqui" # Asegúrate de que esta también exista y sea segura
    ALGORITHM: str = "HS256" # Asegúrate de que esta también exista
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    access_token_expire_minutes: int = 30
    
    # Scopes para Gmail API
    gmail_scopes: List[str] = ["https://www.googleapis.com/auth/gmail.send"]

settings = Settings()