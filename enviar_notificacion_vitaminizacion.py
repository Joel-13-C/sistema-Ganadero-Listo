# Script para enviar una notificación de vitaminización pendiente
from src.database import get_db_connection
from src.alarmas import SistemaAlarmas
from datetime import datetime, timedelta
import logging

# Configurar logging para mostrar información detallada
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print("=== ENVIANDO NOTIFICACIÓN DE VITAMINIZACIÓN PENDIENTE ===")
print("Fecha actual:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Inicializar el sistema de alarmas
alarmas = SistemaAlarmas(get_db_connection)

# Verificar vitaminizaciones pendientes y enviar notificaciones
notificaciones = alarmas.verificar_vitaminizaciones_pendientes()

print(f"\nResultado: Se enviaron {notificaciones} notificaciones de vitaminizaciones pendientes")
print("\nPor favor, revisa la bandeja de entrada del correo fernando05calero@gmail.com")
print("La notificación debería haber llegado con el asunto 'ALERTA: Vitaminización pendiente'")
