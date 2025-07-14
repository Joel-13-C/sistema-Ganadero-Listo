-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sistema_ganadero;
USE sistema_ganadero;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(64) NOT NULL,
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de animales
CREATE TABLE IF NOT EXISTS animales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    nombre VARCHAR(100),
    numero_arete VARCHAR(50) UNIQUE,
    raza VARCHAR(50),
    sexo VARCHAR(10),
    condicion VARCHAR(50),
    fecha_nacimiento DATE,
    propietario VARCHAR(100),
    padre_arete VARCHAR(50),
    madre_arete VARCHAR(50),
    foto_path VARCHAR(255),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Usuario de prueba
INSERT INTO usuarios (username, email, password) VALUES (
    'admin', 
    'admin@sistemaganadero.com', 
    SHA2('1234', 256)
);
