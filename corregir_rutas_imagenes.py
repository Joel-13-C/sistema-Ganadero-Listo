import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'sistema_ganadero'
}

def corregir_rutas_imagenes():
    # Intentar diferentes configuraciones de conexión
    conexiones_a_probar = [
        {"host": "localhost", "user": "root", "password": ""},
        {"host": "localhost", "user": "root", "password": "root"},
        {"host": "localhost", "user": "root", "password": "admin"},
        {"host": "localhost", "user": "root", "password": "1234"},
        {"host": "localhost", "user": "admin", "password": "admin"}
    ]
    
    conn = None
    for config in conexiones_a_probar:
        try:
            print(f"Intentando conectar con: {config}")
            conn = mysql.connector.connect(
                **config,
                database="sistema_ganadero"
            )
            if conn.is_connected():
                print(f"Conexión exitosa con: {config}")
                break
        except Exception as e:
            print(f"Error al conectar con: {config}. Error: {e}")
            continue
    
    if not conn or not conn.is_connected():
        print("Error: No se pudo conectar a la base de datos")
        return
        
    cursor = conn.cursor()
    
    try:
        # Obtener todas las rutas de imágenes
        cursor.execute("SELECT id, foto_path FROM animales WHERE foto_path IS NOT NULL")
        animales = cursor.fetchall()
        
        contador = 0
        for animal_id, foto_path in animales:
            if foto_path and not foto_path.startswith('static/'):
                # Corregir la ruta para que incluya el prefijo 'static/'
                if foto_path.startswith('uploads/'):
                    nueva_ruta = f'static/{foto_path}'
                elif foto_path.startswith('images/'):
                    nueva_ruta = f'static/{foto_path}'
                else:
                    nueva_ruta = foto_path  # Mantener igual si no coincide con los patrones conocidos
                
                # Actualizar la ruta en la base de datos
                cursor.execute(
                    "UPDATE animales SET foto_path = %s WHERE id = %s",
                    (nueva_ruta, animal_id)
                )
                contador += 1
        
        conn.commit()
        print(f"Se corrigieron {contador} rutas de imágenes")
        
    except Exception as e:
        print(f"Error al corregir las rutas de imágenes: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    corregir_rutas_imagenes()
