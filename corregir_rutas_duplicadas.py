import mysql.connector
import os

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'sistema_ganadero'
}

def corregir_rutas_duplicadas():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todas las rutas de imágenes
        cursor.execute("SELECT id, numero_arete, nombre, foto_path FROM animales")
        animales = cursor.fetchall()
        
        print(f"Total de animales en la base de datos: {len(animales)}")
        contador = 0
        
        for animal in animales:
            animal_id = animal['id']
            ruta_actual = animal['foto_path']
            
            if not ruta_actual:
                continue
                
            ruta_corregida = None
            
            # Corregir rutas duplicadas con 'static//static/'
            if 'static//static/' in ruta_actual:
                ruta_corregida = ruta_actual.replace('static//static/', 'static/')
            
            # Corregir rutas que comienzan con '/static/'
            elif ruta_actual.startswith('/static/'):
                ruta_corregida = ruta_actual[1:]  # Eliminar la barra inicial
            
            # Si se necesita corregir la ruta
            if ruta_corregida:
                print(f"Corrigiendo ruta para animal ID {animal_id}:")
                print(f"  Ruta original: {ruta_actual}")
                print(f"  Ruta corregida: {ruta_corregida}")
                
                # Actualizar la ruta en la base de datos
                cursor.execute(
                    "UPDATE animales SET foto_path = %s WHERE id = %s",
                    (ruta_corregida, animal_id)
                )
                contador += 1
        
        conn.commit()
        print(f"\nSe corrigieron {contador} rutas de imágenes")
        
    except Exception as e:
        print(f"Error al corregir las rutas duplicadas: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    corregir_rutas_duplicadas()
