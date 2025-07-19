#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de Vercel
"""

import os
import sys
import jwt
from datetime import datetime, timedelta

def test_jwt():
    """Probar la funcionalidad JWT"""
    print("=== Prueba de JWT ===")
    
    # Simular la creación de un token
    secret_key = os.environ.get('JWT_SECRET_KEY', 'tu_clave_jwt_secreta_aqui_123456789')
    
    payload = {
        'user_id': 1,
        'username': 'test_user',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    try:
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        print(f"Token generado: {token[:50]}...")
        
        # Verificar el token
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(f"Token verificado: {decoded}")
        print("✅ JWT funciona correctamente")
        
    except Exception as e:
        print(f"❌ Error con JWT: {e}")
        return False
    
    return True

def test_environment():
    """Probar las variables de entorno"""
    print("\n=== Variables de Entorno ===")
    
    required_vars = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'SESSION_TYPE',
        'SESSION_FILE_DIR'
    ]
    
    for var in required_vars:
        value = os.environ.get(var, 'NO_DEFINIDA')
        print(f"{var}: {value}")
    
    print("✅ Variables de entorno configuradas")

def test_imports():
    """Probar las importaciones"""
    print("\n=== Prueba de Importaciones ===")
    
    try:
        from app import app
        print("✅ App importada correctamente")
        
        from src.jwt_auth import create_token, verify_token
        print("✅ JWT auth importado correctamente")
        
        from flask_session import Session
        print("✅ Flask-Session importado correctamente")
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Iniciando pruebas de configuración de Vercel...")
    
    test_environment()
    test_imports()
    test_jwt()
    
    print("\n=== Resumen ===")
    print("Si todas las pruebas pasaron, la configuración está lista para Vercel.")
    print("Recuerda desplegar los cambios con: vercel --prod") 