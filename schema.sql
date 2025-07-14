-- Modificar la tabla animales para agregar la columna activo
ALTER TABLE animales
ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE;

-- Tabla para registros de desparasitación
CREATE TABLE IF NOT EXISTS desparasitacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_registro DATE NOT NULL,
    producto VARCHAR(100) NOT NULL,
    aplicacion_general BOOLEAN NOT NULL,  -- 0 = específica, 1 = general
    vacunador VARCHAR(100) NOT NULL,
    proxima_aplicacion DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para relacionar desparasitación con animales
CREATE TABLE IF NOT EXISTS desparasitacion_animal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    desparasitacion_id INT,
    animal_id INT,
    FOREIGN KEY (desparasitacion_id) REFERENCES desparasitacion(id),
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Tabla para registros de vitaminización
CREATE TABLE IF NOT EXISTS vitaminizacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_registro DATE NOT NULL,
    producto VARCHAR(100) NOT NULL,
    aplicacion_general BOOLEAN NOT NULL,
    aplicador VARCHAR(100) NOT NULL,
    proxima_aplicacion DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para relacionar vitaminización con animales
CREATE TABLE IF NOT EXISTS vitaminizacion_animal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vitaminizacion_id INT,
    animal_id INT,
    FOREIGN KEY (vitaminizacion_id) REFERENCES vitaminizacion(id),
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Tabla para registros de vacunación contra carbunco
CREATE TABLE IF NOT EXISTS carbunco (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_registro DATE NOT NULL,
    producto VARCHAR(100) NOT NULL,
    aplicacion_general BOOLEAN NOT NULL,
    vacunador VARCHAR(100) NOT NULL,
    lote VARCHAR(50) NOT NULL,
    proxima_aplicacion DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para relacionar vacunación contra carbunco con animales
CREATE TABLE IF NOT EXISTS carbunco_animal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carbunco_id INT,
    animal_id INT,
    FOREIGN KEY (carbunco_id) REFERENCES carbunco(id),
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Tabla para registro de vacunas (general)
CREATE TABLE IF NOT EXISTS vacuna (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    usuario_id INT NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    fecha_aplicacion DATE,
    fecha_proxima DATE NOT NULL,
    dosis VARCHAR(50),
    aplicada_por VARCHAR(100),
    observaciones TEXT,
    estado VARCHAR(20) DEFAULT 'Activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_animal (animal_id),
    INDEX idx_usuario (usuario_id),
    INDEX idx_estado (estado),
    INDEX idx_fecha_proxima (fecha_proxima),
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Tabla para provincias del Ecuador
CREATE TABLE IF NOT EXISTS provincias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(10) NOT NULL
);

-- Tabla para cantones
CREATE TABLE IF NOT EXISTS cantones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    provincia_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(10) NOT NULL,
    FOREIGN KEY (provincia_id) REFERENCES provincias(id)
);

-- Tabla para parroquias
CREATE TABLE IF NOT EXISTS parroquias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    canton_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(10) NOT NULL,
    FOREIGN KEY (canton_id) REFERENCES cantones(id)
);

