from flask import Flask
import pg8000
import hashlib
import sys
import logging
from datetime import datetime, timedelta
import os

# Configurar logging para Vercel (sin archivo de log)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, app):
        try:
            # Configuración de PostgreSQL
            self.db_url = "postgresql://ganadero_anwt_user:rOsqRSS6jlrJ6UiEQzj7HM2G5CAb0eBb@dpg-d1tg58idbo4c73dieh30-a.oregon-postgres.render.com/ganadero_anwt"
            
            # Parsear la URL de conexión
            from urllib.parse import urlparse
            parsed = urlparse(self.db_url)
            
            # Configuración de SSL para Render
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Intentar establecer la conexión con pg8000
            self.connection = pg8000.Connection(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else 'ganadero_anwt',
                ssl_context=ssl_context
            )
            
            logger.info("Conexión a PostgreSQL establecida exitosamente")
            
        except Exception as e:
            logger.error(f"Error al conectar a PostgreSQL: {e}")
            self.connection = None

    def get_connection(self):
        """
        Obtiene una conexión a la base de datos, reconectando si es necesario
        """
        try:
            # pg8000 no tiene método is_closed(), verificamos si la conexión existe
            if not hasattr(self, 'connection') or self.connection is None:
                from urllib.parse import urlparse
                parsed = urlparse(self.db_url)
                # Configuración de SSL para Render
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self.connection = pg8000.Connection(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path[1:] if parsed.path else 'ganadero_anwt',
                    ssl_context=ssl_context
                )
            return self.connection
        except Exception as err:
            logger.error(f"Error al obtener conexión: {err}")
            raise Exception("No se pudo establecer la conexión con la base de datos")

    @staticmethod
    def hash_password(password):
        # Función para hashear contraseñas de forma segura
        return hashlib.sha256(password.encode()).hexdigest()

    def validate_user(self, username, password):
        """
        Valida las credenciales del usuario
        """
        try:
            connection = self.get_connection()
            
            with connection.cursor() as cursor:
                # Primero intentamos con la contraseña sin hash
                cursor.execute("""
                    SELECT * FROM usuarios 
                    WHERE username = %s AND password = %s
                """, (username, password))
                user = cursor.fetchone()
                
                if not user:
                    # Si no funciona, intentamos con el hash
                    hashed_password = self.hash_password(password)
                    cursor.execute("""
                        SELECT * FROM usuarios 
                        WHERE username = %s AND password = %s
                    """, (username, hashed_password))
                    user = cursor.fetchone()
                
                if not user:
                    logger.info(f"Intento de inicio de sesión fallido para el usuario: {username}")
                    return None
                
                logger.info(f"Inicio de sesión exitoso para el usuario: {username}")
                return user
                
        except Exception as err:
            logger.error(f"Error al validar usuario: {err}")
            raise Exception("Error al validar las credenciales del usuario")
    
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
        
        except Exception as err:
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
        
        except Exception as err:
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
        
        except Exception as err:
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
            with connection.cursor() as cursor:
                query = "SELECT * FROM usuarios WHERE id = %s"
                cursor.execute(query, (usuario_id,))
                
                return cursor.fetchone()
        
        except Exception as err:
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
            with connection.cursor() as cursor:
                # Verificar si la columna cargo existe
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = current_database() 
                    AND TABLE_NAME = 'usuarios' 
                    AND COLUMN_NAME = 'cargo'
                """)
                result = cursor.fetchone()
                cargo_exists = result[0] > 0
                
                # Verificar si la columna dirección existe
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = current_database() 
                    AND TABLE_NAME = 'usuarios' 
                    AND COLUMN_NAME = 'direccion'
                """)
                result = cursor.fetchone()
                direccion_exists = result[0] > 0
                
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
        
        except Exception as err:
            logger.error(f"Error al actualizar perfil de usuario: {err}")
            if connection and not connection.is_closed():
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
        
        except Exception as err:
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
        
        except Exception as err:
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
                    ) RETURNING id
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
                
                result = cursor.fetchone()
                connection.commit()
                return result[0] if result else None
        
        except Exception as err:
            logger.error(f"Error al registrar animal: {err}")
            if connection and not connection.is_closed():
                connection.rollback()
            
            # Manejar errores específicos de PostgreSQL
            if hasattr(err, 'args') and len(err.args) > 0 and isinstance(err.args[0], dict) and err.args[0].get('C') == '23505':
                # Error de clave duplicada
                if 'numero_arete' in str(err.args[0]):
                    raise Exception("El número de arete ya existe. Por favor, use un número diferente.")
                else:
                    raise Exception("Ya existe un registro con estos datos.")
            
            # Si no es un error de clave duplicada, re-raise la excepción original
            raise Exception(f"Error al registrar animal: {str(err)}")

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
            with connection.cursor() as cursor:
                # Consulta simple que no usa JOIN (porque no hay relaciones por ID)
                cursor.execute("SELECT * FROM animales WHERE id = %s", (animal_id,))
                animal = cursor.fetchone()
                
                if animal:
                    # Si el animal tiene referencias a padre o madre por arete, podemos buscar sus nombres
                    if animal[8]:  # padre_arete
                        cursor.execute("SELECT nombre FROM animales WHERE numero_arete = %s", 
                                      (animal[8],))
                        padre = cursor.fetchone()
                        if padre:
                            animal = list(animal)
                            animal.append(padre[1])  # nombre_padre
                    
                    if animal[9]:  # madre_arete
                        cursor.execute("SELECT nombre FROM animales WHERE numero_arete = %s", 
                                      (animal[9],))
                        madre = cursor.fetchone()
                        if madre:
                            animal = list(animal)
                            animal.append(madre[1])  # nombre_madre
                
                return animal
                
        except Exception as err:
            logger.error(f"Error al obtener animal por ID: {err}")
            return None
    def obtener_animales(self, usuario_id=None, filtros=None):
        """
        Obtiene todos los animales registrados por un usuario específico.
        
        Args:
            usuario_id: ID del usuario
            filtros: Diccionario con filtros para la consulta (opcional)
            
        Returns:
            Lista de animales del usuario
        """
        try:
            print(f"Obteniendo animales para usuario_id: {usuario_id}")
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # Primero verificar si la tabla existe
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'animales'
                """)
                tabla_existe = cursor.fetchone()[0] > 0
                print(f"Tabla animales existe: {tabla_existe}")
                
                if not tabla_existe:
                    print("La tabla animales no existe")
                    return []
                
                # Verificar si hay datos en la tabla
                cursor.execute("SELECT COUNT(*) FROM animales")
                total_animales = cursor.fetchone()[0]
                print(f"Total de animales en la tabla: {total_animales}")
                
                # Consulta base con filtro de usuario
                query = """
                    SELECT * FROM animales 
                    WHERE usuario_id = %s
                """
                params = [usuario_id]
                
                print(f"Ejecutando query: {query}")
                print(f"Parámetros: {params}")
                
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
                resultados = cursor.fetchall()
                print(f"Resultados obtenidos: {len(resultados)}")
                
                if resultados:
                    print(f"Primer resultado: {resultados[0]}")
                else:
                    print("No se encontraron animales para este usuario")
                
                return resultados
        
        except Exception as err:
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
            with connection.cursor() as cursor:
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
        
        except Exception as err:
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
        
        except Exception as err:
            logger.error(f"Error al eliminar animal: {err}")
            if connection and not connection.is_closed():
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
            with connection.cursor() as cursor:
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
                
                # Calcular fecha probable de parto (283 días después de la monta)
                for g in gestaciones:
                    if g[3]:  # fecha_monta
                        g = list(g)
                        g.append(g[3] + timedelta(days=283))  # fecha_probable_parto
                
                return gestaciones
        
        except Exception as err:
            logger.error(f"Error al obtener gestaciones: {err}")
            return []

    def actualizar_animal(self, animal_id, datos_animal):
        """
        Actualiza la información de un animal existente en la base de datos.
        
        Args:
            animal_id: ID del animal a actualizar
            datos_animal: Diccionario con los datos actualizados del animal
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # Construir la consulta SQL de actualización
                update_query = """
                    UPDATE animales 
                    SET nombre = %s,
                        numero_arete = %s,
                        raza = %s,
                        sexo = %s,
                        condicion = %s,
                        foto_path = %s,
                        fecha_nacimiento = %s,
                        propietario = %s,
                        padre_arete = %s,
                        madre_arete = %s
                    WHERE id = %s
                """
                
                # Valores para la consulta
                values = (
                    datos_animal.get('nombre'),
                    datos_animal.get('numero_arete'),
                    datos_animal.get('raza'),
                    datos_animal.get('sexo'),
                    datos_animal.get('condicion'),
                    datos_animal.get('foto_path'),
                    datos_animal.get('fecha_nacimiento'),
                    datos_animal.get('propietario'),
                    datos_animal.get('padre_arete'),
                    datos_animal.get('madre_arete'),
                    animal_id
                )
                
                # Ejecutar la consulta
                cursor.execute(update_query, values)
                connection.commit()
                
                logger.info(f"Animal ID {animal_id} actualizado exitosamente")
                return True
                
        except Exception as err:
            logger.error(f"Error al actualizar animal: {err}")
            if connection and not connection.closed:
                connection.rollback()
            return False


def get_db_connection():
    """
    Obtiene una conexión a PostgreSQL usando la URL de conexión de Render
    """
    try:
        db_url = "postgresql://ganadero_anwt_user:rOsqRSS6jlrJ6UiEQzj7HM2G5CAb0eBb@dpg-d1tg58idbo4c73dieh30-a.oregon-postgres.render.com/ganadero_anwt"
        
        # Parsear la URL de conexión
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        # Configuración de SSL para Render
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Establecer la conexión con pg8000 usando parámetros separados
        connection = pg8000.Connection(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else 'ganadero_anwt',
            ssl_context=ssl_context
        )
        
        logger.info("Conexión a PostgreSQL establecida exitosamente")
        return connection
    except Exception as err:
        logger.error(f"Error al conectar a PostgreSQL: {err}")
        # Retornar None en lugar de lanzar excepción para manejo más elegante
        return None
