-- Script para eliminar las tablas relacionadas con el módulo de empleados
-- ADVERTENCIA: Este script eliminará permanentemente los datos de empleados, asistencias y tareas

-- Primero eliminar las tablas dependientes (con claves foráneas)
DROP TABLE IF EXISTS tareas;
DROP TABLE IF EXISTS asistencias;

-- Finalmente eliminar la tabla principal
DROP TABLE IF EXISTS empleados;

-- Mensaje de confirmación
SELECT 'Módulo de empleados eliminado correctamente' AS mensaje;
