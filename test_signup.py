#!/usr/bin/env python3
"""
Script para probar el registro y login de usuarios
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup(username, email, password):
    """Probar el registro de usuario"""
    signup_url = f"{BASE_URL}/signup/users/"
    
    payload = {
        "username": username,
        "email": email,
        "password": password
    }
    
    try:
        print(f"Registrando usuario: {username}")
        response = requests.post(signup_url, json=payload)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Usuario registrado exitosamente!")
            print(f"   - ID: {user_data['id']}")
            print(f"   - Username: {user_data['username']}")
            print(f"   - Email: {user_data['email']}")
            print(f"   - Role: {user_data['role']}")
            return True
        else:
            print(f"❌ Error en registro: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error durante registro: {str(e)}")
        return False

def test_login(username, password):
    """Probar el login de usuario"""
    login_url = f"{BASE_URL}/auth/token"
    
    try:
        print(f"Intentando login con usuario: {username}")
        response = requests.post(
            login_url,
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login exitoso!")
            print(f"   - Token: {token_data['access_token'][:20]}...")
            print(f"   - User: {token_data['user']['username']}")
            return token_data["access_token"]
        else:
            print(f"❌ Error en login: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error durante login: {str(e)}")
        return None

def main():
    print("=== Prueba de Registro y Login ===")
    
    # Datos de prueba
    test_username = "testuser123"
    test_email = "testuser123@example.com"
    test_password = "testpass123"
    
    # 1. Probar registro
    print("\\n1. Probando registro...")
    signup_success = test_signup(test_username, test_email, test_password)
    
    if not signup_success:
        print("❌ No se pudo completar el registro")
        return
    
    # 2. Probar login
    print("\\n2. Probando login...")
    token = test_login(test_username, test_password)
    
    if token:
        print("\\n✅ Proceso completo exitoso!")
    else:
        print("\\n❌ Login falló después del registro")

if __name__ == "__main__":
    main()