-- Tabla para registros de fiebre aftosa
CREATE TABLE IF NOT EXISTS fiebre_aftosa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_registro DATE NOT NULL,
    numero_certificado VARCHAR(50) NOT NULL,
    nombre_propietario VARCHAR(100) NOT NULL,
    identificacion VARCHAR(13) NOT NULL COMMENT 'C.C. o R.U.C.',
    nombre_predio VARCHAR(100) NOT NULL,
    provincia_id INT NOT NULL,
    canton_id INT NOT NULL,
    parroquia_id INT NOT NULL,
    tipo_explotacion ENUM('Carne', 'Leche', 'Mixta', 'Lidia') NOT NULL,
    nombre_vacunador VARCHAR(100) NOT NULL,
    cedula_vacunador VARCHAR(10) NOT NULL,
    fecha_proxima_aplicacion DATE NOT NULL,
    usuario_id INT NOT NULL,
    FOREIGN KEY (provincia_id) REFERENCES provincias(id),
    FOREIGN KEY (canton_id) REFERENCES cantones(id),
    FOREIGN KEY (parroquia_id) REFERENCES parroquias(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla para relacionar animales con vacunaciones de fiebre aftosa
CREATE TABLE IF NOT EXISTS fiebre_aftosa_animal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fiebre_aftosa_id INT NOT NULL,
    animal_id INT NOT NULL,
    FOREIGN KEY (fiebre_aftosa_id) REFERENCES fiebre_aftosa(id),
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Tabla para los pastizales
CREATE TABLE IF NOT EXISTS pastizales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    dimension DECIMAL(10,2) NOT NULL COMMENT 'Dimensión en metros cuadrados',
    tipo_hierba ENUM('Pasto Dallis', 'Pasto Elefante', 'Pasto Saboya') NOT NULL,
    estado ENUM('En uso', 'Disponible', 'En regeneración') NOT NULL DEFAULT 'Disponible',
    fecha_ultimo_uso DATE,
    fecha_disponible DATE,
    capacidad_maxima INT GENERATED ALWAYS AS (FLOOR(dimension / 3.5)) STORED COMMENT 'Cantidad máxima de animales basada en 3.5m² por animal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla para relacionar pastizales con animales (cuando están en uso)
CREATE TABLE IF NOT EXISTS pastizales_animales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pastizal_id INT NOT NULL,
    animal_id INT NOT NULL,
    fecha_ingreso DATE NOT NULL,
    FOREIGN KEY (pastizal_id) REFERENCES pastizales(id),
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Módulo de Reproducción y Genética
CREATE TABLE IF NOT EXISTS inseminaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha_inseminacion DATE NOT NULL,
    tipo ENUM('Natural', 'Artificial') NOT NULL,
    semental VARCHAR(100),
    raza_semental VARCHAR(100),
    codigo_pajuela VARCHAR(50),
    inseminador VARCHAR(100),
    observaciones TEXT,
    exitosa BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

CREATE TABLE IF NOT EXISTS genealogia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    padre_id INT,
    madre_id INT,
    caracteristicas_heredadas TEXT,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (padre_id) REFERENCES animales(id),
    FOREIGN KEY (madre_id) REFERENCES animales(id)
);

-- Módulo de Producción Lechera
CREATE TABLE IF NOT EXISTS produccion_leche (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    fecha DATE NOT NULL,
    cantidad_manana DECIMAL(10,2),
    cantidad_tarde DECIMAL(10,2),
    calidad ENUM('A', 'B', 'C') NOT NULL,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

CREATE TABLE IF NOT EXISTS ventas_leche (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    cantidad_litros DECIMAL(10,2) NOT NULL,
    precio_litro DECIMAL(10,2) NOT NULL,
    comprador VARCHAR(100),
    total_venta DECIMAL(10,2) GENERATED ALWAYS AS (cantidad_litros * precio_litro) STORED,
    forma_pago ENUM('Efectivo', 'Transferencia', 'Crédito') NOT NULL,
    estado_pago ENUM('Pendiente', 'Pagado', 'Parcial') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Módulo de Finanzas
CREATE TABLE IF NOT EXISTS categorias_financieras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('Ingreso', 'Gasto') NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS transacciones_financieras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id INT NOT NULL,
    fecha DATE NOT NULL,
    tipo ENUM('Ingreso', 'Gasto') NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion TEXT,
    comprobante VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_financieras(id)
);

-- Módulo de Inventario
CREATE TABLE IF NOT EXISTS categorias_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS unidades_medida (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    abreviatura VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    categoria_id INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL DEFAULT 0,
    unidad_medida_id INT NOT NULL,
    precio_unitario DECIMAL(10,2),
    stock_minimo DECIMAL(10,2),
    ubicacion VARCHAR(100),
    fecha_vencimiento DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_inventario(id),
    FOREIGN KEY (unidad_medida_id) REFERENCES unidades_medida(id)
);

-- Módulo de Alimentación
CREATE TABLE IF NOT EXISTS planes_alimentacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria_animal ENUM('Ternero', 'Novillo', 'Vaca', 'Toro') NOT NULL,
    estado_productivo ENUM('Crecimiento', 'Mantenimiento', 'Producción', 'Gestación') NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detalles_plan_alimentacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT NOT NULL,
    alimento_id INT NOT NULL,
    cantidad_diaria DECIMAL(10,2) NOT NULL,
    unidad_medida VARCHAR(20) NOT NULL,
    horario VARCHAR(50),
    FOREIGN KEY (plan_id) REFERENCES planes_alimentacion(id),
    FOREIGN KEY (alimento_id) REFERENCES inventario(id)
);

