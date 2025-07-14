# Script para corregir problemas de indentación en el archivo alarmas.py
import os

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')

# Leer el contenido completo del archivo
with open(alarmas_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Recrear el archivo con la estructura correcta
with open(alarmas_path, 'w', encoding='utf-8') as file:
    file.write('''import smtplib
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
        """
        Inicializa el sistema de alarmas
        
        Args:
            db_connection: Función para obtener conexión a la base de datos
            email_config (dict): Configuración para el envío de correos
                                (smtp_server, port, username, password, from_email)
        """
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
        
    def _crear_tabla_si_no_existe(self):
        """Crea la tabla de alarmas si no existe"""
        try:
            print("\\n==== VERIFICANDO TABLAS DE ALARMAS ====\\n")
            
            # Intentar diferentes configuraciones de conexión
            conexiones_a_probar = [
                {"host": "localhost", "user": "root", "password": "1234"},  # Contraseña confirmada que funciona
                {"host": "localhost", "user": "root", "password": ""},
                {"host": "localhost", "user": "root", "password": "root"},
                {"host": "localhost", "user": "root", "password": "admin"},
                {"host": "localhost", "user": "admin", "password": "admin"}
            ]
            
            conn = None
            for config in conexiones_a_probar:
                try:
                    import mysql.connector
                    conn = mysql.connector.connect(
                        **config,
                        database="sistema_ganadero"
                    )
                    if conn.is_connected():
                        print(f"Conexión exitosa con: {config}")
                        break
                except Exception as e:
                    print(f"Error al conectar con: {config}. Error: {e}")
                    continue
            
            if not conn or not conn.is_connected():
                logger.error("No se pudo conectar a la base de datos para crear tabla de alarmas")
                print("Error: No se pudo conectar a la base de datos")
                return
                
            cursor = conn.cursor()
            
            # Verificar si la tabla config_alarmas existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'sistema_ganadero' 
                AND table_name = 'config_alarmas'
            """)
            tabla_existe = cursor.fetchone()[0] > 0
            print(f"¿Existe la tabla config_alarmas?: {tabla_existe}")
            
            # Tabla para configuración de alarmas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_alarmas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    tipo VARCHAR(50) NOT NULL,
                    dias_anticipacion INT DEFAULT 7,
                    email VARCHAR(100) NOT NULL,
                    activo BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla para registro de alarmas enviadas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alarmas_enviadas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo VARCHAR(50) NOT NULL,
                    referencia_id INT,
                    email VARCHAR(100) NOT NULL,
                    mensaje TEXT,
                    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            print("Tablas de alarmas verificadas/creadas correctamente")
            
        except Exception as e:
            logger.error(f"Error al crear tablas de alarmas: {e}")
            print(f"Error al crear tablas de alarmas: {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def configurar_alarma(self, tipo, email, dias_anticipacion=7):
        """
        Configura una alarma para un usuario
        
        Args:
            tipo (str): Tipo de alarma ('parto', 'vacunacion')
            email (str): Correo electrónico para recibir notificaciones
            dias_anticipacion (int): Días de anticipación para la notificación
        
        Returns:
            bool: True si se configuró correctamente, False en caso contrario
        """
        try:
            # Obtener el ID del usuario actual
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                logger.error("No se pudo identificar al usuario para configurar alarma")
                return False
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para configurar alarma")
                return False
                
            cursor = conn.cursor()
            
            # Verificar si ya existe una configuración para este usuario y tipo
            cursor.execute("""
                SELECT id FROM config_alarmas
                WHERE usuario_id = %s AND tipo = %s
            """, (usuario_id, tipo))
            
            result = cursor.fetchone()
            
            if result:
                # Actualizar configuración existente
                cursor.execute("""
                    UPDATE config_alarmas
                    SET email = %s, dias_anticipacion = %s, activo = TRUE
                    WHERE usuario_id = %s AND tipo = %s
                """, (email, dias_anticipacion, usuario_id, tipo))
            else:
                # Crear nueva configuración
                cursor.execute("""
                    INSERT INTO config_alarmas
                    (usuario_id, tipo, dias_anticipacion, email)
                    VALUES (%s, %s, %s, %s)
                """, (usuario_id, tipo, dias_anticipacion, email))
            
            conn.commit()
            logger.info(f"Alarma de tipo {tipo} configurada para el usuario {usuario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al configurar alarma: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def desactivar_alarma(self, tipo):
        """
        Desactiva una alarma para un usuario
        
        Args:
            tipo (str): Tipo de alarma ('parto', 'vacunacion')
        
        Returns:
            bool: True si se desactivó correctamente, False en caso contrario
        """
        try:
            # Obtener el ID del usuario actual
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                logger.error("No se pudo identificar al usuario para desactivar alarma")
                return False
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para desactivar alarma")
                return False
                
            cursor = conn.cursor()
            
            # Desactivar la alarma
            cursor.execute("""
                UPDATE config_alarmas
                SET activo = FALSE
                WHERE usuario_id = %s AND tipo = %s
            """, (usuario_id, tipo))
            
            conn.commit()
            logger.info(f"Alarma de tipo {tipo} desactivada para el usuario {usuario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al desactivar alarma: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def obtener_configuracion_alarmas(self):
        """
        Obtiene la configuración de alarmas del usuario actual
        
        Returns:
            dict: Diccionario con la configuración de alarmas
        """
        try:
            # Obtener el ID del usuario actual
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                logger.info("No hay usuario en sesión para obtener configuración de alarmas")
                return {}
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para obtener configuración de alarmas")
                return {}
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas
            cursor.execute("""
                SELECT * FROM config_alarmas
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            configuraciones = cursor.fetchall()
            
            # Organizar por tipo
            config = {}
            for c in configuraciones:
                config[c['tipo']] = {
                    'activo': c['activo'],
                    'email': c['email'],
                    'dias_anticipacion': c['dias_anticipacion']
                }
            
            cursor.close()
            conn.close()
            
            return config
            
        except Exception as e:
            logger.error(f"Error al obtener configuración de alarmas: {e}")
            return {}
    
    def verificar_desparasitaciones_pendientes(self):
        """
        Verifica si hay desparasitaciones pendientes y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        """
        try:
            print("\\n==== INICIANDO VERIFICACIÓN DE DESPARASITACIONES PENDIENTES ====\\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar desparasitaciones pendientes")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas de desparasitación activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'desparasitacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = cursor.fetchall()
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de desparasitación activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de desparasitación activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar desparasitaciones pendientes
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando desparasitaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar desparasitaciones pendientes
                query = """
                    SELECT d.*, GROUP_CONCAT(a.id) as animal_ids, 
                           GROUP_CONCAT(a.nombre) as nombres_animales,
                           GROUP_CONCAT(a.numero_arete) as aretes_animales
                    FROM desparasitacion d
                    JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id
                    JOIN animales a ON da.animal_id = a.id
                    WHERE d.proxima_aplicacion <= %s
                    AND d.proxima_aplicacion >= CURDATE()
                    GROUP BY d.id
                """
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                desparasitaciones = cursor.fetchall()
                print(f"Desparasitaciones pendientes encontradas: {len(desparasitaciones)}")
                
                if desparasitaciones:
                    print("\\n==== DETALLES DE DESPARASITACIONES PENDIENTES ====")
                    for d in desparasitaciones:
                        dias_restantes = (d['proxima_aplicacion'] - datetime.now().date()).days
                        print(f"Desparasitación: ID={d['id']}, Producto={d['producto']}")
                        print(f"  Fecha próxima aplicación: {d['proxima_aplicacion']}")
                        print(f"  Días restantes: {dias_restantes}")
                        print(f"  Animales: {d['nombres_animales']}")
                        print("  ----------------------------------------")
                
                if desparasitaciones:
                    # Enviar notificaciones para estas desparasitaciones
                    for desparasitacion in desparasitaciones:
                        # Calcular días restantes
                        dias_restantes = (desparasitacion['proxima_aplicacion'] - datetime.now().date()).days
                        
                        # Preparar lista de animales
                        nombres_animales = desparasitacion['nombres_animales'].split(',') if desparasitacion['nombres_animales'] else []
                        aretes_animales = desparasitacion['aretes_animales'].split(',') if desparasitacion['aretes_animales'] else []
                        
                        # Crear lista formateada de animales
                        lista_animales = ""
                        for i in range(min(len(nombres_animales), len(aretes_animales))):
                            lista_animales += f"- {nombres_animales[i]} (Arete: {aretes_animales[i]})\\n"
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Desparasitación pendiente - {desparasitacion['producto']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f"""
                        ALERTA DE DESPARASITACIÓN PENDIENTE
                        
                        Hay una desparasitación programada próximamente.
                        
                        Detalles:
                        - Producto: {desparasitacion['producto']}
                        - Fecha de aplicación: {desparasitacion['proxima_aplicacion'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Animales que requieren desparasitación:
                        {lista_animales}
                        
                        Por favor, prepare todo lo necesario para realizar la desparasitación.
                        """
                        
                        # Enviar la notificación
                        print(f"Enviando notificación de desparasitación a {email}:")
                        print(f"Asunto: {asunto}")
                        print(f"Descripción: {mensaje}")
                        
                        enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                        
                        if enviado:
                            # Registrar la notificación en la base de datos
                            cursor.execute("""
                                INSERT INTO alarmas_enviadas
                                (tipo, referencia_id, email, mensaje, fecha_envio)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (
                                'desparasitacion',
                                desparasitacion['id'],
                                email,
                                mensaje
                            ))
                            conn.commit()
                            notificaciones_enviadas += 1
                            print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
            
            print(f"\\n==== VERIFICACIÓN DE DESPARASITACIONES PENDIENTES FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar desparasitaciones pendientes: {e}")
            print(f"Error: {e}")
            return 0
    
    def _enviar_notificacion_email(self, destinatario, asunto, mensaje):
        """
        Envía una notificación por correo electrónico
        
        Args:
            destinatario (str): Correo electrónico del destinatario
            asunto (str): Asunto del correo
            mensaje (str): Contenido del correo
        
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = destinatario
            msg['Subject'] = asunto
            
            # Adjuntar cuerpo del mensaje
            msg.attach(MIMEText(mensaje, 'plain'))
            
            print(f"Intentando login con: {self.email_config['username']}")
            
            # Iniciar sesión y enviar
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['from_email'], destinatario, text)
            server.quit()
            
            print(f"Notificación enviada exitosamente a {destinatario}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar notificación por correo: {e}")
            print(f"Error al enviar correo: {e}")
            return False
''')

print("Archivo alarmas.py recreado correctamente con indentación correcta")
