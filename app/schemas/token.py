from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """
    Esquema para la respuesta del token de acceso JWT.
    Contiene el token en sí y su tipo (generalmente 'bearer').
    """
    access_token: str # El token JWT.
    token_type: str   # Tipo de token, comúnmente "bearer".

class TokenData(BaseModel):
    """
    Esquema para los datos contenidos dentro del payload de un token JWT.
    Utilizado para validar y extraer la información del sujeto (username) del token.
    """
    username: Optional[str] = None # El nombre de usuario (subject 'sub') extraído del token. Es opcional en la definición.