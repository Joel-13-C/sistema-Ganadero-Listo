import mysql.connector
import os

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'sistema_ganadero'
}

def verificar_rutas_imagenes():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todas las rutas de imágenes
        cursor.execute("SELECT id, numero_arete, nombre, foto_path FROM animales")
        animales = cursor.fetchall()
        
        print(f"Total de animales en la base de datos: {len(animales)}")
        print("\nRutas de imágenes en la base de datos:")
        print("-" * 80)
        
        for animal in animales:
            ruta_bd = animal['foto_path']
            ruta_completa = None
            
            if ruta_bd:
                # Construir la ruta completa
                ruta_completa = os.path.join("C:\\Users\\JOEL\\CascadeProjects\\SistemaGanadero", ruta_bd.replace('/', '\\'))
                existe = os.path.exists(ruta_completa)
            else:
                existe = False
            
            print(f"ID: {animal['id']}, Arete: {animal['numero_arete']}, Nombre: {animal['nombre']}")
            print(f"Ruta en BD: {ruta_bd}")
            print(f"Ruta completa: {ruta_completa}")
            print(f"¿Existe el archivo?: {'Sí' if existe else 'No'}")
            print("-" * 80)
        
    except Exception as e:
        print(f"Error al verificar las rutas de imágenes: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    verificar_rutas_imagenes()
