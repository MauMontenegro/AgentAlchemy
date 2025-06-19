from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from src.models.models import User
from src.schemas.db_schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(db: AsyncSession, user: UserCreate):
    try:
        # Hash the password before storing
        hashed_password = pwd_context.hash(user.password)
        
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password  # Make sure your User model has this field
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        await db.rollback()
        # Re-raise with more context
        raise Exception(f"Failed to create user: {str(e)}") from e    
    

async def get_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
        return True
    return False

# src/services/user_crud.py
async def update_user(db: AsyncSession, user_id: int, user_data: dict):
    from sqlalchemy import select
    
    # Buscar el usuario
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Actualizar campos
    if "username" in user_data:
        user.username = user_data["username"]
    
    if "email" in user_data:
        user.email = user_data["email"]
    
    if "password" in user_data and user_data["password"]:
        # Importa tu función get_password_hash de donde la tengas
        from src.routers.auth_route import get_password_hash
        user.hashed_password = get_password_hash(user_data["password"])
    
    if "role" in user_data:
        user.role = user_data["role"]
    
    await db.commit()
    await db.refresh(user)
    
    return user

