# Script para probar el funcionamiento del sistema de notificaciones
import sys
import os
import datetime
from flask import session, Flask

# Añadir ruta actual al path de Python
sys.path.append(os.getcwd())

# Importar necesarios desde el proyecto
from src.alarmas import SistemaAlarmas
from src.database import get_db_connection

def probar_sistema_notificaciones():
    print("\n=== PRUEBA DEL SISTEMA DE NOTIFICACIONES AUTOMÁTICAS ===\n")
    
    # Crear una aplicación Flask para simular el entorno
    app = Flask(__name__)
    app.secret_key = "sistema_ganadero_secret_key"
    
    # Simular una sesión de usuario
    with app.test_request_context():
        # Establecer datos de sesión (simulando un usuario logueado)
        session['usuario_id'] = 1
        session['username'] = 'admin'
        
        # Inicializar el sistema de alarmas con la función de conexión que ya existe
        print("Inicializando sistema de alarmas...")
        sistema_alarmas = SistemaAlarmas(get_db_connection)
        
        # 1. Probar envío de correo directo
        print("\n--- Probando envío de correo directo ---")
        destinatario = sistema_alarmas.email_config['username']  # Usar el email configurado
        asunto = "Prueba de Sistema de Notificaciones - " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mensaje = f"""
        PRUEBA DE SISTEMA DE NOTIFICACIONES
        
        Este correo confirma que el sistema de notificaciones del
        Sistema Ganadero está correctamente configurado y funcionando.
        
        Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Este mensaje fue enviado manualmente como parte de una prueba
        de funcionamiento del sistema.
        """
        
        enviado = sistema_alarmas._enviar_notificacion_email(destinatario, asunto, mensaje)
        if enviado:
            print(f"[OK] Correo enviado exitosamente a {destinatario}")
        else:
            print(f"[ERROR] Error al enviar correo a {destinatario}")
        
        # 2. Verificar desparasitaciones pendientes
        print("\n--- Verificando desparasitaciones pendientes ---")
        try:
            notificaciones = sistema_alarmas.verificar_desparasitaciones_pendientes()
            print(f"Notificaciones de desparasitación enviadas: {notificaciones}")
        except Exception as e:
            print(f"Error al verificar desparasitaciones: {e}")
    
    print("\n=== PRUEBA DE NOTIFICACIONES FINALIZADA ===\n")

if __name__ == "__main__":
    probar_sistema_notificaciones()
