#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificar alarmas de partos y vacunaciones manualmente.
Este script puede ser ejecutado directamente o programado con una tarea cron/programador de tareas.
"""

from src.database import get_db_connection
from src.alarmas import SistemaAlarmas
import sys

def main():
    """
    Función principal que verifica las alarmas de partos y vacunaciones
    """
    print("\n===== SISTEMA DE VERIFICACIÓN MANUAL DE ALARMAS =====\n")
    
    try:
        # Inicializar el sistema de alarmas
        print("Inicializando sistema de alarmas...")
        alarmas = SistemaAlarmas(get_db_connection)
        
        # Verificar partos próximos
        print("\nVerificando partos próximos...")
        partos = alarmas.verificar_partos_proximos()
        print(f"Notificaciones de partos enviadas: {partos}")
        
        # Verificar vacunaciones pendientes
        print("\nVerificando vacunaciones pendientes...")
        vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        print(f"Notificaciones de vacunaciones enviadas: {vacunaciones}")
        
        # Mostrar resumen
        print("\n===== RESUMEN DE VERIFICACIÓN =====")
        print(f"Total de notificaciones enviadas: {partos + vacunaciones}")
        print(f"- Partos próximos: {partos}")
        print(f"- Vacunaciones pendientes: {vacunaciones}")
        
        return 0  # Éxito
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1  # Error

if __name__ == "__main__":
    sys.exit(main())
