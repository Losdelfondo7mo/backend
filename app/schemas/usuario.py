from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UsuarioBase(BaseModel):
    """
    Esquema base para un usuario. Define los campos comunes.
    No incluye información sensible como contraseñas.
    """
    email: EmailStr # El correo electrónico del usuario, validado como formato de email.
    usuario: str    # El nombre de usuario para el login.
    nombre: Optional[str] = None # Nombre real del usuario, opcional.
    apellido: Optional[str] = None # Apellido del usuario, opcional.

class UsuarioCrear(UsuarioBase):
    """
    Esquema utilizado para la creación de un nuevo usuario.
    Hereda de `UsuarioBase` y añade el campo `contraseña`.
    """
    contraseña: str # Contraseña en texto plano proporcionada al crear el usuario.

class UsuarioPublic(UsuarioBase):
    """
    Esquema para mostrar la información pública de un usuario.
    Hereda de `UsuarioBase` y añade el `id`.
    Crucialmente, NO incluye la contraseña ni su hash.
    """
    id: int # Identificador único del usuario.

    # Configuración para Pydantic v2. 'from_attributes=True' permite la creación
    # del esquema a partir de un modelo ORM de SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)


# El esquema UsuarioVerificar podría ser útil para un endpoint de login si no se usa OAuth2PasswordRequestForm
# o para otros propósitos de verificación, pero el endpoint de login actual usa OAuth2PasswordRequestForm.
# class UsuarioVerificar(BaseModel):
#     """
#     Esquema para verificar las credenciales de un usuario (ej. en un login personalizado).
#     """
#     usuario: str
#     contraseña: str

class Usuario(UsuarioBase):
    """
    Esquema completo para un usuario, incluyendo su ID.
    Podría usarse para respuestas donde se necesita toda la información pública del usuario.
    Similar a UsuarioPublic, pero definido explícitamente.
    """
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    # Eliminar esta clase Config
    # class Config:
    #     orm_mode = True