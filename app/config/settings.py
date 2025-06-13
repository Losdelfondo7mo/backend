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
    secret_key: str = "c67d978e20f38a9a00db5e4e60de978d93e0e3031b18e6c248e928bd3b9fad5b"
    algorithm: str = "HS256"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    access_token_expire_minutes: int = 30
    
    # Scopes para Gmail API
    gmail_scopes: List[str] = ["https://www.googleapis.com/auth/gmail.send"]

settings = Settings()