CREATE TABLE IF NOT EXISTS registro_alimentacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    plan_id INT NOT NULL,
    fecha DATE NOT NULL,
    consumo_real DECIMAL(10,2),
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id),
    FOREIGN KEY (plan_id) REFERENCES planes_alimentacion(id)
);

-- Módulo de Mantenimiento
CREATE TABLE IF NOT EXISTS equipos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    modelo VARCHAR(100),
    serie VARCHAR(100),
    fecha_adquisicion DATE,
    estado ENUM('Activo', 'En Mantenimiento', 'Fuera de Servicio') NOT NULL,
    ubicacion VARCHAR(100),
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS mantenimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipo_id INT NOT NULL,
    tipo ENUM('Preventivo', 'Correctivo') NOT NULL,
    fecha_programada DATE,
    fecha_realizado DATE,
    costo DECIMAL(10,2),
    responsable VARCHAR(100),
    descripcion TEXT,
    estado ENUM('Pendiente', 'En Proceso', 'Completado', 'Cancelado') NOT NULL,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

-- Módulo de Empleados
CREATE TABLE IF NOT EXISTS empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    fecha_nacimiento DATE,
    fecha_contratacion DATE NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    salario DECIMAL(10,2),
    telefono VARCHAR(20),
    direccion TEXT,
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo'
);

CREATE TABLE IF NOT EXISTS asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    fecha DATE NOT NULL,
    hora_entrada TIME,
    hora_salida TIME,
    observaciones TEXT,
    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS tareas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    fecha_asignacion DATE NOT NULL,
    fecha_limite DATE,
    estado ENUM('Pendiente', 'En Proceso', 'Completada', 'Cancelada') NOT NULL,
    prioridad ENUM('Baja', 'Media', 'Alta', 'Urgente') NOT NULL,
    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);

-- Módulo de Clima y Ambiente
CREATE TABLE IF NOT EXISTS registros_clima (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    temperatura_min DECIMAL(5,2),
    temperatura_max DECIMAL(5,2),
    humedad DECIMAL(5,2),
    precipitacion DECIMAL(5,2),
    velocidad_viento DECIMAL(5,2),
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Módulo de Trazabilidad
CREATE TABLE IF NOT EXISTS eventos_animal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    tipo_evento ENUM('Nacimiento', 'Compra', 'Venta', 'Muerte', 'Traslado', 'Tratamiento', 'Otro') NOT NULL,
    fecha DATE NOT NULL,
    descripcion TEXT,
    ubicacion VARCHAR(100),
    responsable VARCHAR(100),
    documentos VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES animales(id)
);

-- Tabla para categorías de ingresos
CREATE TABLE IF NOT EXISTS categorias_ingreso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar algunas categorías predefinidas
INSERT INTO categorias_ingreso (nombre, descripcion) VALUES
('Venta de Leche', 'Ingresos por venta de producción lechera'),
('Venta de Ganado', 'Ingresos por venta de animales'),
('Venta de Productos', 'Ingresos por venta de otros productos ganaderos'),
('Servicios', 'Ingresos por servicios prestados'),
('Otros', 'Otros ingresos relacionados con la actividad ganadera');

-- Tabla para registro de ingresos
CREATE TABLE IF NOT EXISTS ingresos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    categoria_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion TEXT,
    comprobante VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_ingreso(id)
);

