-- Agregar columna usuario_id
ALTER TABLE inseminaciones
ADD COLUMN usuario_id INT;

-- Actualizar registros existentes con el usuario_id del animal correspondiente
UPDATE inseminaciones i
JOIN animales a ON i.animal_id = a.id
SET i.usuario_id = a.usuario_id;

-- Hacer la columna NOT NULL después de actualizarla
ALTER TABLE inseminaciones
MODIFY COLUMN usuario_id INT NOT NULL;

-- Agregar la llave foránea
ALTER TABLE inseminaciones
ADD CONSTRAINT fk_inseminaciones_usuario
FOREIGN KEY (usuario_id) REFERENCES usuarios(id);
