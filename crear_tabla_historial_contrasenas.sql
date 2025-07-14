-- Script para crear la tabla de historial de contraseñas
-- Esta tabla almacenará un registro de las contraseñas anteriores de los usuarios
-- para implementar políticas de seguridad como no reutilizar contraseñas

CREATE TABLE IF NOT EXISTS historial_contrasenas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip VARCHAR(45),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índice para búsquedas por usuario_id
CREATE INDEX idx_historial_contrasenas_usuario_id ON historial_contrasenas(usuario_id);

-- Comentarios de la tabla
ALTER TABLE historial_contrasenas COMMENT 'Almacena el historial de contraseñas de los usuarios para implementar políticas de seguridad';