-- Tabla para categorías de gastos
CREATE TABLE IF NOT EXISTS categorias_gasto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar algunas categorías predefinidas de gastos
INSERT INTO categorias_gasto (nombre, descripcion) VALUES
('Alimentación', 'Gastos en alimentos y suplementos para el ganado'),
('Medicamentos', 'Gastos en medicamentos y tratamientos veterinarios'),
('Mantenimiento', 'Gastos en mantenimiento de instalaciones y equipos'),
('Servicios', 'Gastos en servicios como agua, luz, etc.'),
('Mano de Obra', 'Gastos en personal y trabajadores'),
('Otros', 'Otros gastos relacionados con la actividad ganadera');

-- Tabla para registro de gastos
CREATE TABLE IF NOT EXISTS gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    categoria_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    descripcion TEXT,
    comprobante VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_gasto(id)
);

-- Datos iniciales para categorías financieras
INSERT IGNORE INTO categorias_financieras (nombre, tipo, descripcion) VALUES
('Venta de Leche', 'Ingreso', 'Ingresos por venta de producción láctea'),
('Venta de Ganado', 'Ingreso', 'Ingresos por venta de animales'),
('Alimentación', 'Gasto', 'Gastos en alimentos y suplementos'),
('Medicamentos', 'Gasto', 'Gastos en medicamentos y tratamientos'),
('Mantenimiento', 'Gasto', 'Gastos en mantenimiento de equipos e instalaciones'),
('Salarios', 'Gasto', 'Pago de salarios a empleados'),
('Servicios', 'Gasto', 'Gastos en servicios básicos');

-- Insertar provincias
INSERT IGNORE INTO provincias (nombre, codigo) VALUES 
('Azuay', '01'),
('Bolívar', '02'),
('Cañar', '03'),
('Carchi', '04'),
('Cotopaxi', '05'),
('Chimborazo', '06'),
('El Oro', '07'),
('Esmeraldas', '08'),
('Guayas', '09'),
('Imbabura', '10'),
('Loja', '11'),
('Los Ríos', '12'),
('Manabí', '13'),
('Morona Santiago', '14'),
('Napo', '15'),
('Pastaza', '16'),
('Pichincha', '17'),
('Tungurahua', '18'),
('Zamora Chinchipe', '19'),
('Galápagos', '20'),
('Sucumbíos', '21'),
('Orellana', '22'),
('Santo Domingo de los Tsáchilas', '23'),
('Santa Elena', '24');

-- Insertar cantones y parroquias de Cotopaxi
SET @cotopaxi_id = (SELECT id FROM provincias WHERE nombre = 'Cotopaxi');

-- Cantones de Cotopaxi
INSERT IGNORE INTO cantones (provincia_id, nombre, codigo) VALUES 
(@cotopaxi_id, 'Latacunga', '0501'),
(@cotopaxi_id, 'La Maná', '0502'),
(@cotopaxi_id, 'Pangua', '0503'),
(@cotopaxi_id, 'Pujilí', '0504'),
(@cotopaxi_id, 'Salcedo', '0505'),
(@cotopaxi_id, 'Saquisilí', '0506'),
(@cotopaxi_id, 'Sigchos', '0507');

-- Parroquias de Latacunga
SET @latacunga_id = (SELECT id FROM cantones WHERE nombre = 'Latacunga' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@latacunga_id, 'Toacaso', '050151'),
(@latacunga_id, 'San Juan de Pastocalle', '050152'),
(@latacunga_id, 'Mulaló', '050153'),
(@latacunga_id, 'Tanicuchí', '050154'),
(@latacunga_id, 'José Guango Bajo', '050155'),
(@latacunga_id, 'Guaytacama', '050156'),
(@latacunga_id, 'Aláquez', '050157'),
(@latacunga_id, 'Poaló', '050158'),
(@latacunga_id, '11 de Noviembre', '050159'),
(@latacunga_id, 'Belisario Quevedo', '050160'),
(@latacunga_id, 'Latacunga', '050150');

-- Parroquias de La Maná
SET @lamana_id = (SELECT id FROM cantones WHERE nombre = 'La Maná' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@lamana_id, 'La Maná', '050201'),
(@lamana_id, 'Guasaganda', '050202'),
(@lamana_id, 'Pucayacu', '050203');

