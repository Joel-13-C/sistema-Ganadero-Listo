-- Crear tabla para configuración de correo electrónico
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
);
