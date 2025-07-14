# Script para enviar automáticamente todas las notificaciones pendientes
import sys
import os
import datetime
from flask import Flask, session

# Añadir ruta actual al path de Python
sys.path.append(os.getcwd())

# Importar los componentes necesarios
from src.alarmas import SistemaAlarmas
from src.database import get_db_connection

def enviar_todas_notificaciones():
    print("\n====== ENVIANDO TODAS LAS NOTIFICACIONES PENDIENTES ======\n")
    
    # Crear una aplicación Flask para simular el entorno
    app = Flask(__name__)
    app.secret_key = "sistema_ganadero_secret_key"
    
    # Simular una sesión de usuario
    with app.test_request_context():
        # Establecer datos de sesión (simulando un usuario logueado)
        session['usuario_id'] = 1
        session['username'] = 'admin'
        
        # Inicializar el sistema de alarmas con la función de conexión
        print("Inicializando sistema de alarmas...")
        sistema_alarmas = SistemaAlarmas(get_db_connection)
        
        total_notificaciones = 0
        
        # 1. Verificar partos próximos
        print("\n------ VERIFICANDO PARTOS PRÓXIMOS ------")
        try:
            notificaciones_partos = sistema_alarmas.verificar_partos_proximos()
            print(f"Notificaciones de partos enviadas: {notificaciones_partos}")
            total_notificaciones += notificaciones_partos
        except Exception as e:
            print(f"Error al verificar partos próximos: {e}")
        
        # 2. Verificar vacunaciones pendientes
        print("\n------ VERIFICANDO VACUNACIONES PENDIENTES ------")
        try:
            notificaciones_vacunaciones = sistema_alarmas.verificar_vacunaciones_pendientes()
            print(f"Notificaciones de vacunaciones enviadas: {notificaciones_vacunaciones}")
            total_notificaciones += notificaciones_vacunaciones
        except Exception as e:
            print(f"Error al verificar vacunaciones pendientes: {e}")
        
        # 3. Verificar desparasitaciones pendientes
        print("\n------ VERIFICANDO DESPARASITACIONES PENDIENTES ------")
        try:
            notificaciones_desparasitaciones = sistema_alarmas.verificar_desparasitaciones_pendientes()
            print(f"Notificaciones de desparasitaciones enviadas: {notificaciones_desparasitaciones}")
            total_notificaciones += notificaciones_desparasitaciones
        except Exception as e:
            print(f"Error al verificar desparasitaciones pendientes: {e}")
        
        # Enviar resumen de notificaciones
        print("\n------ ENVIANDO RESUMEN DE NOTIFICACIONES ------")
        try:
            if total_notificaciones > 0:
                destinatario = sistema_alarmas.email_config['username']
                fecha_hora = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                asunto = f"Resumen de notificaciones del Sistema Ganadero - {fecha_hora}"
                
                mensaje = f"""
                RESUMEN DE NOTIFICACIONES DEL SISTEMA GANADERO
                
                Fecha y hora: {fecha_hora}
                
                Se han enviado las siguientes notificaciones:
                - Partos próximos: {notificaciones_partos}
                - Vacunaciones pendientes: {notificaciones_vacunaciones}
                - Desparasitaciones pendientes: {notificaciones_desparasitaciones}
                
                Total de notificaciones: {total_notificaciones}
                
                Este es un mensaje automático generado por el Sistema Ganadero.
                """
                
                enviado = sistema_alarmas._enviar_notificacion_email(destinatario, asunto, mensaje)
                if enviado:
                    print(f"Resumen de notificaciones enviado exitosamente a {destinatario}")
                else:
                    print("Error al enviar el resumen de notificaciones")
            else:
                print("No se encontraron notificaciones pendientes para enviar")
        except Exception as e:
            print(f"Error al enviar resumen de notificaciones: {e}")
    
    print(f"\n====== PROCESO DE ENVÍO DE NOTIFICACIONES FINALIZADO ======")
    print(f"Total de notificaciones enviadas: {total_notificaciones}")

if __name__ == "__main__":
    enviar_todas_notificaciones()