-- Parroquias de Pangua
SET @pangua_id = (SELECT id FROM cantones WHERE nombre = 'Pangua' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@pangua_id, 'El Corazón', '050301'),
(@pangua_id, 'Moraspungo', '050302'),
(@pangua_id, 'Pinllopata', '050303'),
(@pangua_id, 'Ramón Campaña', '050304');

-- Parroquias de Pujilí
SET @pujili_id = (SELECT id FROM cantones WHERE nombre = 'Pujilí' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@pujili_id, 'Pujilí', '050401'),
(@pujili_id, 'Angamarca', '050402'),
(@pujili_id, 'Guangaje', '050403'),
(@pujili_id, 'La Victoria', '050404'),
(@pujili_id, 'Pilaló', '050405'),
(@pujili_id, 'Tingo', '050406'),
(@pujili_id, 'Zumbahua', '050407');

-- Parroquias de Salcedo
SET @salcedo_id = (SELECT id FROM cantones WHERE nombre = 'Salcedo' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@salcedo_id, 'San Miguel', '050501'),
(@salcedo_id, 'Antonio José Holguín', '050502'),
(@salcedo_id, 'Cusubamba', '050503'),
(@salcedo_id, 'Mulalillo', '050504'),
(@salcedo_id, 'Mulliquindil', '050505'),
(@salcedo_id, 'Panzaleo', '050506');

-- Parroquias de Saquisilí
SET @saquisili_id = (SELECT id FROM cantones WHERE nombre = 'Saquisilí' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@saquisili_id, 'Saquisilí', '050601'),
(@saquisili_id, 'Canchagua', '050602'),
(@saquisili_id, 'Chantilin', '050603'),
(@saquisili_id, 'Cochapamba', '050604');

-- Parroquias de Sigchos
SET @sigchos_id = (SELECT id FROM cantones WHERE nombre = 'Sigchos' AND provincia_id = @cotopaxi_id);
INSERT IGNORE INTO parroquias (canton_id, nombre, codigo) VALUES
(@sigchos_id, 'Sigchos', '050701'),
(@sigchos_id, 'Chugchilán', '050702'),
(@sigchos_id, 'Isinliví', '050703'),
(@sigchos_id, 'Las Pampas', '050704'),
(@sigchos_id, 'Palo Quemado', '050705');

-- Insertar provincias de Ecuador
INSERT INTO provincias (nombre) VALUES 
('Los Ríos'),
('Chimborazo'),
('Guayas'),
('Pichincha'),
('Manabí');

-- Cantones y Parroquias de Los Ríos
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Babahoyo', id FROM provincias WHERE nombre = 'Los Ríos';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Quevedo', id FROM provincias WHERE nombre = 'Los Ríos';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Ventanas', id FROM provincias WHERE nombre = 'Los Ríos';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Vinces', id FROM provincias WHERE nombre = 'Los Ríos';

-- Parroquias de Babahoyo
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Babahoyo', id FROM cantones WHERE nombre = 'Babahoyo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Caracol', id FROM cantones WHERE nombre = 'Babahoyo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Febres Cordero', id FROM cantones WHERE nombre = 'Babahoyo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Pimocha', id FROM cantones WHERE nombre = 'Babahoyo';

-- Parroquias de Quevedo
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Quevedo', id FROM cantones WHERE nombre = 'Quevedo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'San Carlos', id FROM cantones WHERE nombre = 'Quevedo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'La Esperanza', id FROM cantones WHERE nombre = 'Quevedo';

-- Cantones y Parroquias de Chimborazo
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Riobamba', id FROM provincias WHERE nombre = 'Chimborazo';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Alausí', id FROM provincias WHERE nombre = 'Chimborazo';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Guano', id FROM provincias WHERE nombre = 'Chimborazo';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Chunchi', id FROM provincias WHERE nombre = 'Chimborazo';

-- Parroquias de Riobamba
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Lizarzaburu', id FROM cantones WHERE nombre = 'Riobamba';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Maldonado', id FROM cantones WHERE nombre = 'Riobamba';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Velasco', id FROM cantones WHERE nombre = 'Riobamba';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Veloz', id FROM cantones WHERE nombre = 'Riobamba';

