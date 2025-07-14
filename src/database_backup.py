from flask import Flask
from flask_mysqldb import MySQL
import hashlib
import mysql.connector
import sys
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='database_connection.log'
)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, app):
        try:
            # Configuración de la base de datos MySQL
            app.config['MYSQL_HOST'] = 'localhost'
            app.config['MYSQL_USER'] = 'root'
            app.config['MYSQL_PASSWORD'] = '1234'  # Contraseña confirmada que funciona
            app.config['MYSQL_DB'] = 'sistema_ganadero'
            app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
            
            self.mysql = MySQL(app)
            
            # Lista de credenciales a intentar para MySQL 8.0
            credenciales = [
                # Credenciales con puerto estándar 3306
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'root'},  # Credencial principal según la memoria
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''},      # Usuario root sin contraseña
                {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'root'}, # Usando IP en lugar de localhost
                {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': ''},     # IP con usuario sin contraseña
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'admin'}, # Usuario root con contraseña admin
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1234'},  # Usuario root con contraseña 1234
                
                # Intentar con otros puertos comunes para MySQL
                {'host': 'localhost', 'port': 3307, 'user': 'root', 'password': 'root'},  # Puerto alternativo
                {'host': 'localhost', 'port': 3307, 'user': 'root', 'password': ''},      # Puerto alternativo sin contraseña
            ]
            
            # Intentar cada combinación de credenciales
            last_error = None
            connection_successful = False
            
            for cred in credenciales:
                try:
                    logger.info(f"Intentando conectar a {cred['host']}:{cred['port']} con usuario: {cred['user']} y contraseña: {'[vacía]' if cred['password'] == '' else '[presente]'}")
                    
                    # Actualizar la configuración de Flask-MySQL
                    app.config['MYSQL_HOST'] = cred['host']
                    app.config['MYSQL_USER'] = cred['user']
                    app.config['MYSQL_PASSWORD'] = cred['password']
                    
                    # Intentar conexión directa con mysql.connector
                    self.connection = mysql.connector.connect(
                        host=cred['host'],
                        port=cred['port'],
                        user=cred['user'],
                        password=cred['password'],
                        database='sistema_ganadero'
                    )
                    
                    if not self.connection:
                        raise mysql.connector.Error("No se pudo establecer conexión con la base de datos")
                    
                    logger.info(f"Conexión a la base de datos establecida exitosamente con {cred['host']}:{cred['port']} y usuario: {cred['user']}")
                    connection_successful = True
                    break
                
                except mysql.connector.Error as err:
                    last_error = err
                    logger.warning(f"Intento fallido con {cred['host']}:{cred['port']} y usuario: {cred['user']} - Error: {err}")
            
            if not connection_successful:
                # Clasificar y manejar diferentes tipos de errores del último intento
                if last_error.errno == mysql.connector.errorcode.CR_CONN_HOST_ERROR:
                    logger.error("No se puede conectar al host. Verifique que el servidor MySQL esté corriendo.")
                elif last_error.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                    logger.error("Acceso denegado. Verifique usuario y contraseña.")
                elif last_error.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                    logger.error("La base de datos no existe. Necesita crearla.")
                
                self.connection = None
                raise ConnectionError(f"Error de conexión a la base de datos: {last_error}")
        
        except Exception as e:
            logger.critical(f"Error fatal al inicializar la base de datos: {e}")
            logger.critical(f"Detalles del error: {sys.exc_info()}")
            self.connection = None
            raise

    def get_connection(self):
        """
        Método para obtener una conexión segura a la base de datos.
        Reintenta la conexión si está cerrada usando diferentes credenciales.
        """
        if not self.connection or not self.connection.is_connected():
            logger.warning("Conexión perdida. Reintentando conexión...")
            
            # Lista de credenciales a intentar para MySQL 8.0
            credenciales = [
                # Credenciales con puerto estándar 3306
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'root'},  # Credencial principal según la memoria
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''},      # Usuario root sin contraseña
                {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'root'}, # Usando IP en lugar de localhost
                {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': ''},     # IP con usuario sin contraseña
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'admin'}, # Usuario root con contraseña admin
                {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1234'},  # Usuario root con contraseña 1234
                
                # Intentar con otros puertos comunes para MySQL
                {'host': 'localhost', 'port': 3307, 'user': 'root', 'password': 'root'},  # Puerto alternativo
                {'host': 'localhost', 'port': 3307, 'user': 'root', 'password': ''},      # Puerto alternativo sin contraseña
            ]
            
            # Intentar cada combinación de credenciales
            last_error = None
            connection_successful = False
            
            for cred in credenciales:
                try:
                    logger.info(f"Intentando reconectar a {cred['host']}:{cred['port']} con usuario: {cred['user']} y contraseña: {'[vacía]' if cred['password'] == '' else '[presente]'}")
                    
                    self.connection = mysql.connector.connect(
                        host=cred['host'],
                        port=cred['port'],
                        user=cred['user'],
                        password=cred['password'],
                        database='sistema_ganadero'
                    )
                    
                    logger.info(f"Reconexión exitosa con {cred['host']}:{cred['port']} y usuario: {cred['user']}")
                    connection_successful = True
                    break
                
                except mysql.connector.Error as err:
                    last_error = err
                    logger.warning(f"Intento de reconexión fallido con {cred['host']}:{cred['port']} y usuario: {cred['user']} - Error: {err}")
            
            if not connection_successful:
                logger.error(f"No se pudo reconectar con ninguna credencial. Último error: {last_error}")
                raise ConnectionError("No se pudo restablecer la conexión a la base de datos")
        
        return self.connection

    @staticmethod
    def hash_password(password):
        # Función para hashear contraseñas de forma segura
        return hashlib.sha256(password.encode()).hexdigest()

    def validate_user(self, username, password):
        try:
            connection = self.get_connection()
            hashed_password = self.hash_password(password)
            
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, hashed_password))
                user = cursor.fetchone()
                
                if not user:
                    logger.info(f"Intento de inicio de sesión fallido para el usuario: {username}")
                
                return user
        
        except mysql.connector.Error as err:
            logger.error(f"Error al validar usuario: {err}")
            raise
    
    def register_user(self, username, email, password):
        try:
            connection = self.get_connection()
            hashed_password = self.hash_password(password)
            
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO usuarios (username, email, password) VALUES (%s, %s, %s)", 
                    (username, email, hashed_password)
                )
                connection.commit()
                logger.info(f"Usuario {username} registrado exitosamente")
                return cursor.lastrowid
        
        except mysql.connector.Error as err:
            logger.error(f"Error al registrar usuario: {err}")
            connection.rollback()
            raise

    def verificar_email_existente(self, email):
        """
        Verifica si un correo electrónico ya existe en la base de datos.
        
        Args:
            email: Correo electrónico a verificar
        
        Returns:
            True si existe, False si no existe
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                query = "SELECT * FROM usuarios WHERE email = %s"
                cursor.execute(query, (email,))
                
                result = cursor.fetchone()
                return result is not None
        
        except mysql.connector.Error as err:
            logger.error(f"Error al verificar email existente: {err}")
            return False

    def verificar_username_existente(self, username):
        """
        Verifica si un nombre de usuario ya existe en la base de datos.
        
        Args:
            username: Nombre de usuario a verificar
        
        Returns:
            True si existe, False si no existe
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                query = "SELECT * FROM usuarios WHERE username = %s"
                cursor.execute(query, (username,))
                
                result = cursor.fetchone()
                return result is not None
        
        except mysql.connector.Error as err:
            logger.error(f"Error al verificar username existente: {err}")
            return False

    def obtener_usuario_por_id(self, usuario_id):
        """
        Obtiene la información de un usuario por su ID.
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            Diccionario con la información del usuario o None si no existe
        """
        try:
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                query = "SELECT * FROM usuarios WHERE id = %s"
                cursor.execute(query, (usuario_id,))
                
                return cursor.fetchone()
        
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener usuario por ID: {err}")
            return None

    def actualizar_perfil_usuario(self, usuario_id, nombre, email, telefono, foto_path=None, cargo=None, direccion=None):
        """
        Actualiza la información del perfil de un usuario.
        
        Args:
            usuario_id: ID del usuario
            nombre: Nombre completo del usuario
            email: Correo electrónico
            telefono: Número de teléfono (puede ser None)
            foto_path: Ruta de la foto de perfil (opcional)
            cargo: Cargo del usuario en la empresa (opcional)
            direccion: Dirección del usuario (opcional)
        
        Returns:
            True si la actualización fue exitosa, False en caso contrario
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

    def actualizar_contrasena_usuario(self, usuario_id, nueva_contrasena_hash):
        """
        Actualiza la contraseña de un usuario.
        
        Args:
            usuario_id: ID del usuario
            nueva_contrasena_hash: Hash de la nueva contraseña
        
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE usuarios 
                    SET password = %s
                    WHERE id = %s
                """, (nueva_contrasena_hash, usuario_id))
                
                connection.commit()
                return True
        
        except mysql.connector.Error as err:
            logger.error(f"Error al actualizar contraseña de usuario: {err}")
            return False

    def verificar_contrasena(self, usuario_id, contrasena):
        """
        Verifica si la contraseña proporcionada coincide con la almacenada para el usuario.
        
        Args:
            usuario_id: ID del usuario
            contrasena: Contraseña a verificar
        
        Returns:
            True si la contraseña es correcta, False en caso contrario
        """
        try:
            connection = self.get_connection()
            hashed_password = self.hash_password(contrasena)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM usuarios 
                    WHERE id = %s AND password = %s
                """, (usuario_id, hashed_password))
                
                result = cursor.fetchone()
                return result is not None
        
        except mysql.connector.Error as err:
            logger.error(f"Error al verificar contraseña: {err}")
            return False

    def registrar_animal(self, datos_animal):
        """
        Registra un nuevo animal en la base de datos.
        
        Args:
            datos_animal: Diccionario con los datos del animal
        
        Returns:
            ID del animal registrado o None si ocurrió un error
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                query = """
                    INSERT INTO animales (
                        usuario_id, nombre, numero_arete, raza, sexo, condicion,
                        fecha_nacimiento, propietario, foto_path, padre_arete, madre_arete,
                        fecha_registro
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                """
                
                cursor.execute(query, (
                    datos_animal['usuario_id'],
                    datos_animal['nombre'],
                    datos_animal['numero_arete'],
                    datos_animal['raza'],
                    datos_animal['sexo'],
                    datos_animal.get('condicion', 'Normal'),
                    datos_animal['fecha_nacimiento'],
                    datos_animal.get('propietario', ''),
                    datos_animal.get('foto_path', None),
                    datos_animal.get('padre_arete', None),
                    datos_animal.get('madre_arete', None)
                ))
                
                connection.commit()
                return cursor.lastrowid
        
        except mysql.connector.Error as err:
            logger.error(f"Error al registrar animal: {err}")
            if connection and connection.is_connected():
                connection.rollback()
            return None

    def obtener_animal_por_id(self, animal_id, usuario_id=None):
        """
        Obtiene un animal por su ID sin verificar el usuario.
        
        Args:
            animal_id: ID del animal a obtener
            usuario_id: ID del usuario (opcional, ya no se usa)
            
        Returns:
            Diccionario con la información del animal o None si no se encuentra
        """
        try:
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT a.*, 
                           m.nombre as nombre_madre, m.numero_arete as arete_madre,
                           p.nombre as nombre_padre, p.numero_arete as arete_padre
                    FROM animales a
                    LEFT JOIN animales m ON a.madre_id = m.id
                    LEFT JOIN animales p ON a.padre_id = p.id
                    WHERE a.id = %s
                """, (animal_id,))
                
                return cursor.fetchone()
        
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener animal por ID: {err}")
            return None

    def obtener_animales(self, usuario_id=None, filtros=None):
        """
        Obtiene todos los animales registrados en el sistema.
        
        Args:
            usuario_id: ID del usuario (opcional, ya no se usa)
            filtros: Diccionario con filtros para la consulta (opcional)
            
        Returns:
            Lista de animales
        """
        try:
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                # Consulta base sin filtro de usuario
                query = """
                    SELECT * FROM animales 
                    WHERE 1=1
                """
                params = []
                
                # Aplicar filtros adicionales si existen
                if filtros:
                    if 'raza' in filtros and filtros['raza']:
                        query += " AND raza = %s"
                        params.append(filtros['raza'])
                    
                    if 'sexo' in filtros and filtros['sexo']:
                        query += " AND sexo = %s"
                        params.append(filtros['sexo'])
                    
                    if 'condicion' in filtros and filtros['condicion']:
                        query += " AND condicion = %s"
                        params.append(filtros['condicion'])
                
                query += " ORDER BY fecha_registro DESC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
        
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener animales: {err}")
            return []
            
    def obtener_animales_por_usuario(self, usuario_id, filtros=None):
        """
        Obtiene los animales registrados por un usuario específico.
        
        Args:
            usuario_id: ID del usuario
            filtros: Diccionario con filtros para la consulta
            
        Returns:
            Lista de animales del usuario
        """
        # Reutilizamos el método obtener_animales para mantener consistencia
        return self.obtener_animales(usuario_id, filtros)

    def buscar_animal_por_identificador(self, identificador, usuario_id):
        """
        Busca un animal por número de arete, nombre o ID.
        
        Args:
            identificador: Número de arete, nombre o ID del animal
            usuario_id: ID del usuario
        
        Returns:
            Lista de animales que coinciden con el identificador
        """
        try:
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                # Intentar convertir a entero para búsqueda por ID
                try:
                    animal_id = int(identificador)
                    id_search = True
                except (ValueError, TypeError):
                    id_search = False
                
                if id_search:
                    cursor.execute("""
                        SELECT * FROM animales 
                        WHERE id = %s AND usuario_id = %s
                    """, (animal_id, usuario_id))
                else:
                    cursor.execute("""
                        SELECT * FROM animales 
                        WHERE (numero_arete LIKE %s OR nombre LIKE %s) AND usuario_id = %s
                    """, (f"%{identificador}%", f"%{identificador}%", usuario_id))
                
                return cursor.fetchall()
        
        except mysql.connector.Error as err:
            logger.error(f"Error al buscar animal por identificador: {err}")
            return []

    def eliminar_animal(self, animal_id, usuario_id):
        """
        Elimina un animal de la base de datos.
        
        Args:
            animal_id: ID del animal a eliminar
            usuario_id: ID del usuario propietario del animal
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # Verificar que el animal pertenece al usuario
                cursor.execute("""
                    SELECT id FROM animales 
                    WHERE id = %s AND usuario_id = %s
                """, (animal_id, usuario_id))
                
                if not cursor.fetchone():
                    return False
                
                # Eliminar el animal
                cursor.execute("""
                    DELETE FROM animales 
                    WHERE id = %s AND usuario_id = %s
                """, (animal_id, usuario_id))
                
                connection.commit()
                return True
        
        except mysql.connector.Error as err:
            logger.error(f"Error al eliminar animal: {err}")
            if connection and connection.is_connected():
                connection.rollback()
            return False
    
    def obtener_gestaciones(self, usuario_id):
        """
        Obtiene todas las gestaciones registradas por un usuario.
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            Lista de gestaciones
        """
        try:
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT g.*, a.nombre as nombre_vaca, a.numero_arete as arete_vaca,
                           t.nombre as nombre_toro, t.numero_arete as arete_toro
                    FROM gestaciones g
                    JOIN animales a ON g.vaca_id = a.id
                    LEFT JOIN animales t ON g.toro_id = t.id
                    WHERE g.usuario_id = %s
                    ORDER BY g.fecha_actualizacion DESC
                """, (usuario_id,))
                
                gestaciones = cursor.fetchall()
                
                # Calcular fecha probable de parto (283 días después de la inseminación)
                for g in gestaciones:
                    if g['fecha_inseminacion']:
                        g['fecha_probable_parto'] = g['fecha_inseminacion'] + timedelta(days=283)
                
                return gestaciones
        
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener gestaciones: {err}")
            return []


