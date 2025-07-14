import mysql.connector
from mysql.connector import Error

def verificar_tablas():
    connection = None
    try:
        # Establecer conexión
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Contraseña vacía según .env
            database='sistema_ganadero'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Verificar si existen las tablas
            cursor.execute("SHOW TABLES")
            tablas = cursor.fetchall()
            print("Tablas existentes:")
            for tabla in tablas:
                print(tabla[0])
            
            # Verificar estructura de la tabla carbunco
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'sistema_ganadero'
                AND TABLE_NAME = 'carbunco'
            """)
            columnas = cursor.fetchall()
            print("\nEstructura de la tabla carbunco:")
            for columna in columnas:
                print(f"{columna[0]} - {columna[1]} - Nullable: {columna[2]} - Key: {columna[3]}")

    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    verificar_tablas()
