# Este modulo contiene los esquemas de validación para los objetos de la base de datos

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Usuarios del Sistema
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str    

class UserOut(BaseModel):
    id:int
    username: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


# Contextos creados por el usuario para Petroil-GPT
class ContextCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ContextUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ContextOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# Esquemas Generados dinámicamente por el usuario para formatos de OCR 
class SchemaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schema_data: str

class SchemaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_data: Optional[str] = None

class SchemaOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    schema_data: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True