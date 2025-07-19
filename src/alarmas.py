import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
from flask import session
import os

import pg8000

# Configurar logger
logger = logging.getLogger('alarmas')
logger.setLevel(logging.INFO)

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

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
        
        # Configuración directa de correo electrónico
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'port': 587,
            'username': 'p2pacademy.oficial@gmail.com',
            'password': 'dtnf whvj oycf nhbb',
            'from_email': 'p2pacademy.oficial@gmail.com'
        }
        
        self._crear_tabla_si_no_existe()
        
    def _crear_tabla_si_no_existe(self):
        """La tabla de alarmas ya existe en la base de datos"""
        pass
    
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
                
            cursor = conn.cursor()
            
            # Obtener configuraciones de alarmas
            cursor.execute("""
                SELECT * FROM config_alarmas
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            configuraciones = dictfetchall(cursor)
            
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
            print("\n==== INICIANDO VERIFICACIÓN DE DESPARASITACIONES PENDIENTES ====\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar desparasitaciones pendientes")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor()
            
            # Obtener configuraciones de alarmas de desparasitación activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'desparasitacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = dictfetchall(cursor)
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
                    SELECT d.*, a.nombre as nombre_animal, a.numero_arete as arete_animal
                    FROM desparasitaciones d
                    JOIN animales a ON d.animal_id = a.id
                    WHERE d.fecha_proxima <= %s
                    AND d.fecha_proxima >= CURRENT_DATE
                    AND d.usuario_id = %s
                """
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                desparasitaciones = dictfetchall(cursor)
                print(f"Desparasitaciones pendientes encontradas: {len(desparasitaciones)}")
                
                if desparasitaciones:
                    print("\n==== DETALLES DE DESPARASITACIONES PENDIENTES ====")
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
                        dias_restantes = (desparasitacion['fecha_proxima'] - datetime.now().date()).days
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Desparasitación pendiente - {desparasitacion['producto']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f"""
                        ALERTA DE DESPARASITACIÓN PENDIENTE
                        
                        Hay una desparasitación programada próximamente.
                        
                        Detalles:
                        - Animal: {desparasitacion['nombre_animal']} (Arete: {desparasitacion['arete_animal']})
                        - Producto: {desparasitacion['producto']}
                        - Fecha de aplicación: {desparasitacion['fecha_proxima'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
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
            
            print(f"\n==== VERIFICACIÓN DE DESPARASITACIONES PENDIENTES FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar desparasitaciones pendientes: {e}")
            print(f"Error: {e}")
            return 0
    

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
                
            cursor = conn.cursor()
            
            # Obtener configuraciones de alarmas de parto activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'parto' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = dictfetchall(cursor)
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
            
            # Para cada configuración, buscar partos próximos
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                from datetime import datetime, timedelta
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando partos para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar animales con partos próximos
                query = """
                    SELECT a.*, r.fecha_parto_estimada, (r.fecha_parto_estimada - CURRENT_DATE) as dias_restantes
                    FROM animales a
                    JOIN reproduccion r ON a.id = r.animal_id
                    WHERE a.sexo = 'Hembra' 
                    AND r.fecha_parto_estimada IS NOT NULL
                    AND r.fecha_parto_estimada <= %s
                    AND r.fecha_parto_estimada >= CURRENT_DATE
                """
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                animales = dictfetchall(cursor)
                print(f"Animales con partos próximos encontrados: {len(animales)}")
                
                if animales:
                    print("\n==== DETALLES DE PARTOS PRÓXIMOS ====")
                    for a in animales:
                        print(f"Animal: {a['nombre']} (ID={a['id']}, Arete={a['numero_arete']})")
                        print(f"  Fecha estimada de parto: {a['fecha_parto_estimada']}")
                        print(f"  Días restantes: {a['dias_restantes']}")
                        print("  ----------------------------------------")
                
                if animales:
                    # Enviar notificaciones para estos animales
                    for animal in animales:
                        # Calcular días restantes
                        dias_restantes = animal['dias_restantes']
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Parto próximo - {animal['nombre']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f"""
                        ALERTA DE PARTO PRÓXIMO
                        
                        Hay un parto programado próximamente.
                        
                        Detalles:
                        - Animal: {animal['nombre']}
                        - Número de arete: {animal['numero_arete']}
                        - Fecha estimada de parto: {animal['fecha_parto_estimada'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Por favor, prepare todo lo necesario para atender el parto.
                        """
                        
                        # Enviar la notificación
                        print(f"Enviando notificación de parto a {email}:")
                        print(f"Asunto: {asunto}")
                        print(f"Descripción: {mensaje}")
                        
                        enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                        
                        if enviado:
                            # Registrar la notificación en la base de datos
                            try:
                                cursor.execute("""
                                    INSERT INTO alarmas_enviadas
                                    (tipo, referencia_id, email, mensaje, fecha_envio)
                                    VALUES (%s, %s, %s, %s, NOW())
                                """, (
                                    'parto',
                                    animal['id'],
                                    email,
                                    mensaje
                                ))
                                conn.commit()
                                notificaciones_enviadas += 1
                                print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
                            except Exception as e:
                                print(f"Error al registrar notificación: {e}")
            
            print(f"\n==== VERIFICACIÓN DE PARTOS PRÓXIMOS FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar partos próximos: {e}")
            print(f"Error: {e}")
            return 0

    def verificar_vacunaciones_pendientes(self):
        """
        Verifica si hay vacunaciones pendientes y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        """
        try:
            print("\n==== INICIANDO VERIFICACIÓN DE VACUNACIONES PENDIENTES ====\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar vacunaciones pendientes")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor()
            
            # Obtener configuraciones de alarmas de vacunación activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'vacunacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = dictfetchall(cursor)
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de vacunación activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de vacunación activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar vacunaciones pendientes
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando vacunaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar todas las vacunaciones pendientes
                query = """
                    SELECT rv.*, a.nombre as nombre_animal,
                           a.numero_arete as arete_animal,
                           v.nombre as tipo_vacuna
                    FROM registro_vacunas rv
                    JOIN animales a ON rv.animal_id = a.id
                    JOIN vacunas v ON rv.vacuna_id = v.id
                    WHERE rv.fecha_proxima <= %s
                    AND rv.fecha_proxima >= CURRENT_DATE
                    AND rv.usuario_id = %s
                """
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}, {usuario_id}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'), usuario_id))
                
                vacunaciones = dictfetchall(cursor)
                print(f"Vacunaciones pendientes encontradas: {len(vacunaciones)}")
                
                if vacunaciones:
                    print("\n==== DETALLES DE VACUNACIONES PENDIENTES ====")
                    for v in vacunaciones:
                        print(f"Animal: {v['nombre_animal']} (Arete: {v['arete_animal']})")
                        print(f"  Tipo de vacuna: {v['tipo_vacuna']}")
                        print(f"  Fecha próxima: {v['fecha_proxima']}")
                        print("  ----------------------------------------")
                
                # Procesar cada vacunación
                for vacunacion in vacunaciones:
                    tipo = vacunacion['tipo_vacuna']
                    nombre_animal = vacunacion['nombre_animal']
                    arete_animal = vacunacion['arete_animal']
                    
                    # Crear mensaje
                    asunto = f"Recordatorio de Vacunación - {tipo}"
                    mensaje = f"""
                    Recordatorio de vacunación próxima:
                    
                    Tipo: {tipo}
                    Fecha programada: {vacunacion['fecha_proxima']}
                    
                    Animal a vacunar:
                    - {nombre_animal} (Arete: {arete_animal})
                    
                    Observaciones: {vacunacion['observaciones'] if vacunacion['observaciones'] else 'Ninguna'}
                    """
                    
                    # Enviar la notificación
                    print(f"Enviando notificación de vacunación a {email}:")
                    print(f"Asunto: {asunto}")
                    print(f"Descripción: {mensaje}")
                    
                    enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                    
                    if enviado:
                        # Registrar la notificación en la base de datos
                        try:
                            cursor.execute("""
                                INSERT INTO alarmas_enviadas
                                (tipo, referencia_id, email, mensaje, fecha_envio)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (
                                tipo.lower(),
                                vacunacion['id'],
                                email,
                                mensaje
                            ))
                            conn.commit()
                            notificaciones_enviadas += 1
                            print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
                        except Exception as e:
                            print(f"Error al registrar notificación: {e}")
                
                print(f"\n==== VERIFICACIÓN DE VACUNACIONES PENDIENTES FINALIZADA ====")
                print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
                
                return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar vacunaciones pendientes: {e}")
            print(f"Error: {e}")
            return 0

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
                
            cursor = conn.cursor()
            
            # Obtener configuraciones de alarmas de vitaminización activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'vitaminizacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = dictfetchall(cursor)
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
                
                # Buscar todas las vitaminizaciones pendientes
                query = """
                    SELECT v.*, a.nombre as nombre_animal,
                           a.numero_arete as arete_animal
                    FROM vitaminizaciones v
                    JOIN animales a ON v.animal_id = a.id
                    WHERE v.fecha_proxima <= %s
                    AND v.fecha_proxima >= CURRENT_DATE
                    AND v.usuario_id = %s
                """
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}, {usuario_id}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'), usuario_id))
                
                vitaminizaciones = dictfetchall(cursor)
                print(f"Vitaminizaciones pendientes encontradas: {len(vitaminizaciones)}")
                
                if vitaminizaciones:
                    print("\n==== DETALLES DE VITAMINIZACIONES PENDIENTES ====")
                    for v in vitaminizaciones:
                        print(f"Animal: {v['nombre_animal']} (Arete: {v['arete_animal']})")
                        print(f"  Producto: {v['producto']}")
                        print(f"  Fecha próxima: {v['fecha_proxima']}")
                        print("  ----------------------------------------")
                
                # Procesar cada vitaminización
                for vitaminizacion in vitaminizaciones:
                    producto = vitaminizacion['producto']
                    nombre_animal = vitaminizacion['nombre_animal']
                    arete_animal = vitaminizacion['arete_animal']
                    
                    # Crear mensaje
                    asunto = f"Recordatorio de Vitaminización - {producto}"
                    mensaje = f"""
                    Recordatorio de vitaminización próxima:
                    
                    Producto: {producto}
                    Fecha programada: {vitaminizacion['fecha_proxima']}
                    
                    Animal a vitaminizar:
                    - {nombre_animal} (Arete: {arete_animal})
                    
                    Observaciones: {vitaminizacion['observaciones'] if vitaminizacion['observaciones'] else 'Ninguna'}
                    """
                    
                    # Enviar la notificación
                    print(f"Enviando notificación de vitaminización a {email}:")
                    print(f"Asunto: {asunto}")
                    print(f"Descripción: {mensaje}")
                    
                    enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                    
                    if enviado:
                        # Registrar la notificación en la base de datos
                        try:
                            cursor.execute("""
                                INSERT INTO alarmas_enviadas
                                (tipo, referencia_id, email, mensaje, fecha_envio)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (
                                'vitaminizacion',
                                vitaminizacion['id'],
                                email,
                                mensaje
                            ))
                            conn.commit()
                            notificaciones_enviadas += 1
                            print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
                        except Exception as e:
                            print(f"Error al registrar notificación: {e}")
                
                print(f"\n==== VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES FINALIZADA ====")
                print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
                
                return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar vitaminizaciones pendientes: {e}")
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
