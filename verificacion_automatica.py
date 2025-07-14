#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificación automática de alarmas.
Este script puede ser programado para ejecutarse automáticamente con el Programador de tareas de Windows.
"""

from src.database import get_db_connection
from src.alarmas import SistemaAlarmas
import sys
import os
import logging
from datetime import datetime

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'verificacion_automatica.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """
    Función principal que verifica las alarmas de partos y vacunaciones
    """
    logging.info("===== INICIANDO VERIFICACIÓN AUTOMÁTICA DE ALARMAS =====")
    
    try:
        # Inicializar el sistema de alarmas
        logging.info("Inicializando sistema de alarmas...")
        alarmas = SistemaAlarmas(get_db_connection)
        
        # Verificar partos próximos
        logging.info("Verificando partos próximos...")
        partos = alarmas.verificar_partos_proximos()
        logging.info(f"Notificaciones de partos enviadas: {partos}")
        
        # Verificar vacunaciones pendientes
        logging.info("Verificando vacunaciones pendientes...")
        vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        logging.info(f"Notificaciones de vacunaciones enviadas: {vacunaciones}")
        
        # Verificar desparasitaciones pendientes
        logging.info("Verificando desparasitaciones pendientes...")
        desparasitaciones = alarmas.verificar_desparasitaciones_pendientes()
        logging.info(f"Notificaciones de desparasitaciones enviadas: {desparasitaciones}")
        
        # Mostrar resumen
        logging.info("===== RESUMEN DE VERIFICACIÓN =====")
        logging.info(f"Total de notificaciones enviadas: {partos + vacunaciones + desparasitaciones}")
        logging.info(f"- Partos próximos: {partos}")
        logging.info(f"- Vacunaciones pendientes: {vacunaciones}")
        logging.info(f"- Desparasitaciones pendientes: {desparasitaciones}")
        
        return 0  # Éxito
    except Exception as e:
        logging.error(f"ERROR: {str(e)}")
        return 1  # Error

if __name__ == "__main__":
    sys.exit(main())
