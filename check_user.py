#!/usr/bin/env python3
"""
Script para verificar usuarios en la base de datos
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.services.db_connection import AsyncSessionLocal
from src.models.models import User

async def check_user_exists(username):
    """Verificar si un usuario existe"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ Usuario '{username}' encontrado:")
                print(f"   - ID: {user.id}")
                print(f"   - Email: {user.email}")
                print(f"   - Role: {user.role}")
                print(f"   - Hash: {user.hashed_password[:50]}...")
                return user
            else:
                print(f"❌ Usuario '{username}' no encontrado")
                return None
        except Exception as e:
            print(f"❌ Error consultando usuario: {str(e)}")
            return None

async def list_all_users():
    """Listar todos los usuarios"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            print(f"\\n📋 Total de usuarios: {len(users)}")
            for user in users:
                print(f"   - {user.username} ({user.email}) - Role: {user.role}")
            
            return users
        except Exception as e:
            print(f"❌ Error listando usuarios: {str(e)}")
            return []

async def test_db_connection():
    """Probar conexión a la base de datos"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos exitosa")
            return True
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")
            return False

async def main():
    print("=== Verificación de Usuarios ===")
    
    # 1. Probar conexión
    print("\\n1. Probando conexión a la base de datos...")
    if not await test_db_connection():
        return
    
    # 2. Listar todos los usuarios
    print("\\n2. Listando todos los usuarios...")
    await list_all_users()
    
    # 3. Verificar usuario específico
    print("\\n3. Verificando usuario 'maumont92'...")
    await check_user_exists("maumont92")

if __name__ == "__main__":
    asyncio.run(main())