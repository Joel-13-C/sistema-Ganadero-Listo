#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para modificar el archivo app.py y mejorar el planificador de tareas.
"""

import re
import os
import sys
import shutil
from datetime import datetime

def main():
    """
    Función principal que modifica el archivo app.py
    """
    print("\n===== MODIFICANDO PLANIFICADOR DE TAREAS =====\n")
    
    try:
        # Ruta del archivo app.py
        app_path = 'app.py'
        
        # Crear una copia de seguridad
        backup_path = f'app.py.bak.{datetime.now().strftime("%Y%m%d%H%M%S")}'
        shutil.copy2(app_path, backup_path)
        print(f"Copia de seguridad creada: {backup_path}")
        
        # Leer el contenido del archivo
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar la sección del planificador
        scheduler_pattern = r'# Inicializar el planificador\nscheduler = BackgroundScheduler\(\)\nscheduler\.add_job\(.*?\)\nscheduler\.start\(\)\n\n# Asegurar que el planificador'
        
        # Reemplazar con la nueva configuración
        new_scheduler_code = """# Inicializar el planificador
scheduler = BackgroundScheduler()
# Ejecutar cada 6 horas en lugar de cada 24 horas para verificar más frecuentemente
scheduler.add_job(func=verificar_alarmas_programadas, trigger="interval", hours=6)

# Ejecutar la verificación de alarmas al iniciar la aplicación (después de 10 segundos)
scheduler.add_job(func=verificar_alarmas_programadas, trigger="date", run_date=datetime.now() + timedelta(seconds=10))
app.logger.info('Verificación inicial de alarmas programada')

# Iniciar el planificador
scheduler.start()

# Asegurar que el planificador"""
        
        # Realizar el reemplazo
        new_content = re.sub(scheduler_pattern, new_scheduler_code, content, flags=re.DOTALL)
        
        # Verificar si se realizó algún cambio
        if new_content == content:
            print("No se pudo encontrar la sección del planificador. Intentando otro enfoque...")
            
            # Buscar la sección del planificador de forma más simple
            scheduler_start = content.find("# Inicializar el planificador")
            scheduler_end = content.find("# Asegurar que el planificador")
            
            if scheduler_start != -1 and scheduler_end != -1:
                # Extraer la parte antes y después de la sección del planificador
                before = content[:scheduler_start]
                after = content[scheduler_end:]
                
                # Crear el nuevo contenido
                new_content = before + new_scheduler_code + after[after.find("se detenga"):]
            else:
                print("No se pudo encontrar la sección del planificador de forma manual.")
                return 1
        
        # Guardar el nuevo contenido
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("Archivo app.py modificado exitosamente.")
        print("\nCambios realizados:")
        print("1. El planificador ahora ejecuta la verificación de alarmas cada 6 horas en lugar de cada 24 horas")
        print("2. Se agregó una verificación inicial que se ejecuta 10 segundos después de iniciar la aplicación")
        print("\nPara aplicar los cambios, reinicia la aplicación Flask.")
        
        return 0  # Éxito
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1  # Error

if __name__ == "__main__":
    sys.exit(main())
