from fastapi import APIRouter, HTTPException,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.db_connection import AsyncSessionLocal
from src.schemas.db_schemas import UserCreate, UserOut
from src.services import user_crud as crud

router = APIRouter()

# Dependency para obtener sesión DB
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/users/", response_model=UserOut)
async def signup_user(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),    
):
    try:
        # Check if user with same email already exists
        existing_users = await crud.get_users(db)
        if any(u.email == user.email for u in existing_users):
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        return await crud.create_user(db, user)    
    except Exception as e:
        # Log the error (in a real app, use a proper logger)
        print(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to signup"
        )
