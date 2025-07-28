#!/usr/bin/env python3
"""
Script para crear un usuario admin inicial en Aurora RDS
"""
import asyncio
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

load_dotenv()

from src.services.db_connection import AsyncSessionLocal
from src.models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    """Crear usuario admin inicial"""
    username = "maumont92"
    email = "m.montenegro.meza@gmail.com"
    password = "1492plcaz!"  # Cambiar después del primer login
    
    async with AsyncSessionLocal() as db:
        try:
            # Verificar si ya existe
            result = await db.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"Usuario ya existe")
                return
            
            # Crear usuario admin
            hashed_password = pwd_context.hash(password)
            admin_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role="admin"
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            print(f"✅ Usuario admin creado:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Email: {email}")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())