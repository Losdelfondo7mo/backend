from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UsuarioLogin(BaseModel):
    """
    Esquema para el login de usuario.
    Contiene solo los campos necesarios para autenticación.
    """
    usuario: str  # Nombre de usuario
    contraseña: str  # Contraseña en texto plano

class UsuarioBase(BaseModel):
    """
    Esquema base para un usuario. Define los campos comunes.
    No incluye información sensible como contraseñas ni el rol.
    """
    email: EmailStr # El correo electrónico del usuario, validado como formato de email.
    usuario: str    # El nombre de usuario para el login.
    nombre: Optional[str] = None # Nombre real del usuario, opcional.
    apellido: Optional[str] = None # Apellido del usuario, opcional.
    contraseña: Optional[str] = None

class UsuarioCrear(UsuarioBase):
    """
    Esquema para la creación de un usuario.
    Hereda de `UsuarioBase` y añade el campo `contraseña`.
    """
    email: EmailStr # El correo electrónico del usuario, validado como formato de email.
    usuario: str    # El nombre de usuario para el login.
    nombre: Optional[str] = None # Nombre real del usuario, opcional.
    apellido: Optional[str] = None # Apellido del usuario, opcional.
    contraseña: Optional[str] = None
    
class UsuarioPublic(BaseModel):
    """Esquema para mostrar la información pública de un usuario."""
    id: int
    email: EmailStr
    usuario: str
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    rol: Optional[str] = "usuario"
    
    model_config = ConfigDict(from_attributes=True)

class Usuario(UsuarioBase):
    """
    Esquema completo para un usuario, incluyendo su ID y rol.
    Podría usarse para respuestas donde se necesita toda la información pública del usuario.
    """
    id: int
    rol: Optional[str] = "usuario" # Rol del usuario
    
    model_config = ConfigDict(from_attributes=True)

class UsuarioActualizarRol(BaseModel):
    """
    Esquema para actualizar el rol de un usuario.
    Solo permite cambiar el rol.
    """
    rol: str # Nuevo rol: 'usuario' o 'administrador'

class AdminCrear(BaseModel):
    """
    Esquema específico para crear un administrador.
    Incluye todos los campos necesarios y establece el rol como administrador.
    """
    email: EmailStr
    usuario: str
    nombre: str
    apellido: str
    contraseña: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@ejemplo.com",
                "usuario": "admin",
                "nombre": "Administrador",
                "apellido": "Sistema",
                "contraseña": "contraseña_segura"
            }
        }

class CambiarContraseña(BaseModel):
    """
    Esquema para cambiar la contraseña de un usuario.
    """
    contraseña_actual: str # Contraseña actual del usuario
    contraseña_nueva: str # Nueva contraseña
    confirmar_contraseña: str # Confirmación de la nueva contraseña

class EstadisticasUsuarios(BaseModel):
    """
    Esquema para mostrar estadísticas de usuarios.
    """
    total_usuarios: int
    usuarios_activos: int
    administradores: int
    usuarios_regulares: int

class EstadisticasVisitas(BaseModel):
    """
    Esquema para mostrar estadísticas de visitas.
    """
    total_visitas: int
    visitas_hoy: int
    visitas_esta_semana: int
    visitas_este_mes: int
    # Eliminar esta clase Config
    # class Config:
    #     orm_mode = True