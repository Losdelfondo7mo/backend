from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCrear(CategoriaBase):
    pass

class CategoriaMostrar(CategoriaBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)