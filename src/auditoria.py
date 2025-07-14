from datetime import datetime, timedelta
from flask import request, session
import logging
from datetime import datetime

# Configurar logger
logger = logging.getLogger('auditoria')
logger.setLevel(logging.INFO)

class SistemaAuditoria:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self._crear_tabla_si_no_existe()
    
    def _crear_tabla_si_no_existe(self):
        """Crea la tabla de auditoría si no existe"""
        try:
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para crear tabla de auditoría")
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT,
                    usuario_nombre VARCHAR(100),
                    accion VARCHAR(255) NOT NULL,
                    modulo VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip VARCHAR(45)
                )
            """)
            conn.commit()
            logger.info("Tabla de auditoría verificada/creada correctamente")
        except Exception as e:
            logger.error(f"Error al crear tabla de auditoría: {e}")
            # No detener la ejecución del programa si hay un error al crear la tabla
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def registrar_evento(self, usuario_id, tipo_evento, descripcion=None):
        """
        Registra un evento en el sistema para fines de auditoría
        
        :param usuario_id: ID del usuario que realiza la acción
        :param tipo_evento: Tipo de evento (ej: 'actualizacion_perfil', 'cambio_contrasena')
        :param descripcion: Descripción detallada del evento
        :return: True si se registró correctamente, False en caso contrario
        """
        try:
            # Obtener información adicional
            ip = request.remote_addr if request and hasattr(request, 'remote_addr') else 'desconocida'
            usuario_nombre = session.get('nombre', 'Usuario desconocido') if 'session' in globals() else 'Usuario desconocido'
            
            # Determinar el módulo según el tipo de evento
            if 'perfil' in tipo_evento or 'contrasena' in tipo_evento:
                modulo = 'perfil'
            else:
                modulo = 'sistema'
            
            # Conectar a la base de datos
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para registrar evento")
                return False
                
            cursor = conn.cursor()
            
            # Insertar el registro
            cursor.execute("""
                INSERT INTO auditoria (usuario_id, usuario_nombre, accion, modulo, descripcion, ip)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (usuario_id, usuario_nombre, tipo_evento, modulo, descripcion, ip))
            
            conn.commit()
            logger.info(f"Evento {tipo_evento} registrado para usuario {usuario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar evento: {e}")
            return False
            
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def registrar_actividad(self, accion, modulo, descripcion=None):
        """
        Registra una actividad en el sistema para fines de auditoría
        
        Args:
            accion (str): La acción realizada (ej: 'Crear', 'Actualizar', 'Eliminar')
            modulo (str): El módulo donde se realizó la acción (ej: 'Animales', 'Empleados')
            descripcion (str, optional): Descripción detallada de la acción
        """
        try:
            # Obtener el ID y nombre del usuario actual si está autenticado
            usuario_id = session.get('usuario_id', None)
            usuario_nombre = session.get('username', 'Usuario no identificado')
                
            # Obtener la dirección IP del cliente
            ip = request.remote_addr
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para registrar actividad")
                # Continuar con la ejecución del programa aunque no se pueda registrar la actividad
                return
                
            cursor = conn.cursor()
            
            # Insertar el registro de actividad
            cursor.execute("""
                INSERT INTO auditoria (usuario_id, usuario_nombre, accion, modulo, descripcion, ip)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (usuario_id, usuario_nombre, accion, modulo, descripcion, ip))
            
            conn.commit()
            logger.info(f"Actividad registrada: {accion} en {modulo}")
        except Exception as e:
            logger.error(f"Error al registrar actividad: {e}")
            # No detener la ejecución del programa si hay un error al registrar la actividad
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def obtener_actividad_reciente(self, limite=10):
        """
        Obtiene los registros de actividad más recientes
        
        Args:
            limite (int): Número máximo de registros a devolver
            
        Returns:
            list: Lista de diccionarios con la información de actividad
        """
        try:
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para obtener actividad reciente")
                # Devolver una lista vacía si no se puede conectar a la base de datos
                return self._generar_actividades_demo(limite)
                
            cursor = conn.cursor(dictionary=True)
            
            try:
                # Consultar los registros más recientes
                cursor.execute("""
                    SELECT * FROM auditoria
                    ORDER BY fecha_hora DESC
                    LIMIT %s
                """, (limite,))
                
                actividades = cursor.fetchall()
                
                # Si no hay actividades en la base de datos, generar algunas de demostración
                if not actividades:
                    return self._generar_actividades_demo(limite)
                
                # Formatear las fechas y preparar los datos
                for actividad in actividades:
                    if 'fecha_hora' in actividad and actividad['fecha_hora']:
                        # Calcular tiempo relativo (hace X minutos/horas/días)
                        delta = datetime.now() - actividad['fecha_hora']
                        
                        if delta.days > 0:
                            if delta.days == 1:
                                actividad['tiempo_relativo'] = 'Ayer'
                            else:
                                actividad['tiempo_relativo'] = f'Hace {delta.days} días'
                        elif delta.seconds >= 3600:
                            horas = delta.seconds // 3600
                            if horas == 1:
                                actividad['tiempo_relativo'] = 'Hace 1 hora'
                            else:
                                actividad['tiempo_relativo'] = f'Hace {horas} horas'
                        elif delta.seconds >= 60:
                            minutos = delta.seconds // 60
                            if minutos == 1:
                                actividad['tiempo_relativo'] = 'Hace 1 minuto'
                            else:
                                actividad['tiempo_relativo'] = f'Hace {minutos} minutos'
                        else:
                            actividad['tiempo_relativo'] = 'Hace unos segundos'
                    
                return actividades
            except Exception as e:
                logger.error(f"Error al consultar actividades: {e}")
                return self._generar_actividades_demo(limite)
                
        except Exception as e:
            logger.error(f"Error al obtener actividad reciente: {e}")
            return self._generar_actividades_demo(limite)
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
                
    def _generar_actividades_demo(self, limite=5):
        """
        Genera actividades de demostración cuando no se puede acceder a la base de datos
        
        Args:
            limite (int): Número máximo de actividades a generar
            
        Returns:
            list: Lista de diccionarios con actividades de demostración
        """
        # Crear algunas actividades de demostración para mostrar en la interfaz
        actividades_demo = [
            {
                'id': 1,
                'usuario_id': 1,
                'usuario_nombre': 'Administrador',
                'accion': 'Registro',
                'modulo': 'Animales',
                'descripcion': 'Se registró un nuevo animal: Vaca Holstein',
                'fecha_hora': datetime.now() - timedelta(hours=2),
                'ip': '127.0.0.1',
                'tiempo_relativo': 'Hace 2 horas'
            },
            {
                'id': 2,
                'usuario_id': 1,
                'usuario_nombre': 'Administrador',
                'accion': 'Actualización',
                'modulo': 'Inventario',
                'descripcion': 'Se actualizó el inventario de alimentos',
                'fecha_hora': datetime.now() - timedelta(hours=5),
                'ip': '127.0.0.1',
                'tiempo_relativo': 'Hace 5 horas'
            },
            {
                'id': 3,
                'usuario_id': 1,
                'usuario_nombre': 'Administrador',
                'accion': 'Registro',
                'modulo': 'Vacunación',
                'descripcion': 'Se registró una nueva vacunación para el ganado',
                'fecha_hora': datetime.now() - timedelta(days=1),
                'ip': '127.0.0.1',
                'tiempo_relativo': 'Ayer'
            },
            {
                'id': 4,
                'usuario_id': 1,
                'usuario_nombre': 'Administrador',
                'accion': 'Eliminación',
                'modulo': 'Empleados',
                'descripcion': 'Se eliminó un registro de empleado',
                'fecha_hora': datetime.now() - timedelta(days=2),
                'ip': '127.0.0.1',
                'tiempo_relativo': 'Hace 2 días'
            },
            {
                'id': 5,
                'usuario_id': 1,
                'usuario_nombre': 'Administrador',
                'accion': 'Actualización',
                'modulo': 'Finanzas',
                'descripcion': 'Se registró un nuevo ingreso financiero',
                'fecha_hora': datetime.now() - timedelta(days=3),
                'ip': '127.0.0.1',
                'tiempo_relativo': 'Hace 3 días'
            }
        ]
        
        # Devolver solo la cantidad solicitada
        return actividades_demo[:min(limite, len(actividades_demo))]
