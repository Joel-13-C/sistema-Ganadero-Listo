-- Script para agregar los campos cargo y dirección a la tabla usuarios
-- Estos campos son necesarios para el funcionamiento del módulo de perfil

-- Verificar si la columna cargo existe, si no, agregarla
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS cargo VARCHAR(100) DEFAULT NULL;

-- Verificar si la columna direccion existe, si no, agregarla
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS direccion VARCHAR(255) DEFAULT NULL;

-- Agregar índice para búsquedas por cargo
CREATE INDEX IF NOT EXISTS idx_usuarios_cargo ON usuarios(cargo);
