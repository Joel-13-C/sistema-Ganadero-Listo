from datetime import datetime, timedelta
from flask import request, session
import logging
from datetime import datetime
import psycopg2.extras

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
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auditoria'
            """)
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS auditoria (
                        id SERIAL PRIMARY KEY,
                        usuario_id INT,
                        usuario_nombre VARCHAR(100),
                        accion VARCHAR(255) NOT NULL,
                        modulo VARCHAR(100) NOT NULL,
                        descripcion TEXT,
                        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip VARCHAR(45),
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    )
                """)
                conn.commit()
                logger.info("Tabla de auditoría creada correctamente")
            
        except Exception as e:
            logger.error(f"Error al crear tabla de auditoría: {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def registrar_actividad(self, accion, modulo, descripcion=None):
        """
        Registra una actividad en el sistema de auditoría
        
        Args:
            accion (str): Tipo de acción realizada
            modulo (str): Módulo donde se realizó la acción
            descripcion (str, optional): Descripción detallada de la acción
        """
        try:
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para registrar actividad")
                return
                
            cursor = conn.cursor()
            
            # Obtener información del usuario
            usuario_id = session.get('usuario_id')
            usuario_nombre = session.get('username')
            
            # Obtener IP del cliente
            ip = request.remote_addr
            
            cursor.execute("""
                INSERT INTO auditoria (
                    usuario_id, usuario_nombre, accion, 
                    modulo, descripcion, ip
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (usuario_id, usuario_nombre, accion, modulo, descripcion, ip))
            
            conn.commit()
            logger.info(f"Actividad registrada: {accion} en {modulo}")
            
        except Exception as e:
            logger.error(f"Error al registrar actividad: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def obtener_historial(self, limite=100):
        """
        Obtiene el historial de actividades
        
        Args:
            limite (int): Número máximo de registros a retornar
            
        Returns:
            list: Lista de actividades ordenadas por fecha descendente
        """
        try:
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para obtener historial")
                return []
                
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM auditoria 
                ORDER BY fecha_hora DESC 
                LIMIT %s
            """, (limite,))
            
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"Error al obtener historial: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
    
    def obtener_actividad_reciente(self, limite=5, usuario_id=None):
        """
        Obtiene las actividades más recientes para el dashboard
        
        Args:
            limite (int): Número máximo de registros a retornar
            usuario_id (int, optional): ID del usuario para filtrar actividades
            
        Returns:
            list: Lista de actividades recientes ordenadas por fecha descendente
        """
        try:
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para obtener actividad reciente")
                return []
                
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if usuario_id:
                # Filtrar por usuario específico
                cursor.execute("""
                    SELECT 
                        a.id,
                        a.accion,
                        a.modulo,
                        a.descripcion,
                        a.fecha_hora,
                        a.usuario_nombre,
                        a.ip
                    FROM auditoria a
                    WHERE a.usuario_id = %s
                    ORDER BY a.fecha_hora DESC 
                    LIMIT %s
                """, (usuario_id, limite))
            else:
                # Obtener todas las actividades
                cursor.execute("""
                    SELECT 
                        a.id,
                        a.accion,
                        a.modulo,
                        a.descripcion,
                        a.fecha_hora,
                        a.usuario_nombre,
                        a.ip
                    FROM auditoria a
                    ORDER BY a.fecha_hora DESC 
                    LIMIT %s
                """, (limite,))
            
            actividades = cursor.fetchall()
            
            # Formatear las fechas para mejor visualización
            for actividad in actividades:
                if actividad['fecha_hora']:
                    actividad['fecha_formato'] = actividad['fecha_hora'].strftime('%d/%m/%Y %H:%M')
                    # Calcular tiempo relativo
                    ahora = datetime.now()
                    diferencia = ahora - actividad['fecha_hora']
                    if diferencia.days > 0:
                        actividad['tiempo_relativo'] = f"Hace {diferencia.days} días"
                    elif diferencia.seconds > 3600:
                        horas = diferencia.seconds // 3600
                        actividad['tiempo_relativo'] = f"Hace {horas} horas"
                    elif diferencia.seconds > 60:
                        minutos = diferencia.seconds // 60
                        actividad['tiempo_relativo'] = f"Hace {minutos} minutos"
                    else:
                        actividad['tiempo_relativo'] = "Hace un momento"
                else:
                    actividad['fecha_formato'] = 'N/A'
                    actividad['tiempo_relativo'] = 'N/A'
            
            return actividades
            
        except Exception as e:
            logger.error(f"Error al obtener actividad reciente: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
