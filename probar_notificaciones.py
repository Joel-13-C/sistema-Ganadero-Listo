# Script para probar el envío de notificaciones automáticas
import sys
import os
import datetime
sys.path.append(os.getcwd())

from src.alarmas import SistemaAlarmas
from src.database import DatabaseConnection

def obtener_conexion():
    # Usamos el método correcto para obtener una conexión
    try:
        db = DatabaseConnection()  # No pasamos parámetros porque los usa del archivo .env
        return db.get_connection()
    except Exception as e:
        print(f"Error al obtener conexión: {e}")
        return None

def probar_envio_notificaciones():
    print("=== INICIANDO PRUEBA DE ENVÍO DE NOTIFICACIONES ===")
    
    # Inicializar el sistema de alarmas con la función de conexión
    alarmas = SistemaAlarmas(obtener_conexion)
    
    # Verificar desparasitaciones pendientes y enviar notificaciones
    print("\n=== VERIFICANDO DESPARASITACIONES PENDIENTES ===")
    notificaciones_desparasitacion = alarmas.verificar_desparasitaciones_pendientes()
    print(f"Notificaciones de desparasitación enviadas: {notificaciones_desparasitacion}")
    
    print("\n=== PROBANDO ENVÍO DIRECTO DE CORREO DE PRUEBA ===")
    # Probar envío directo de un correo electrónico de prueba
    destinatario = alarmas.email_config['username']  # Usar el mismo correo configurado
    asunto = "Prueba de Notificaciones - Sistema Ganadero"
    fecha_hora_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mensaje = f"""
    PRUEBA DE SISTEMA DE NOTIFICACIONES
    
    Este es un correo de prueba para verificar que el sistema de notificaciones
    automáticas del Sistema Ganadero esté funcionando correctamente.
    
    Fecha y hora de la prueba: {fecha_hora_actual}
    
    Si recibe este correo, significa que el sistema está correctamente configurado
    para enviar notificaciones automáticas.
    """
    
    enviado = alarmas._enviar_notificacion_email(destinatario, asunto, mensaje)
    print(f"Resultado de envío de correo de prueba: {'EXITOSO' if enviado else 'FALLIDO'}")
    
    print("\n=== PRUEBA DE ENVÍO DE NOTIFICACIONES FINALIZADA ===")
    
if __name__ == "__main__":
    probar_envio_notificaciones()
