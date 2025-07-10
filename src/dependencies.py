from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
import logging
import os
from datetime import datetime

from src.services.db_connection import AsyncSessionLocal
from src.models.models import User

# Configure logging
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Use the same path as defined in the auth router
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        # Validate SECRET_KEY is available
        if not SECRET_KEY:
            logger.error("SECRET_KEY is not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication system misconfigured"
            )
            
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")            
            
    except JWTError as e:
        # Log the specific JWT error
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    try:
        # Buscar usuario
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        return user
    except Exception as e:
        # Log database errors
        logger.error(f"Database error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )

# Admin role requirement
async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user