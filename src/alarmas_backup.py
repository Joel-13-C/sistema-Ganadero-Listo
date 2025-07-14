import smtplib
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
        
        # Ya no es necesario cargar desde la BD porque la configuración está fija
        # self._cargar_config_email_desde_db()
        
    def _crear_tabla_si_no_existe(self):
        """Crea la tabla de alarmas si no existe"""
        try:
            print("\n==== VERIFICANDO TABLAS DE ALARMAS ====\n")
            
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
                    usuario_id INT NOT NULL,
                    tipo VARCHAR(50) NOT NULL,
                    referencia_id INT NOT NULL,
                    descripcion TEXT,
                    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    email VARCHAR(100) NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("Tablas de alarmas verificadas/creadas correctamente")
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
                    SET dias_anticipacion = %s, email = %s, activo = TRUE
                    WHERE usuario_id = %s AND tipo = %s
                """, (dias_anticipacion, email, usuario_id, tipo))
            else:
                # Crear nueva configuración
                cursor.execute("""
                    INSERT INTO config_alarmas (usuario_id, tipo, dias_anticipacion, email)
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
            print(f"Obteniendo configuración de alarmas para usuario_id: {usuario_id}")
            
            if not usuario_id:
                logger.error("No se pudo identificar al usuario para obtener configuración de alarmas")
                return {}
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para obtener configuración de alarmas")
                return {}
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuración de alarmas
            cursor.execute("""
                SELECT * FROM config_alarmas
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            config = cursor.fetchall()
            
            # Formatear resultado como diccionario
            result = {}
            for item in config:
                result[item['tipo']] = {
                    'dias_anticipacion': item['dias_anticipacion'],
                    'email': item['email'],
                    'activo': item['activo']
                }
            
            return result
        except Exception as e:
            logger.error(f"Error al obtener configuración de alarmas: {e}")
            return {}
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def verificar_partos_proximos(self):
        """
        Verifica si hay partos próximos y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        """
        try:
            print("\n==== INICIANDO VERIFICACIÓN DE PARTOS PRÓXIMOS ====\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar partos próximos")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas de parto activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'parto' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = cursor.fetchall()
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de parto activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de parto activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar gestaciones próximas a terminar
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando gestaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar gestaciones próximas a terminar
                query = """
                    SELECT g.*, a.nombre as nombre_animal, a.numero_arete
                    FROM gestaciones g
                    JOIN animales a ON g.animal_id = a.id
                    WHERE DATE_ADD(g.fecha_inseminacion, INTERVAL 283 DAY) <= %s
                    AND DATE_ADD(g.fecha_inseminacion, INTERVAL 283 DAY) >= CURDATE()
                    AND g.estado = 'En Gestación'
                """
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                gestaciones = cursor.fetchall()
                print(f"Gestaciones encontradas: {len(gestaciones)}")
                
                if gestaciones:
                    print("\n==== DETALLES DE GESTACIONES ENCONTRADAS ====")
                    for g in gestaciones:
                        fecha_parto_estimada = g['fecha_inseminacion'] + timedelta(days=283)
                        dias_restantes = (fecha_parto_estimada - datetime.now().date()).days
                        print(f"Gestación: ID={g['id']}, Animal={g['nombre_animal']}, Arete={g['numero_arete']}")
                        print(f"  Fecha inseminación: {g['fecha_inseminacion']}")
                        print(f"  Fecha parto estimada: {fecha_parto_estimada}")
                        print(f"  Días restantes: {dias_restantes}")
                        print("  ----------------------------------------")
                
                if gestaciones:
                    # Verificar si ya se enviaron notificaciones para estas gestaciones
                    for gestacion in gestaciones:
                        # Calcular fecha probable de parto y días restantes
                        fecha_parto_estimada = gestacion['fecha_inseminacion'] + timedelta(days=283)
                        dias_restantes = (fecha_parto_estimada - datetime.now().date()).days
                        
                        # Crear mensaje detallado
                        descripcion = f"""
                        ALERTA DE PARTO PRÓXIMO
                        
                        La vaca {gestacion['nombre_animal']} (Arete: {gestacion['numero_arete']}) está próxima a parir.
                        
                        Detalles:
                        - Fecha de inseminación: {gestacion['fecha_inseminacion'].strftime('%d/%m/%Y')}
                        - Fecha probable de parto: {fecha_parto_estimada.strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Por favor, prepare todo lo necesario para atender el parto.
                        """
                        
                        # Enviar notificación por correo
                        asunto = f"ALERTA: Parto próximo - Vaca {gestacion['nombre_animal']} en {dias_restantes} días"
                        
                        print(f"\nEnviando notificación de parto a {email}:")
                        print(f"Asunto: {asunto}")
                        print(f"Descripción: {descripcion}")
                        
                        if self._enviar_notificacion_email(email, asunto, descripcion):
                            # Registrar notificación enviada
                            cursor.execute("""
                                INSERT INTO alarmas_enviadas (usuario_id, tipo, referencia_id, descripcion, email)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (usuario_id, 'parto', gestacion['id'], descripcion, email))
                            
                            conn.commit()
                            notificaciones_enviadas += 1
                            print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
            
            print(f"\n==== VERIFICACIÓN DE PARTOS PRÓXIMOS FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
    def verificar_vitaminizaciones_pendientes(self):
        """
        Verifica si hay vitaminizaciones pendientes y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        """
        try:
            print("\n==== INICIANDO VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES ====\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar vitaminizaciones pendientes")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas de vitaminización activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'vitaminizacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = cursor.fetchall()
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de vitaminización activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de vitaminización activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar vitaminizaciones pendientes
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando vitaminizaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar vitaminizaciones pendientes
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
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                vitaminizaciones = cursor.fetchall()
                print(f"Vitaminizaciones pendientes encontradas: {len(vitaminizaciones)}")
                
                if vitaminizaciones:
                    print("\n==== DETALLES DE VITAMINIZACIONES PENDIENTES ====\n")
                    for v in vitaminizaciones:
                        dias_restantes = (v['proxima_aplicacion'] - datetime.now().date()).days
                        print(f"Vitaminización: ID={v['id']}, Producto={v['producto']}")
                        print(f"  Fecha próxima aplicación: {v['proxima_aplicacion']}")
                        print(f"  Días restantes: {dias_restantes}")
                        print(f"  Animales: {v['nombres_animales']}")
                        print("  ----------------------------------------")
                
                if vitaminizaciones:
                    # Enviar notificaciones para estas vitaminizaciones
                    for vitaminizacion in vitaminizaciones:
                        # Calcular días restantes
                        dias_restantes = (vitaminizacion['proxima_aplicacion'] - datetime.now().date()).days
                        
                        # Preparar lista de animales
                        nombres_animales = vitaminizacion['nombres_animales'].split(',') if vitaminizacion['nombres_animales'] else []
                        aretes_animales = vitaminizacion['aretes_animales'].split(',') if vitaminizacion['aretes_animales'] else []
                        
                        # Crear lista formateada de animales
                        lista_animales = ""
                        for i in range(min(len(nombres_animales), len(aretes_animales))):
                            lista_animales += f"- {nombres_animales[i]} (Arete: {aretes_animales[i]})\n"
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Vitaminización pendiente - {vitaminizacion['producto']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f"""
                        ALERTA DE VITAMINIZACIÓN PENDIENTE
                        
                        Hay una vitaminización programada próximamente.
                        
                        Detalles:
                        - Producto: {vitaminizacion['producto']}
                        - Fecha de aplicación: {vitaminizacion['proxima_aplicacion'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Animales que requieren vitaminización:
                        {lista_animales}
                        
                        Por favor, prepare todo lo necesario para realizar la vitaminización.
                        """
                        
                        # Enviar la notificación
                        print(f"Enviando notificación de vitaminización a {email}:")
                        print(f"Asunto: {asunto}")
                        print(f"Mensaje: {mensaje[:100]}...")
                        
                        enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                        
                        if enviado:
                            # Registrar la notificación en la base de datos
                            cursor.execute("""
                                INSERT INTO alarmas_enviadas
                                (tipo, referencia_id, email, asunto, mensaje, fecha_envio)
                                VALUES (%s, %s, %s, %s, %s, NOW())
                            """, (
                                'vitaminizacion',
                                vitaminizacion['id'],
                                email,
                                asunto,
                                mensaje
                            ))
                            conn.commit()
                            notificaciones_enviadas += 1
                            print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
            
            cursor.close()
            conn.close()
            
            print("\n==== VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES FINALIZADA ====\n")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar vitaminizaciones pendientes: {e}")
            print(f"Error: {e}")
            return 0
    
        except Exception as e:
            logger.error(f"Error al verificar desparasitaciones pendientes: {e}")
            print(f"Error al verificar desparasitaciones pendientes: {e}")
            return 0
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
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
            # Verificar configuración de correo
            if not self.email_config['username'] or not self.email_config['password']:
                logger.error("Falta configuración de correo electrónico")
                return False
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = destinatario
            msg['Subject'] = asunto
            
            # Agregar cuerpo del mensaje con mejor formato
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                    h2 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .alert {{ background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Sistema Ganadero - Notificación Importante</h2>
                    <div class="alert">
                        <p><strong>{mensaje}</strong></p>
                    </div>
                    <p>Esta notificación ha sido generada automáticamente por el Sistema Ganadero.</p>
                    <p>Por favor, ingrese al sistema para obtener más detalles y tomar las acciones necesarias.</p>
                    <div class="footer">
                        <p>Este es un correo automático, por favor no responda a este mensaje.</p>
                        <p> {datetime.now().year} Sistema Ganadero - Todos los derechos reservados</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # Conectar al servidor SMTP
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port'])
            server.starttls()
            
            # Imprimir información de depuración sobre el intento de login
            print(f"Intentando login con: {self.email_config['username']}")
            
            server.login(self.email_config['username'], self.email_config['password'])
            
            # Enviar correo
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Notificación enviada a {destinatario}: {asunto}")
            print(f"Notificación enviada exitosamente a {destinatario}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar notificación por correo: {e}")
            print(f"Error al enviar notificación por correo: {e}")
            return False
    
    def configurar_email(self, smtp_server, port, username, password, from_email=None):
        """
        Configura los parámetros para el envío de correos electrónicos y los guarda en la base de datos
        
        Args:
            smtp_server (str): Servidor SMTP
            port (int): Puerto del servidor SMTP
            username (str): Nombre de usuario para autenticación SMTP
            password (str): Contraseña para autenticación SMTP
            from_email (str, optional): Correo electrónico remitente
        
        Returns:
            bool: True si se configuró correctamente, False en caso contrario
        """
        try:
            # Actualizar la configuración en memoria
            self.email_config = {
                'smtp_server': smtp_server,
                'port': port,
                'username': username,
                'password': password,
                'from_email': from_email or username
            }
            
            # Obtener el ID del usuario actual
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                logger.error("No se pudo identificar al usuario para guardar configuración de correo")
                return False
            
            # Guardar la configuración en la base de datos
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para guardar configuración de correo")
                return False
                
            cursor = conn.cursor()
            
            # Verificar si ya existe una configuración para este usuario
            cursor.execute("""
                SELECT id FROM config_email
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            result = cursor.fetchone()
            
            if result:
                # Actualizar configuración existente
                cursor.execute("""
                    UPDATE config_email
                    SET smtp_server = %s, port = %s, username = %s, password = %s, from_email = %s
                    WHERE usuario_id = %s
                """, (smtp_server, port, username, password, from_email or username, usuario_id))
            else:
                # Crear nueva configuración
                cursor.execute("""
                    INSERT INTO config_email (usuario_id, smtp_server, port, username, password, from_email)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (usuario_id, smtp_server, port, username, password, from_email or username))
            
            conn.commit()
            logger.info(f"Configuración de correo electrónico guardada en la base de datos para el usuario {usuario_id}")
            return True
        except Exception as e:
            logger.error(f"Error al configurar correo electrónico: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
                
    def _cargar_config_email_desde_db(self):
        """
        Carga la configuración de correo electrónico desde la base de datos
        """
        try:
            # Obtener el ID del usuario actual
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                logger.info("No hay usuario en sesión para cargar configuración de correo")
                return
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para cargar configuración de correo")
                return
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuración de correo
            cursor.execute("""
                SELECT * FROM config_email
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            config = cursor.fetchone()
            
            if config:
                self.email_config = {
                    'smtp_server': config['smtp_server'],
                    'port': config['port'],
                    'username': config['username'],
                    'password': config['password'],
                    'from_email': config['from_email'] or config['username']
                }
                logger.info(f"Configuración de correo electrónico cargada desde la base de datos para el usuario {usuario_id}")
        except Exception as e:
            logger.error(f"Error al cargar configuración de correo electrónico: {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
