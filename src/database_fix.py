import mysql.connector
import logging
import hashlib
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('database')

class DatabaseConnection:
    def __init__(self, app=None):
        self.app = app
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '1234',
            'database': 'sistema_ganadero'
        }
        
    def get_connection(self):
        """
        Obtiene una conexión a la base de datos.
        
        :return: Objeto de conexión a la base de datos
        """
        try:
            connection = mysql.connector.connect(**self.config)
            connection.autocommit = False
            return connection
        except mysql.connector.Error as err:
            logger.error(f"Error al conectar a la base de datos: {err}")
            raise
    
    def actualizar_perfil_usuario(self, usuario_id, nombre, email, telefono, foto_path=None, cargo=None, direccion=None):
        """
        Actualiza la información del perfil de un usuario.
        
        :param usuario_id: ID del usuario
        :param nombre: Nombre completo del usuario
        :param email: Correo electrónico del usuario
        :param telefono: Número de teléfono del usuario
        :param foto_path: Ruta de la foto de perfil (opcional)
        :param cargo: Cargo del usuario en la empresa (opcional)
        :param direccion: Dirección del usuario (opcional)
        :return: True si se actualizó correctamente, False en caso contrario
        """
        connection = None
        try:
            # Primero verificamos si las columnas cargo y dirección existen
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                # Verificar si la columna cargo existe
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'usuarios' 
                    AND COLUMN_NAME = 'cargo'
                """)
                result = cursor.fetchone()
                cargo_exists = result['count'] > 0
                
                # Verificar si la columna dirección existe
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'usuarios' 
                    AND COLUMN_NAME = 'direccion'
                """)
                result = cursor.fetchone()
                direccion_exists = result['count'] > 0
                
                # Si las columnas no existen, las creamos
                if not cargo_exists:
                    logger.info("La columna 'cargo' no existe en la tabla usuarios, creándola...")
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN cargo VARCHAR(100) DEFAULT NULL")
                
                if not direccion_exists:
                    logger.info("La columna 'direccion' no existe en la tabla usuarios, creándola...")
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(255) DEFAULT NULL")
                
                if not cargo_exists or not direccion_exists:
                    connection.commit()
                    logger.info("Columnas creadas exitosamente")
            
            # Ahora actualizamos el perfil
            with connection.cursor() as cursor:
                # Construir la consulta SQL de manera dinámica según los campos proporcionados
                query_parts = ["UPDATE usuarios SET nombre = %s, email = %s"]
                params = [nombre, email]
                
                # Agregar teléfono si no es None
                if telefono is not None:
                    query_parts.append(", telefono = %s")
                    params.append(telefono)
                else:
                    query_parts.append(", telefono = NULL")
                
                if foto_path:
                    query_parts.append(", foto_perfil = %s")
                    params.append(foto_path)
                
                if cargo:
                    query_parts.append(", cargo = %s")
                    params.append(cargo)
                
                if direccion:
                    query_parts.append(", direccion = %s")
                    params.append(direccion)
                
                query_parts.append(" WHERE id = %s")
                params.append(usuario_id)
                
                query = "".join(query_parts)
                logger.info(f"Ejecutando consulta: {query} con parámetros: {params}")
                
                # Ejecutar la consulta
                cursor.execute(query, params)
                connection.commit()
                
                logger.info(f"Perfil del usuario {usuario_id} actualizado correctamente")
                return True
        
        except mysql.connector.Error as err:
            logger.error(f"Error al actualizar perfil de usuario: {err}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
        except Exception as e:
            logger.error(f"Error inesperado al actualizar perfil: {e}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
        finally:
            if connection and connection.is_connected():
                connection.close()
