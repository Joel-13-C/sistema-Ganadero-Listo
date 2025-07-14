import mysql.connector
from mysql.connector import Error

def crear_tablas():
    """
    Crea las tablas necesarias para el sistema ganadero si no existen
    """
    try:
        # Intentar diferentes configuraciones de conexión
        conexiones_a_probar = [
            {"host": "localhost", "user": "root", "password": ""},
            {"host": "localhost", "user": "root", "password": "root"},
            {"host": "localhost", "user": "root", "password": "admin"},
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
        
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute("CREATE DATABASE IF NOT EXISTS sistema_ganadero")
        cursor.execute("USE sistema_ganadero")
        
        # Crear tabla de vacunaciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacunaciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            animal_id INT NOT NULL,
            usuario_id INT NOT NULL,
            tipo_vacuna VARCHAR(100) NOT NULL,
            fecha_aplicacion DATE,
            fecha_programada DATE NOT NULL,
            dosis VARCHAR(50),
            aplicada_por VARCHAR(100),
            observaciones TEXT,
            estado VARCHAR(20) DEFAULT 'Pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_animal (animal_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_estado (estado),
            INDEX idx_fecha_programada (fecha_programada)
        )
        """)
        
        # Crear tabla de gestaciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gestaciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            animal_id INT NOT NULL,
            usuario_id INT NOT NULL,
            fecha_inseminacion DATE NOT NULL,
            fecha_parto_estimada DATE NOT NULL,
            fecha_parto_real DATE,
            padre_id INT,
            metodo_reproduccion VARCHAR(50) NOT NULL,
            estado VARCHAR(20) DEFAULT 'En progreso',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_animal (animal_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_estado (estado),
            INDEX idx_fecha_parto (fecha_parto_estimada)
        )
        """)
        
        # Crear tabla de registro_leche
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_leche (
            id INT AUTO_INCREMENT PRIMARY KEY,
            animal_id INT NOT NULL,
            usuario_id INT NOT NULL,
            fecha DATE NOT NULL,
            cantidad DECIMAL(10,2) NOT NULL,
            periodo VARCHAR(20) NOT NULL,
            calidad VARCHAR(50),
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_animal (animal_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_fecha (fecha)
        )
        """)
        
        conn.commit()
        print("Tablas creadas exitosamente")
        return True
    
    except Error as e:
        print(f"Error al crear tablas: {e}")
        return False
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    crear_tablas()
