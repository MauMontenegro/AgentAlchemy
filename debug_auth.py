#!/usr/bin/env python3
"""
Script para diagnosticar problemas de autenticación
"""
import asyncio
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Cargar variables de entorno
load_dotenv()

# Importar modelos y servicios
from src.services.db_connection import AsyncSessionLocal
from src.models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def check_user_password(username: str, plain_password: str):
    """Verificar si la contraseña del usuario es correcta"""
    async with AsyncSessionLocal() as db:
        # Buscar usuario
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return False
            
        print(f"✅ Usuario '{username}' encontrado")
        print(f"   - Email: {user.email}")
        print(f"   - Role: {user.role}")
        print(f"   - Hash almacenado: {user.hashed_password[:50]}...")
        
        # Verificar contraseña
        is_valid = pwd_context.verify(plain_password, user.hashed_password)
        print(f"   - Contraseña válida: {'✅' if is_valid else '❌'}")
        
        return is_valid

async def create_test_user(username: str, email: str, password: str):
    """Crear un usuario de prueba"""
    async with AsyncSessionLocal() as db:
        try:
            # Verificar si ya existe
            result = await db.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Usuario '{username}' ya existe")
                return existing_user
            
            # Crear nuevo usuario
            hashed_password = pwd_context.hash(password)
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role="user"
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print(f"✅ Usuario '{username}' creado exitosamente")
            return new_user
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error creando usuario: {str(e)}")
            return None

def check_env_variables():
    """Verificar variables de entorno"""
    print("=== Verificando variables de entorno ===")
    
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM")
    expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    
    print(f"SECRET_KEY: {'✅' if secret_key else '❌'} ({len(secret_key) if secret_key else 0} chars)")
    print(f"ALGORITHM: {'✅' if algorithm else '❌'} ({algorithm})")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {'✅' if expire_minutes else '❌'} ({expire_minutes})")
    
    # Verificar si hay problemas con el parsing
    if expire_minutes:
        try:
            parsed_minutes = int(expire_minutes.split("#")[0].strip())
            print(f"   - Parsed value: {parsed_minutes}")
        except Exception as e:
            print(f"   - ❌ Error parsing: {str(e)}")
    
    return secret_key and algorithm and expire_minutes

async def main():
    print("🔍 Diagnóstico de Autenticación")
    print("=" * 50)
    
    # 1. Verificar variables de entorno
    env_ok = check_env_variables()
    if not env_ok:
        print("❌ Problemas con variables de entorno")
        return
    
    print("\n=== Verificando usuario existente ===")
    # 2. Verificar usuario existente
    username = "maumont92"
    password = input(f"Ingresa la contraseña para '{username}': ")
    
    password_ok = await check_user_password(username, password)
    
    if not password_ok:
        print(f"\n=== Creando usuario de prueba ===")
        # 3. Crear usuario de prueba si es necesario
        test_password = "test123"
        await create_test_user("testuser", "test@example.com", test_password)
        
        print(f"\n✅ Usuario de prueba creado:")
        print(f"   - Username: testuser")
        print(f"   - Password: {test_password}")
        print(f"   - Email: test@example.com")

if __name__ == "__main__":
    asyncio.run(main())