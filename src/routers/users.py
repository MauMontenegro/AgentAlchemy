from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.db_connection import AsyncSessionLocal
from src.services import user_crud as crud
from src.schemas.db_schemas import UserCreate, UserOut
from src.routers.auth_route import require_admin  # Importar la función
from typing import List


router = APIRouter()

# Dependency para obtener sesión DB
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/users/", response_model=UserOut)
async def create_user(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),
    admin: UserOut = Depends(require_admin)
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
    except HTTPException:
        # Re-raise HTTP exceptions as they already have status codes
        raise
    except Exception as e:
        # Log the error (in a real app, use a proper logger)
        print(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

@router.get("/users/", response_model=List[UserOut])
async def read_users(
    db: AsyncSession = Depends(get_db),
    admin: UserOut = Depends(require_admin)
):
    return await crud.get_users(db)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    admin: UserOut = Depends(require_admin)  # ← Agregar esto
):
    success = await crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}

@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_data: dict,
    db: AsyncSession = Depends(get_db),
    admin: UserOut = Depends(require_admin)  # ← Agregar esto
):
    updated_user = await crud.update_user(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user
