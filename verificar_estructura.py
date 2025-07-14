from src.database import get_db_connection

def verificar_estructura():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener la estructura de la tabla animales
        cursor.execute("""
            DESCRIBE animales
        """)
        columnas = cursor.fetchall()
        print("\nEstructura de la tabla animales:")
        for columna in columnas:
            print(f"Campo: {columna['Field']}, Tipo: {columna['Type']}")
        
        # Obtener algunos registros de ejemplo
        cursor.execute("""
            SELECT *
            FROM animales
            LIMIT 3
        """)
        animales = cursor.fetchall()
        print("\nEjemplos de registros:")
        for animal in animales:
            print("\nAnimal:")
            for key, value in animal.items():
                print(f"{key}: {value}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al verificar estructura: {e}")

if __name__ == "__main__":
    verificar_estructura()
