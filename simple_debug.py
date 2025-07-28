#!/usr/bin/env python3
"""
Script simple para diagnosticar problemas de autenticación
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_env_variables():
    """Verificar variables de entorno"""
    print("=== Verificando variables de entorno ===")
    
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM")
    expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    
    print(f"SECRET_KEY: {'OK' if secret_key else 'ERROR'} ({len(secret_key) if secret_key else 0} chars)")
    print(f"ALGORITHM: {'OK' if algorithm else 'ERROR'} ({algorithm})")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {'OK' if expire_minutes else 'ERROR'} ({expire_minutes})")
    
    # Verificar si hay problemas con el parsing
    if expire_minutes:
        try:
            parsed_minutes = int(expire_minutes.split("#")[0].strip())
            print(f"   - Parsed value: {parsed_minutes}")
        except Exception as e:
            print(f"   - ERROR parsing: {str(e)}")
            return False
    
    return secret_key and algorithm and expire_minutes

def main():
    print("Diagnostico Simple de Autenticacion")
    print("=" * 50)
    
    # Verificar variables de entorno
    env_ok = check_env_variables()
    
    if not env_ok:
        print("\nERROR: Hay problemas con las variables de entorno")
        print("\nSoluciones sugeridas:")
        print("1. Verificar que el archivo .env existe y tiene las variables correctas")
        print("2. Verificar que ACCESS_TOKEN_EXPIRE_MINUTES no tiene comentarios inline")
        return False
    
    print("\nOK: Variables de entorno estan correctas")
    return True

if __name__ == "__main__":
    main()