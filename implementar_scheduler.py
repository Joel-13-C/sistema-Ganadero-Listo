# Script para implementar el scheduler de notificaciones automáticas
import os

# Ruta al archivo app.py
app_path = os.path.join(os.getcwd(), 'app.py')

# Leer el contenido del archivo app.py
with open(app_path, 'r', encoding='utf-8') as file:
    content = file.readlines()

# Verificar si ya está importado APScheduler
has_apscheduler_import = False
for line in content:
    if 'from apscheduler.schedulers.background import BackgroundScheduler' in line:
        has_apscheduler_import = True
        break

# Si no está importado, añadirlo
if not has_apscheduler_import:
    # Buscar la última importación para añadir después
    last_import_index = 0
    for i, line in enumerate(content):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            last_import_index = i
    
    # Añadir la importación de APScheduler después de la última importación
    content.insert(last_import_index + 1, 'from apscheduler.schedulers.background import BackgroundScheduler\n')
    print("Importación de APScheduler añadida")

# Definir la función verificar_alarmas_programadas
verificar_alarmas_code = """
def verificar_alarmas_programadas():
    \"\"\"
    Función para verificar alarmas programadas (partos, vacunaciones, desparasitaciones)
    Esta función se ejecuta automáticamente según la programación configurada
    \"\"\"
    app.logger.info('Iniciando verificación programada de alarmas...')
    
    # Inicializar sistema de alarmas
    alarmas = SistemaAlarmas(get_db_connection)
    
    # Verificar partos próximos
    partos = alarmas.verificar_partos_proximos()
    
    # Verificar vacunaciones pendientes
    vacunaciones = alarmas.verificar_vacunaciones_pendientes()
    
    # Verificar desparasitaciones pendientes
    desparasitaciones = alarmas.verificar_desparasitaciones_pendientes()
    
    app.logger.info(f'Verificación programada de alarmas: {partos} notificaciones de partos, {vacunaciones} de vacunaciones y {desparasitaciones} de desparasitaciones enviadas')
"""

# Buscar si la función verificar_alarmas_programadas ya existe
has_function = False
for i, line in enumerate(content):
    if 'def verificar_alarmas_programadas' in line:
        has_function = True
        break

# Si la función no existe, añadirla al final de las otras funciones
if not has_function:
    # Buscar la última función para añadir después
    last_func_end = 0
    in_route = False
    for i, line in enumerate(content):
        if line.strip().startswith('@app.route'):
            in_route = True
        elif in_route and line.strip() == '':
            in_route = False
            last_func_end = i
    
    # Añadir la función después de la última ruta
    content.insert(last_func_end, verificar_alarmas_code + '\n')
    print("Función verificar_alarmas_programadas añadida")

# Código para inicializar y configurar el scheduler
scheduler_code = """
# Inicializar el scheduler para tareas programadas
scheduler = BackgroundScheduler()
scheduler.add_job(func=verificar_alarmas_programadas, trigger="interval", hours=24)
scheduler.start()

# Registrar una función para detener el scheduler cuando la aplicación se cierre
import atexit
atexit.register(lambda: scheduler.shutdown())
"""

# Buscar si el scheduler ya está configurado
has_scheduler = False
for i, line in enumerate(content):
    if 'scheduler = BackgroundScheduler()' in line:
        has_scheduler = True
        break

# Si el scheduler no está configurado, añadirlo antes de iniciar la aplicación
if not has_scheduler:
    # Buscar dónde se inicia la aplicación (normalmente al final del archivo)
    app_run_index = 0
    for i, line in enumerate(content):
        if 'app.run(' in line:
            app_run_index = i
            break
    
    # Si no se encuentra app.run(), usar el final del archivo
    if app_run_index == 0:
        app_run_index = len(content)
    
    # Añadir el código del scheduler justo antes de app.run()
    content.insert(app_run_index, scheduler_code + '\n')
    print("Configuración del scheduler añadida")

# Guardar los cambios
with open(app_path, 'w', encoding='utf-8') as file:
    file.writelines(content)

print("¡Implementación del sistema de notificaciones automáticas completada!")
