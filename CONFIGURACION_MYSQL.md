# Configuración de MySQL para Sistema Ganadero

## Pasos para configurar MySQL Workbench

1. Abre MySQL Workbench
2. Conecta a tu instancia local de MySQL
3. Abre un nuevo query tab
4. Copia y pega el contenido de `init_database.sql`
5. Ejecuta el script (botón de rayo ⚡)

## Credenciales por defecto

- Host: localhost
- Usuario: root
- Contraseña: (dejar en blanco o configurar según tu instalación)
- Base de datos: sistema_ganadero

## Solución de problemas

- Si tienes contraseña para root, modifica `src/database.py`
- Asegúrate de tener MySQL Connector instalado
- Verifica que el servicio MySQL esté corriendo
