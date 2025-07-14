from src.database import get_db_connection
import sys

def describir_tabla(nombre_tabla):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener la estructura de la tabla
        cursor.execute(f"DESCRIBE {nombre_tabla}")
        columnas = cursor.fetchall()
        
        print(f"\n=== ESTRUCTURA DE LA TABLA '{nombre_tabla}' ===")
        for col in columnas:
            print(f"Columna: {col['Field']}, Tipo: {col['Type']}, Nulo: {col['Null']}, Clave: {col['Key']}, Default: {col['Default']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al describir la tabla {nombre_tabla}: {str(e)}")

if __name__ == "__main__":
    # Tablas a verificar
    tablas = ["gestaciones", "vacunaciones", "vacuna"]
    
    for tabla in tablas:
        describir_tabla(tabla)
