import mysql.connector

def actualizar_inseminaciones():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='sistema_ganadero'
        )
        
        # Crear un cursor
        cursor = conn.cursor()
        
        # Actualizar los registros existentes con valores para los campos faltantes
        query = """
        UPDATE inseminaciones 
        SET raza_semental = 'Holstein', 
            codigo_pajuela = 'COD-001', 
            inseminador = 'Juan Pérez' 
        WHERE raza_semental = '' OR raza_semental IS NULL
        """
        
        cursor.execute(query)
        
        # Confirmar los cambios
        conn.commit()
        
        # Mostrar cuántos registros se actualizaron
        print(f"Registros actualizados: {cursor.rowcount}")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    actualizar_inseminaciones()