def get_db_connection():
    # Lista de credenciales a intentar para MySQL 8.0
    credenciales = [
        # Credenciales con puerto estándar 3306
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '1234'},  # Credencial principal confirmada
        {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': '1234'}, # Usando IP en lugar de localhost
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'root'},  # Credencial alternativa
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': ''},      # Usuario root sin contraseña
        {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'root'}, # Usando IP con contraseña alternativa
        {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': ''},     # IP con usuario sin contraseña
        {'host': 'localhost', 'port': 3306, 'user': 'root', 'password': 'admin'}, # Usuario root con contraseña admin
        
        # Intentar con otros puertos comunes para MySQL
        {'host': 'localhost', 'port': 3307, 'user': 'root', 'password': 'root'},  # Puerto alternativo
        {'host': 'localhost', 'port': 3307, 'user': 'root', 'password': ''},      # Puerto alternativo sin contraseña
    ]
    
    last_error = None
    
    # Intentar cada combinación de credenciales
    for cred in credenciales:
        try:
            logger.info(f"Intentando conectar a {cred['host']}:{cred['port']} con usuario: {cred['user']} y contraseña: {'[vacía]' if cred['password'] == '' else '[presente]'}")
            connection = mysql.connector.connect(
                host=cred['host'],
                port=cred['port'],
                user=cred['user'],
                password=cred['password'],
                database='sistema_ganadero'
            )
            logger.info(f"Conexión exitosa con {cred['host']}:{cred['port']} y usuario: {cred['user']}")
            return connection
        except mysql.connector.Error as err:
            last_error = err
            logger.warning(f"Intento fallido con {cred['host']}:{cred['port']} y usuario: {cred['user']} - Error: {err}")
    
    # Si llegamos aquí, ninguna credencial funcionó
    logger.error(f"No se pudo conectar con ninguna credencial. Último error: {last_error}")
    
    # Intentar crear la base de datos si no existe
    try:
        logger.info("Intentando conectar sin especificar base de datos para crearla si no existe")
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='1234'
        )
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS sistema_ganadero")
        cursor.close()
        connection.close()
        
        # Intentar conectar nuevamente con la base de datos recién creada
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='1234',
            database='sistema_ganadero'
        )
        logger.info("Base de datos creada y conexión establecida exitosamente")
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Error al intentar crear la base de datos: {err}")
        raise last_error