-- Parroquias de Guano
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Guano', id FROM cantones WHERE nombre = 'Guano';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'San Andrés', id FROM cantones WHERE nombre = 'Guano';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'San Isidro', id FROM cantones WHERE nombre = 'Guano';

-- Cantones y Parroquias de Guayas
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Guayaquil', id FROM provincias WHERE nombre = 'Guayas';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Daule', id FROM provincias WHERE nombre = 'Guayas';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Durán', id FROM provincias WHERE nombre = 'Guayas';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Samborondón', id FROM provincias WHERE nombre = 'Guayas';

-- Parroquias de Guayaquil
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Tarqui', id FROM cantones WHERE nombre = 'Guayaquil';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Ximena', id FROM cantones WHERE nombre = 'Guayaquil';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Pascuales', id FROM cantones WHERE nombre = 'Guayaquil';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Chongón', id FROM cantones WHERE nombre = 'Guayaquil';

-- Parroquias de Daule
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Daule', id FROM cantones WHERE nombre = 'Daule';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'La Aurora', id FROM cantones WHERE nombre = 'Daule';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Los Lojas', id FROM cantones WHERE nombre = 'Daule';

-- Cantones y Parroquias de Pichincha
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Quito', id FROM provincias WHERE nombre = 'Pichincha';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Rumiñahui', id FROM provincias WHERE nombre = 'Pichincha';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Mejía', id FROM provincias WHERE nombre = 'Pichincha';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Cayambe', id FROM provincias WHERE nombre = 'Pichincha';

-- Parroquias de Quito
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'La Magdalena', id FROM cantones WHERE nombre = 'Quito';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Calderón', id FROM cantones WHERE nombre = 'Quito';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Tumbaco', id FROM cantones WHERE nombre = 'Quito';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Cumbayá', id FROM cantones WHERE nombre = 'Quito';

-- Parroquias de Rumiñahui
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Sangolquí', id FROM cantones WHERE nombre = 'Rumiñahui';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'San Rafael', id FROM cantones WHERE nombre = 'Rumiñahui';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'San Pedro de Taboada', id FROM cantones WHERE nombre = 'Rumiñahui';

-- Cantones y Parroquias de Manabí
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Portoviejo', id FROM provincias WHERE nombre = 'Manabí';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Manta', id FROM provincias WHERE nombre = 'Manabí';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Chone', id FROM provincias WHERE nombre = 'Manabí';
INSERT INTO cantones (nombre, provincia_id) 
SELECT 'Jipijapa', id FROM provincias WHERE nombre = 'Manabí';

-- Parroquias de Portoviejo
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Portoviejo', id FROM cantones WHERE nombre = 'Portoviejo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Andrés de Vera', id FROM cantones WHERE nombre = 'Portoviejo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Colón', id FROM cantones WHERE nombre = 'Portoviejo';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Picoazá', id FROM cantones WHERE nombre = 'Portoviejo';

-- Parroquias de Manta
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Manta', id FROM cantones WHERE nombre = 'Manta';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Tarqui', id FROM cantones WHERE nombre = 'Manta';
INSERT INTO parroquias (nombre, canton_id) 
SELECT 'Los Esteros', id FROM cantones WHERE nombre = 'Manta';

-- Datos iniciales para categorías de inventario
INSERT INTO categorias_inventario (nombre, descripcion) VALUES
('Alimentos', 'Productos para alimentación animal'),
('Medicamentos', 'Medicinas y productos veterinarios'),
('Herramientas', 'Herramientas y equipos'),
('Insumos', 'Insumos generales');

-- Datos iniciales para unidades de medida
INSERT INTO unidades_medida (nombre, abreviatura) VALUES
('Kilogramo', 'kg'),
('Gramo', 'g'),
('Litro', 'L'),
('Mililitro', 'ml'),
('Unidad', 'u'),
('Metro', 'm'),
('Metro cuadrado', 'm²'),
('Quintal', 'qq');
