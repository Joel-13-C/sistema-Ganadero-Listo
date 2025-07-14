from src.database import get_db_connection

def verificar_tabla(nombre_tabla):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"DESCRIBE {nombre_tabla}")
        columnas = cursor.fetchall()
        
        print(f"\n=== COLUMNAS DE LA TABLA '{nombre_tabla}' ===")
        for col in columnas:
            print(f"Columna: {col['Field']}, Tipo: {col['Type']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al verificar la tabla {nombre_tabla}: {str(e)}")

if __name__ == "__main__":
    verificar_tabla("gestaciones")
