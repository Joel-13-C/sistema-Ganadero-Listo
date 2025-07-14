# Script para verificar y enviar notificaciones de vitaminizaciones pendientes
from src.database import get_db_connection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuración de correo
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'port': 587,
    'username': 'fernando05calero@gmail.com',
    'password': 'mqsl wlvi usjb kfzl',
    'from_email': 'fernando05calero@gmail.com'
}

# Función para enviar correo
def enviar_notificacion_email(destinatario, asunto, mensaje):
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['from_email']
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Adjuntar cuerpo del mensaje
        msg.attach(MIMEText(mensaje, 'plain'))
        
        print(f"Intentando login con: {EMAIL_CONFIG['username']}")
        
        # Iniciar sesión y enviar
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['port'])
        server.starttls()
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['from_email'], destinatario, text)
        server.quit()
        
        print(f"Notificación enviada exitosamente a {destinatario}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar notificación por correo: {e}")
        print(f"Error al enviar correo: {e}")
        return False

# Función principal para verificar vitaminizaciones pendientes
def verificar_vitaminizaciones():
    try:
        print("==== VERIFICANDO VITAMINIZACIONES PENDIENTES ====")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener configuración de alertas
        email_destino = EMAIL_CONFIG['username']
        dias_anticipacion = 7
        
        # Calcular fecha límite
        fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
        print(f"Buscando vitaminizaciones hasta: {fecha_limite.strftime('%Y-%m-%d')}")
        
        # Consulta para buscar vitaminizaciones pendientes
        query = """
            SELECT v.*, GROUP_CONCAT(a.id) as animal_ids, 
                   GROUP_CONCAT(a.nombre) as nombres_animales,
                   GROUP_CONCAT(a.numero_arete) as aretes_animales
            FROM vitaminizacion v
            JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id
            JOIN animales a ON va.animal_id = a.id
            WHERE v.proxima_aplicacion <= %s
            AND v.proxima_aplicacion >= CURDATE()
            GROUP BY v.id
        """
        
        cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
        vitaminizaciones = cursor.fetchall()
        
        print(f"Vitaminizaciones pendientes encontradas: {len(vitaminizaciones)}")
        
        notificaciones_enviadas = 0
        
        if vitaminizaciones:
            for v in vitaminizaciones:
                dias_restantes = (v['proxima_aplicacion'] - datetime.now().date()).days
                print(f"\nVitaminización: ID={v['id']}, Producto={v['producto']}")
                print(f"  Fecha próxima aplicación: {v['proxima_aplicacion']}")
                print(f"  Días restantes: {dias_restantes}")
                
                # Preparar lista de animales
                nombres_animales = v['nombres_animales'].split(',') if v['nombres_animales'] else []
                aretes_animales = v['aretes_animales'].split(',') if v['aretes_animales'] else []
                
                # Crear lista formateada
                lista_animales = ""
                for i in range(min(len(nombres_animales), len(aretes_animales))):
                    lista_animales += f"- {nombres_animales[i]} (Arete: {aretes_animales[i]})\n"
                
                # Asunto y mensaje
                asunto = f"ALERTA: Vitaminización pendiente - {v['producto']} en {dias_restantes} días"
                mensaje = f"""
                ALERTA DE VITAMINIZACIÓN PENDIENTE
                
                Hay una vitaminización programada próximamente.
                
                Detalles:
                - Producto: {v['producto']}
                - Fecha de aplicación: {v['proxima_aplicacion'].strftime('%d/%m/%Y')}
                - Días restantes: {dias_restantes}
                
                Animales que requieren vitaminización:
                {lista_animales}
                
                Por favor, prepare todo lo necesario para realizar la vitaminización.
                """
                
                # Enviar notificación
                enviado = enviar_notificacion_email(email_destino, asunto, mensaje)
                
                if enviado:
                    # Registrar la notificación
                    cursor.execute("""
                        INSERT INTO alarmas_enviadas
                        (tipo, referencia_id, email, asunto, mensaje, fecha_envio)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (
                        'vitaminizacion',
                        v['id'],
                        email_destino,
                        asunto,
                        mensaje
                    ))
                    conn.commit()
                    notificaciones_enviadas += 1
                    print(f"Notificación registrada en la base de datos")
        
        print(f"\nTotal de notificaciones enviadas: {notificaciones_enviadas}")
        return notificaciones_enviadas
    
    except Exception as e:
        logger.error(f"Error al verificar vitaminizaciones pendientes: {e}")
        print(f"Error: {e}")
        return 0
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    print("=== SERVICIO DE NOTIFICACIONES DE VITAMINIZACIONES ===")
    print("Fecha actual:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    verificar_vitaminizaciones()
