from pydantic import BaseModel, EmailStr

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