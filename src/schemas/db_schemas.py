from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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