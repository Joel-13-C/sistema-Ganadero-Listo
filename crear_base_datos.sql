-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sistema_ganadero;
USE sistema_ganadero;

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Animales
CREATE TABLE IF NOT EXISTS animales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_arete VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100),
    sexo ENUM('Macho', 'Hembra') NOT NULL,
    raza VARCHAR(100),
    condicion ENUM('Toro', 'Torete', 'Vaca', 'Vacona', 'Ternero', 'Ternera') NOT NULL,
    fecha_nacimiento DATE,
    propietario VARCHAR(200),
    foto_path VARCHAR(500),
    padre_arete VARCHAR(50),
    madre_arete VARCHAR(50),
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Usuario de prueba
INSERT IGNORE INTO usuarios (username, email, password) 
VALUES ('admin', 'admin@sistemaganadero.com', 'admin123');

-- Mostrar información
SELECT 'Base de datos sistema_ganadero creada exitosamente' AS mensaje;
