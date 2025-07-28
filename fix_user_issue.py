#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import select, delete, text

load_dotenv()

from src.services.db_connection import AsyncSessionLocal
from src.models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def fix_and_create_user():
    async with AsyncSessionLocal() as db:
        try:
            # 1. Verificar usuarios existentes
            result = await db.execute(select(User))
            users = result.scalars().all()
            print(f"Usuarios encontrados: {len(users)}")
            
            # 2. Limpiar usuarios duplicados/problemáticos
            await db.execute(delete(User).where(User.email == "m.montenegro.meza@gmail.com"))
            await db.commit()
            print("Usuarios con email duplicado eliminados")
            
            # 3. Crear usuario limpio
            hashed_password = pwd_context.hash("1492plcaz!")
            new_user = User(
                username="maumont92",
                email="m.montenegro.meza@gmail.com",
                hashed_password=hashed_password,
                role="admin"
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print("✅ Usuario creado exitosamente:")
            print(f"   Username: maumont92")
            print(f"   Email: m.montenegro.meza@gmail.com")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(fix_and_create_user())