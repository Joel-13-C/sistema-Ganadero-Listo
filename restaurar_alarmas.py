# Script para restaurar el archivo de alarmas original sin la función que está causando problemas
import os
import shutil

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')
backup_path = os.path.join(os.getcwd(), 'src', 'alarmas_backup.py')

# Crear una copia de seguridad si no existe
if not os.path.exists(backup_path):
    shutil.copy2(alarmas_path, backup_path)
    print(f"Se ha creado una copia de seguridad en {backup_path}")

# Copiar el contenido original antes de las modificaciones
try:
    with open(backup_path, 'r', encoding='utf-8') as backup_file:
        original_content = backup_file.read()
        
    with open(alarmas_path, 'w', encoding='utf-8') as file:
        file.write(original_content)
        
    print(f"Se ha restaurado el archivo {alarmas_path} a su estado original")
except FileNotFoundError:
    print(f"No se encontró el archivo de respaldo {backup_path}")
    
    # Crear un archivo limpio con el contenido mínimo
    with open(alarmas_path, 'w', encoding='utf-8') as file:
        file.write("""import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
from flask import session

# Configurar logger
logger = logging.getLogger('alarmas')
logger.setLevel(logging.INFO)

class SistemaAlarmas:
    def __init__(self, db_connection, email_config=None):
        \"\"\"
        Inicializa el sistema de alarmas
        
        Args:
            db_connection: Función para obtener conexión a la base de datos
            email_config (dict): Configuración para el envío de correos
                                (smtp_server, port, username, password, from_email)
        \"\"\"
        self.db_connection = db_connection
        
        # Configuración de correo electrónico fija para evitar pérdida al reiniciar
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'port': 587,
            'username': 'fernando05calero@gmail.com',  # Correo configurado directamente
            'password': 'mqsl wlvi usjb kfzl',  # Contraseña de aplicación configurada directamente
            'from_email': 'fernando05calero@gmail.com'
        }
        
        self._crear_tabla_si_no_existe()
        
        # Ya no es necesario cargar desde la BD porque la configuración está fija
        # self._cargar_config_email_desde_db()
""")
        print("Se ha creado un archivo de alarmas básico")
