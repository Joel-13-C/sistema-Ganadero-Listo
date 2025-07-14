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
