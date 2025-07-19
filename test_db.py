#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a la base de datos PostgreSQL
"""

import pg8000
from urllib.parse import urlparse
import sys

def test_db_connection():
    """Prueba la conexión a la base de datos PostgreSQL"""
    try:
        # URL de conexión
        db_url = "postgresql://ganadero_anwt_user:rOsqRSS6jlrJ6UiEQzj7HM2G5CAb0eBb@dpg-d1tg58idbo4c73dieh30-a.oregon-postgres.render.com/ganadero_anwt"
        
        print("🔍 Probando conexión a PostgreSQL...")
        print(f"URL: {db_url}")
        
        # Parsear la URL de conexión
        parsed = urlparse(db_url)
        
        print(f"Host: {parsed.hostname}")
        print(f"Puerto: {parsed.port or 5432}")
        print(f"Usuario: {parsed.username}")
        print(f"Base de datos: {parsed.path[1:] if parsed.path else 'ganadero_anwt'}")
        
        # Configuración de SSL para Render
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Intentar establecer la conexión
        connection = pg8000.Connection(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else 'ganadero_anwt',
            ssl_context=ssl_context
        )
        
        print("✅ Conexión establecida exitosamente!")
        
        # Probar una consulta simple
        cursor = connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ Versión de PostgreSQL: {version[0]}")
        
        # Probar acceso a las tablas principales
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"✅ Tablas disponibles: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Probar consulta a usuarios
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        user_count = cursor.fetchone()
        print(f"✅ Usuarios en la base de datos: {user_count[0]}")
        
        # Probar consulta a animales
        cursor.execute("SELECT COUNT(*) FROM animales")
        animal_count = cursor.fetchone()
        print(f"✅ Animales en la base de datos: {animal_count[0]}")
        
        cursor.close()
        connection.close()
        print("✅ Conexión cerrada correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba de conexión a la base de datos...")
    success = test_db_connection()
    
    if success:
        print("\n🎉 ¡Prueba completada exitosamente!")
        sys.exit(0)
    else:
        print("\n💥 ¡Prueba falló!")
        sys.exit(1) 