#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para actualizar la función verificar_alarmas_programadas en app.py
para incluir la verificación de desparasitaciones.
"""

import re
import os
import sys
import shutil
from datetime import datetime

def main():
    """
    Función principal que modifica la función verificar_alarmas_programadas en app.py
    """
    print("\n===== ACTUALIZANDO FUNCIÓN DE VERIFICACIÓN DE ALARMAS =====\n")
    
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
        
        # Buscar la función verificar_alarmas_programadas
        function_pattern = r'def verificar_alarmas_programadas\(\):\s+try:.*?app\.logger\.error\(.*?\)\s+print\(.*?\)\s*except'
        
        # Nueva implementación de la función
        new_function = """def verificar_alarmas_programadas():
    try:
        print("\\n==== VERIFICACIÓN PROGRAMADA DE ALARMAS ====")
        
        # Verificar partos próximos
        partos = alarmas.verificar_partos_proximos()
        
        # Verificar vacunaciones pendientes
        vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        
        # Verificar desparasitaciones pendientes
        desparasitaciones = alarmas.verificar_desparasitaciones_pendientes()
        
        app.logger.info(f'Verificación programada de alarmas: {partos} notificaciones de partos, {vacunaciones} de vacunaciones y {desparasitaciones} de desparasitaciones enviadas')
        print(f'Verificación programada de alarmas: {partos} notificaciones de partos, {vacunaciones} de vacunaciones y {desparasitaciones} de desparasitaciones enviadas')
    except"""
        
        # Realizar el reemplazo
        new_content = re.sub(function_pattern, new_function, content, flags=re.DOTALL)
        
        # Verificar si se realizó algún cambio
        if new_content == content:
            print("No se pudo encontrar la función verificar_alarmas_programadas. Intentando otro enfoque...")
            
            # Buscar la función de forma más simple
            function_start = content.find("def verificar_alarmas_programadas():")
            if function_start != -1:
                function_end = content.find("except", function_start)
                if function_end != -1:
                    # Extraer la parte antes y después de la función
                    before = content[:function_start]
                    after = content[function_end:]
                    
                    # Crear el nuevo contenido
                    new_content = before + new_function + after
                else:
                    print("No se pudo encontrar el final de la función verificar_alarmas_programadas.")
                    return 1
            else:
                print("No se pudo encontrar la función verificar_alarmas_programadas de forma manual.")
                return 1
        
        # Guardar el nuevo contenido
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("Archivo app.py modificado exitosamente.")
        print("\nCambios realizados:")
        print("1. Se actualizó la función verificar_alarmas_programadas para incluir la verificación de desparasitaciones")
        print("\nPara aplicar los cambios, reinicia la aplicación Flask.")
        
        return 0  # Éxito
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1  # Error

if __name__ == "__main__":
    sys.exit(main())
