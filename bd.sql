-- Eliminar base de datos si existe y crearla nuevamente
DROP DATABASE IF EXISTS sistema_ganadero2;
CREATE DATABASE sistema_ganadero2;
USE sistema_ganadero2;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    foto_perfil VARCHAR(500),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial_contrasenas
CREATE TABLE historial_contrasenas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de animales
CREATE TABLE animales (
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

-- Tabla de vacunas
CREATE TABLE vacunas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    periodo_aplicacion INT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de registro_vacunas
CREATE TABLE registro_vacunas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    vacuna_id INT NOT NULL,
    fecha_aplicacion DATE NOT NULL,
    fecha_proxima DATE,
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (vacuna_id) REFERENCES vacunas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de gestaciones
CREATE TABLE gestaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_monta DATE NOT NULL,
    fecha_probable_parto DATE NOT NULL,
    estado ENUM('En Gestación', 'Finalizado', 'Abortado') NOT NULL DEFAULT 'En Gestación',
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de inseminaciones
CREATE TABLE inseminaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_inseminacion DATE NOT NULL,
    raza_semental VARCHAR(100),
    codigo_pajuela VARCHAR(50),
    inseminador VARCHAR(100),
    exitosa BOOLEAN DEFAULT FALSE,
    fecha_parto_esperado DATE,
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de registro_leche
CREATE TABLE registro_leche (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha DATE NOT NULL,
    cantidad_manana DECIMAL(10,2),
    cantidad_tarde DECIMAL(10,2),
    total_dia DECIMAL(10,2),
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de ventas_leche
CREATE TABLE ventas_leche (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    cantidad_litros DECIMAL(10,2) NOT NULL,
    precio_litro DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    comprador VARCHAR(200),
    forma_pago ENUM('Efectivo', 'Transferencia', 'Cheque', 'Otro') DEFAULT 'Efectivo',
    estado_pago ENUM('Pagado', 'Pendiente', 'Parcial') DEFAULT 'Pendiente',
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de categorías de ingresos
CREATE TABLE categorias_ingreso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de ingresos
CREATE TABLE ingresos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    categoria_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion TEXT,
    comprobante VARCHAR(255),
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_ingreso(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de categorías de gastos
CREATE TABLE categorias_gasto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de gastos
CREATE TABLE gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    categoria_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion TEXT,
    comprobante VARCHAR(255),
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_gasto(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de pastizales
CREATE TABLE pastizales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ubicacion TEXT,
    area DECIMAL(10,2),
    estado ENUM('Activo', 'Inactivo', 'Mantenimiento') DEFAULT 'Activo',
    descripcion TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de asignación de animales a pastizales
CREATE TABLE animales_pastizal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    pastizal_id INT NOT NULL,
    fecha_asignacion DATE NOT NULL,
    fecha_retiro DATE,
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (pastizal_id) REFERENCES pastizales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de planes de alimentación
CREATE TABLE planes_alimentacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo_alimento VARCHAR(100),
    cantidad_diaria DECIMAL(10,2),
    frecuencia VARCHAR(50),
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de registro de alimentación
CREATE TABLE registro_alimentacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    plan_id INT,
    fecha DATE NOT NULL,
    tipo_alimento VARCHAR(100),
    cantidad DECIMAL(10,2),
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (plan_id) REFERENCES planes_alimentacion(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de mantenimientos
CREATE TABLE mantenimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('Equipo', 'Instalación', 'Vehículo', 'Otro') NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_mantenimiento DATE NOT NULL,
    costo DECIMAL(10,2),
    estado ENUM('Pendiente', 'En Proceso', 'Completado') DEFAULT 'Pendiente',
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de desparasitaciones
CREATE TABLE desparasitaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_aplicacion DATE NOT NULL,
    producto VARCHAR(100) NOT NULL,
    dosis VARCHAR(50),
    fecha_proxima DATE,
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de vitaminizaciones
CREATE TABLE vitaminizaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_aplicacion DATE NOT NULL,
    producto VARCHAR(100) NOT NULL,
    dosis VARCHAR(50),
    fecha_proxima DATE,
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla para registro de vacunación contra Fiebre Aftosa
CREATE TABLE fiebre_aftosa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_aplicacion DATE NOT NULL,
    fecha_proxima DATE NOT NULL,
    dosis VARCHAR(50),
    observaciones TEXT,
    usuario_id INT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla para registro de vacunación contra Carbunco
CREATE TABLE carbunco (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_aplicacion DATE NOT NULL,
    fecha_proxima DATE NOT NULL,
    dosis VARCHAR(50),
    observaciones TEXT,
    usuario_id INT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de genealogía
CREATE TABLE genealogia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    padre_arete VARCHAR(50),
    madre_arete VARCHAR(50),
    abuelo_paterno_arete VARCHAR(50),
    abuela_paterna_arete VARCHAR(50),
    abuelo_materno_arete VARCHAR(50),
    abuela_materna_arete VARCHAR(50),
    observaciones TEXT,
    usuario_id INT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de config_alarmas
CREATE TABLE config_alarmas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    dias_anticipacion INT NOT NULL DEFAULT 7,
    activo BOOLEAN DEFAULT TRUE,
    email VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de alarmas_enviadas
CREATE TABLE alarmas_enviadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    tipo VARCHAR(50) NOT NULL,
    referencia_id INT NOT NULL,
    descripcion TEXT,
    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(100) NOT NULL,
    mensaje TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de config_email
CREATE TABLE config_email (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    smtp_server VARCHAR(100) NOT NULL,
    smtp_port INT NOT NULL,
    smtp_user VARCHAR(100) NOT NULL,
    smtp_password VARCHAR(255) NOT NULL,
    from_email VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de auditoria
CREATE TABLE auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(50) NOT NULL,
    tabla VARCHAR(50) NOT NULL,
    registro_id INT,
    detalles TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Insertar usuario administrador por defecto
INSERT INTO usuarios (username, email, password, nombre, apellido) 
VALUES ('admin', 'admin@sistemaganadero.com', 'admin123', 'Administrador', 'Sistema');

-- Configuraciones iniciales de alarmas para el usuario admin
INSERT INTO config_alarmas (usuario_id, tipo, dias_anticipacion, activo, email) VALUES 
(1, 'parto', 7, true, 'admin@sistemaganadero.com'),
(1, 'vacunacion', 7, true, 'admin@sistemaganadero.com'),
(1, 'desparasitacion', 7, true, 'admin@sistemaganadero.com'),
(1, 'vitaminizacion', 7, true, 'admin@sistemaganadero.com');

-- Vacunas predeterminadas
INSERT INTO vacunas (nombre, descripcion, periodo_aplicacion, usuario_id) VALUES 
('Brucelosis', 'Vacuna contra la Brucelosis bovina', 365, 1),
('Carbunco', 'Vacuna contra el Carbunco bacteridiano', 180, 1),
('Fiebre Aftosa', 'Vacuna contra la Fiebre Aftosa', 180, 1);

-- Categorías de ingresos predeterminadas
INSERT INTO categorias_ingreso (nombre, descripcion, usuario_id) VALUES 
('Venta de Leche', 'Ingresos por venta de leche', 1),
('Venta de Animales', 'Ingresos por venta de ganado', 1),
('Subvenciones', 'Subvenciones gubernamentales', 1),
('Otros', 'Otros ingresos', 1);

-- Categorías de gastos predeterminadas
INSERT INTO categorias_gasto (nombre, descripcion, usuario_id) VALUES 
('Alimentación', 'Gastos en alimentación del ganado', 1),
('Veterinaria', 'Gastos veterinarios y medicamentos', 1),
('Mantenimiento', 'Mantenimiento de equipos e instalaciones', 1),
('Personal', 'Salarios y gastos de personal', 1),
('Otros', 'Otros gastos', 1); 