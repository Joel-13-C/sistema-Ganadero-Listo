import mysql.connector
from mysql.connector import Error

def reconstruir_tabla_registro_leche():
    """
    Elimina y reconstruye la tabla de registro_leche desde cero
    """
    # Configuraciones de conexión a probar
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
            conn = mysql.connector.connect(**config)
            if conn.is_connected():
                print(f"Conexión exitosa con: {config}")
                break
        except Error as e:
            print(f"Error al conectar con: {config}. Error: {e}")
            continue
    
    if not conn or not conn.is_connected():
        print("No se pudo establecer conexión con ninguna configuración")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Usar la base de datos
        cursor.execute("USE sistema_ganadero")
        
        # Eliminar la tabla si existe
        print("Eliminando tabla registro_leche si existe...")
        cursor.execute("DROP TABLE IF EXISTS registro_leche")
        
        # Crear la tabla desde cero con una estructura mejorada
        print("Creando nueva tabla registro_leche...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_leche (
            id INT AUTO_INCREMENT PRIMARY KEY,
            animal_id INT NOT NULL,
            usuario_id INT NOT NULL,
            fecha DATE NOT NULL,
            cantidad DECIMAL(10,2) NOT NULL,
            turno VARCHAR(20) NOT NULL,
            calidad VARCHAR(50) DEFAULT 'A',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_animal (animal_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_fecha (fecha),
            INDEX idx_turno (turno),
            FOREIGN KEY (animal_id) REFERENCES animales(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        print("Tabla registro_leche reconstruida exitosamente")
        return True
    
    except Error as e:
        print(f"Error al reconstruir tabla: {e}")
        return False
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    reconstruir_tabla_registro_leche()
