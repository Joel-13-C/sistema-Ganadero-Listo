from src.database import get_db_connection

def verificar_animales():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si hay animales en la base de datos
        cursor.execute("SELECT COUNT(*) as total FROM animales")
        total = cursor.fetchone()['total']
        print(f"Total de animales en la base de datos: {total}")
        
        if total > 0:
            # Mostrar algunos animales de ejemplo
            cursor.execute("SELECT * FROM animales LIMIT 5")
            animales = cursor.fetchall()
            print("\nEjemplos de animales:")
            for animal in animales:
                print(f"ID: {animal['id']}, Identificación: {animal['identificacion']}, Categoría: {animal['categoria']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al verificar animales: {e}")

if __name__ == "__main__":
    verificar_animales()
