import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'root'),
    'database': os.getenv('MYSQL_DB', 'sistema_ganadero')
}

def init_db():
    # Intentar diferentes configuraciones de conexión
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
            print(f"Intentando conectar con: {config}")
            conn = mysql.connector.connect(
                **config,
                database="sistema_ganadero"
            )
            if conn.is_connected():
                print(f"Conexión exitosa con: {config}")
                break
        except Exception as e:
            print(f"Error al conectar con: {config}. Error: {e}")
            continue
    
    if not conn or not conn.is_connected():
        print("Error: No se pudo conectar a la base de datos")
        return
        
    cursor = conn.cursor()
    
    try:
        # Crear tablas para el módulo de reportes PDF si no existen
        
        # Tabla para categorías de animales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_animales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla para categorías de ingresos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_ingresos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla para categorías de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_gastos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla para configuración de correo electrónico
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_email (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                smtp_server VARCHAR(100) NOT NULL,
                port INT DEFAULT 587,
                username VARCHAR(100) NOT NULL,
                password VARCHAR(255) NOT NULL,
                from_email VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_usuario (usuario_id)
            )
        """)
        
        # Tabla para eventos de salud
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eventos_salud (
                id INT AUTO_INCREMENT PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha DATE NOT NULL,
                tipo ENUM('Vacunación', 'Tratamiento', 'Enfermedad') NOT NULL,
                descripcion TEXT NOT NULL,
                responsable VARCHAR(100) NOT NULL,
                costo DECIMAL(10,2),
                recordatorio_dias INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Tabla para registro de producción de leche
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_leche (
                id INT AUTO_INCREMENT PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha DATE NOT NULL,
                cantidad DECIMAL(10,2) NOT NULL,
                turno ENUM('Mañana', 'Tarde') NOT NULL,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Tabla para ventas de leche
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas_leche (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fecha DATE NOT NULL,
                cantidad DECIMAL(10,2) NOT NULL,
                precio_litro DECIMAL(10,2) NOT NULL,
                comprador VARCHAR(100) NOT NULL,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar datos de ejemplo en categorías de animales
        cursor.execute("SELECT COUNT(*) FROM categorias_animales")
        if cursor.fetchone()[0] == 0:
            categorias = [
                ('Vacas', 'Hembras adultas en producción'),
                ('Toros', 'Machos adultos reproductores'),
                ('Novillos', 'Machos castrados en engorde'),
                ('Vaquillas', 'Hembras jóvenes antes de su primer parto'),
                ('Terneros', 'Crías menores de un año')
            ]
            cursor.executemany(
                "INSERT INTO categorias_animales (nombre, descripcion) VALUES (%s, %s)",
                categorias
            )
        
        # Insertar datos de ejemplo en categorías de ingresos
        cursor.execute("SELECT COUNT(*) FROM categorias_ingresos")
        if cursor.fetchone()[0] == 0:
            categorias = [
                ('Venta de leche', 'Ingresos por venta de producción láctea'),
                ('Venta de animales', 'Ingresos por venta de ganado'),
                ('Subsidios', 'Ingresos por subsidios gubernamentales'),
                ('Otros', 'Otros ingresos relacionados con la actividad ganadera')
            ]
            cursor.executemany(
                "INSERT INTO categorias_ingresos (nombre, descripcion) VALUES (%s, %s)",
                categorias
            )
        
        # Insertar datos de ejemplo en categorías de gastos
        cursor.execute("SELECT COUNT(*) FROM categorias_gastos")
        if cursor.fetchone()[0] == 0:
            categorias = [
                ('Alimentación', 'Gastos en alimentos y suplementos'),
                ('Sanidad', 'Gastos en medicamentos y atención veterinaria'),
                ('Mantenimiento', 'Gastos en mantenimiento de instalaciones'),
                ('Servicios', 'Gastos en servicios como agua, luz, etc.'),
                ('Salarios', 'Gastos en salarios y jornales'),
                ('Otros', 'Otros gastos relacionados con la actividad ganadera')
            ]
            cursor.executemany(
                "INSERT INTO categorias_gastos (nombre, descripcion) VALUES (%s, %s)",
                categorias
            )
        
        conn.commit()
        print("Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_db()
