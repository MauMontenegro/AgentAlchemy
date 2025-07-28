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
        # Check if user already exists
        from sqlalchemy import select
        from src.models.models import User
        
        result = await db.execute(
            select(User).where(
                (User.email == user.email) | (User.username == user.username)
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.email == user.email:
                raise HTTPException(status_code=400, detail="Email already registered")
            else:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        return await crud.create_user(db, user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to signup")
