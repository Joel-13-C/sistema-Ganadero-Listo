# Script para verificar que las notificaciones automáticas se envíen correctamente
import sys
import os
import datetime
from flask import Flask, session

# Agregar directorio actual al path
sys.path.append(os.getcwd())

# Importar las clases necesarias
from src.alarmas import SistemaAlarmas
from src.database import DatabaseConnection

def verificar_notificaciones_automaticas():
    print("\n=== VERIFICANDO FUNCIONAMIENTO DE NOTIFICACIONES AUTOMÁTICAS ===\n")
    
    # Crear una aplicación Flask similar a la de app.py
    app = Flask(__name__)
    app.secret_key = 'clave_secreta_sistema_ganadero'
    
    # Simular sesión activa (necesario para algunas verificaciones)
    with app.test_request_context():
        # Configurar sesión con un usuario
        session['usuario_id'] = 1
        session['username'] = 'admin'
        
        # Inicializar conexión a la base de datos con la app
        db_connection = DatabaseConnection(app)
        db_connection.set_connection_params(
            host="localhost",
            user="root",
            password="1234",
            database="sistema_ganadero"
        )
        
        # Función para obtener conexión
        def get_db_connection():
            return db_connection.get_connection()
        
        # Inicializar sistema de alarmas
        print("Inicializando sistema de alarmas...")
        alarmas = SistemaAlarmas(get_db_connection)
        
        # 1. Verificar desparasitaciones pendientes
        print("\n--- Verificando desparasitaciones pendientes ---")
        try:
            notificaciones_desparasitacion = alarmas.verificar_desparasitaciones_pendientes()
            print(f"Notificaciones de desparasitación enviadas: {notificaciones_desparasitacion}")
        except Exception as e:
            print(f"Error al verificar desparasitaciones: {e}")
        
        # 2. Enviar correo de prueba para verificar la configuración
        print("\n--- Enviando correo de prueba ---")
        try:
            destinatario = alarmas.email_config['username']
            asunto = "Prueba de Sistema de Notificaciones Automáticas"
            fecha_hora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            mensaje = f"""
            PRUEBA DE SISTEMA DE NOTIFICACIONES AUTOMÁTICAS
            
            Este correo confirma que el sistema de notificaciones automáticas
            del Sistema Ganadero está funcionando correctamente.
            
            Fecha y hora: {fecha_hora}
            
            Cuando ocurran eventos importantes (desparasitaciones, vacunaciones,
            partos próximos, etc.) el sistema enviará notificaciones automáticas
            a este correo electrónico.
            """
            
            enviado = alarmas._enviar_notificacion_email(destinatario, asunto, mensaje)
            if enviado:
                print(f"✅ Correo de prueba enviado exitosamente a {destinatario}")
            else:
                print("❌ Error al enviar correo de prueba")
        except Exception as e:
            print(f"Error al enviar correo de prueba: {e}")
    
    print("\n=== VERIFICACIÓN DE NOTIFICACIONES AUTOMÁTICAS FINALIZADA ===\n")

if __name__ == "__main__":
    verificar_notificaciones_automaticas()
