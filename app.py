from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, send_file, make_response
from src.database import DatabaseConnection, get_db_connection
from datetime import datetime, timedelta
from io import BytesIO
from src.auditoria import SistemaAuditoria
from src.alarmas import SistemaAlarmas
from src.chatbot import GanaderiaChatbot
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from dateutil.relativedelta import relativedelta
import os
import re
from werkzeug.utils import secure_filename
import qrcode
import json
import io
import base64
from functools import wraps
import uuid
import logging
import shutil
from logging.handlers import RotatingFileHandler
from src.gestacion import registrar_gestacion, obtener_gestaciones, actualizar_estado_gestacion, obtener_gestaciones_proximas, eliminar_gestacion
from datetime import date
from src.routes.registro_leche_routes import registro_leche_bp
from src.cloudinary_handler import upload_file, delete_file, get_public_id_from_url
import psycopg2.extras
import pg8000
from xhtml2pdf import pisa

# Configuración para Vercel (sin carpetas locales)
# UPLOAD_FOLDERS = ['static/comprobantes', 'static/uploads/animales', 'static/uploads/perfiles']
# for folder in UPLOAD_FOLDERS:
#     os.makedirs(folder, exist_ok=True)

# Inicializar el chatbot
chatbot = None

# Declarar db_connection como global
global db_connection
db_connection = None

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)  # Clave secreta para sesiones
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Función para validar archivos de imagen de perfil
def allowed_file_perfil(filename):
    """Verifica si el archivo tiene una extensión permitida para perfiles"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función para validar archivos de imagen general
def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida para imágenes"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Registrar el blueprint de registro_leche
app.register_blueprint(registro_leche_bp, url_prefix='/registro_leche')

# Inicializar el sistema de auditoría
auditoria = SistemaAuditoria(get_db_connection)

# Inicializar el sistema de alarmas
alarmas = SistemaAlarmas(get_db_connection)

# Configurar el planificador de tareas para verificar alarmas
def verificar_alarmas_programadas():
    try:
        # Verificar partos próximos
        partos = alarmas.verificar_partos_proximos()
        
        # Verificar vacunaciones pendientes
        vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        
        # Verificar vitaminizaciones pendientes
        vitaminizaciones = alarmas.verificar_vitaminizaciones_pendientes()
        
        app.logger.info(f'Verificación programada de alarmas: {partos} notificaciones de partos, {vacunaciones} de vacunaciones y {vitaminizaciones} de vitaminizaciones enviadas')
    except Exception as e:
        app.logger.error(f'Error en la verificación programada de alarmas: {str(e)}')

# Inicializar el planificador
scheduler = BackgroundScheduler()
scheduler.add_job(func=verificar_alarmas_programadas, trigger="interval", hours=6)
scheduler.add_job(func=verificar_alarmas_programadas, trigger="date", run_date=datetime.now() + timedelta(seconds=10))
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Función para servir archivos estáticos (COMENTADA para Vercel)
# def serve_file(directory, filename, mimetype=None):
#     """Función centralizada para servir archivos estáticos de forma segura"""
#     if '..' in filename or filename.startswith('/'):
#         return "Acceso denegado", 403
#         
#     filepath = os.path.join(directory, filename)
#     if not os.path.exists(filepath):
#         return f"Archivo no encontrado: {filename}", 404
#         
#     if mimetype is None:
#         # Determinar el tipo MIME basado en la extensión
#         extension = filename.split('.')[-1].lower() if '.' in filename else ''
#         mimetypes = {
#             'jpg': 'image/jpeg',
#             'jpeg': 'image/jpeg',
#             'png': 'image/png',
#             'gif': 'image/gif',
#             'pdf': 'application/pdf'
#         }
#         mimetype = mimetypes.get(extension)
#     
#     return send_from_directory(directory, filename, mimetype=mimetype)

# Ruta unificada para servir archivos (COMENTADA para Vercel)
# @app.route('/files/<path:filename>')
# def serve_uploaded_file(filename):
#     """Ruta unificada para servir archivos desde diferentes directorios"""
#     # Determinar el directorio correcto basado en el prefijo del archivo
#     if filename.startswith('comprobantes/'):
#         return serve_file('static/comprobantes', filename.replace('comprobantes/', ''))
#     elif filename.startswith('animales/'):
#         return serve_file('static/uploads/animales', filename.replace('animales/', ''))
#     elif filename.startswith('perfiles/'):
#         return serve_file('static/uploads/perfiles', filename.replace('perfiles/', ''))
#     else:
#         return "Tipo de archivo no válido", 400

@app.route('/')
def inicio():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    return render_template('inicio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        global db_connection
        # Si db_connection no está inicializado, intentar inicializarlo
        if db_connection is None:
            try:
                db_connection = DatabaseConnection(app)
                app.logger.info("Conexión a la base de datos inicializada correctamente")
            except Exception as e:
                app.logger.error(f"Error al inicializar la conexión de base de datos: {e}")
                flash('Error de conexión con la base de datos. Por favor, inténtelo de nuevo más tarde.', 'error')
                return render_template('login.html')
        
        try:
            # Intentar validar el usuario
            user = db_connection.validate_user(username, password)
            if user:
                session['username'] = username
                session['usuario_id'] = user['id']
                app.logger.info(f"Usuario {username} ha iniciado sesión correctamente")
                return redirect(url_for('dashboard'))
            else:
                app.logger.warning(f"Intento de inicio de sesión fallido para el usuario: {username}")
                flash('Usuario o contraseña incorrectos', 'error')
                return render_template('login.html')
        except Exception as e:
            app.logger.error(f"Error durante la autenticación: {e}")
            flash('Error durante la autenticación. Por favor, inténtelo de nuevo.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validaciones adicionales del lado del servidor
        if len(username) < 3:
            flash('El nombre de usuario debe tener al menos 3 caracteres', 'error')
            return render_template('registro.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Por favor, introduce un correo electrónico válido', 'error')
            return render_template('registro.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('registro.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        if db_connection.register_user(username, email, password):
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error en el registro. El usuario o correo ya existe.', 'error')
    
    return render_template('registro.html')

# Definir el decorador login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        usuario_id = session.get('usuario_id')
        print(f"Dashboard - Usuario ID: {usuario_id}")
        
        # Obtener estadísticas generales filtradas por usuario
        cursor.execute("SELECT COUNT(*) as total FROM animales WHERE usuario_id = %s", (usuario_id,))
        total_animales = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.estado = 'En Gestación' AND a.usuario_id = %s
        """, (usuario_id,))
        total_gestaciones = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT SUM(rl.total_dia) as total 
            FROM registro_leche rl
            JOIN animales a ON rl.animal_id = a.id
            WHERE a.usuario_id = %s
        """, (usuario_id,))
        total_leche = cursor.fetchone()['total'] or 0
        
        # Contar vacunaciones pendientes de todas las tablas filtradas por usuario
        # 1. Carbunco
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as total 
            FROM carbunco c
            JOIN animales a ON c.animal_id = a.id
            WHERE c.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND a.usuario_id = %s
        """, (usuario_id,))
        total_carbunco = cursor.fetchone()['total']
        
        # 2. Vitaminización
        cursor.execute("""
            SELECT COUNT(DISTINCT v.id) as total 
            FROM vitaminizaciones v
            JOIN animales a ON v.animal_id = a.id
            WHERE v.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND a.usuario_id = %s
        """, (usuario_id,))
        total_vitaminizacion = cursor.fetchone()['total']
        
        # 3. Desparasitación
        cursor.execute("""
            SELECT COUNT(DISTINCT d.id) as total 
            FROM desparasitaciones d
            JOIN animales a ON d.animal_id = a.id
            WHERE d.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND a.usuario_id = %s
        """, (usuario_id,))
        total_desparasitacion = cursor.fetchone()['total']
        
        # 4. Vacunas tradicionales (si existen)
        try:
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM vacuna v
                JOIN animales a ON v.animal_id = a.id
                WHERE v.estado = 'Activo' 
                AND v.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                AND a.usuario_id = %s
            """, (usuario_id,))
            total_vacunas = cursor.fetchone()['total']
        except Exception as e:
            app.logger.error(f"Error al contar vacunas tradicionales: {str(e)}")
            total_vacunas = 0
            
        # Sumar todos los totales
        total_vacunaciones_pendientes = total_carbunco + total_vitaminizacion + total_desparasitacion + total_vacunas
        
        # Registrar en el log para depuración
        app.logger.info(f"Usuario {usuario_id} - Vacunaciones pendientes - Carbunco: {total_carbunco}, Vitaminización: {total_vitaminizacion}, Desparasitación: {total_desparasitacion}, Vacunas: {total_vacunas}, Total: {total_vacunaciones_pendientes}")
        
        # Obtener actividades recientes del usuario
        actividades = auditoria.obtener_actividad_reciente(limite=5, usuario_id=usuario_id)
        
        # Obtener próximos partos (próximos 30 días) filtrados por usuario
        cursor.execute("""
            SELECT g.*, a.nombre as nombre_animal, a.numero_arete
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.fecha_probable_parto BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND g.estado = 'En Gestación'
            AND a.usuario_id = %s
            ORDER BY g.fecha_probable_parto ASC
            LIMIT 5
        """, (usuario_id,))
        proximos_partos = cursor.fetchall()
        
        # Obtener próximas vacunaciones (próximos 30 días) de todas las tablas filtradas por usuario
        # 1. Carbunco
        cursor.execute("""
            SELECT 
                c.id, 
                c.fecha_registro, 
                c.fecha_proxima as fecha_programada, 
                'Carbunco' as tipo_vacuna,
                c.dosis as producto,
                a.nombre as nombre_animal, 
                a.numero_arete,
                a.id as animal_id
            FROM carbunco c
            JOIN animales a ON c.animal_id = a.id
            WHERE c.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND a.usuario_id = %s
        """, (usuario_id,))
        proximas_carbunco = cursor.fetchall()
        
        # 2. Vitaminización
        cursor.execute("""
            SELECT 
                v.id, 
                v.fecha_aplicacion, 
                v.fecha_proxima as fecha_programada, 
                'Vitaminización' as tipo_vacuna,
                v.producto,
                a.nombre as nombre_animal, 
                a.numero_arete,
                a.id as animal_id
            FROM vitaminizaciones v
            JOIN animales a ON v.animal_id = a.id
            WHERE v.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND a.usuario_id = %s
        """, (usuario_id,))
        proximas_vitaminizacion = cursor.fetchall()
        
        # 3. Desparasitación
        cursor.execute("""
            SELECT 
                d.id, 
                d.fecha_registro, 
                d.fecha_proxima as fecha_programada, 
                'Desparasitación' as tipo_vacuna,
                d.producto,
                a.nombre as nombre_animal, 
                a.numero_arete,
                a.id as animal_id
            FROM desparasitaciones d
            JOIN animales a ON d.animal_id = a.id
            WHERE d.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND a.usuario_id = %s
        """, (usuario_id,))
        proximas_desparasitacion = cursor.fetchall()
        
        # 4. Vacunas tradicionales (si existen)
        try:
            cursor.execute("""
                SELECT v.*, a.nombre as nombre_animal, a.numero_arete, v.tipo as tipo_vacuna,
                       v.fecha_proxima as fecha_programada
                FROM vacuna v
                JOIN animales a ON v.animal_id = a.id
                WHERE v.fecha_proxima BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                AND v.estado = 'Activo'
                AND a.usuario_id = %s
                ORDER BY v.fecha_proxima ASC
            """, (usuario_id,))
            proximas_vacunas = cursor.fetchall()
        except Exception as e:
            app.logger.error(f"Error al consultar tabla vacuna: {str(e)}")
            proximas_vacunas = []
        
        # Combinar todas las vacunaciones próximas
        proximas_vacunaciones = proximas_carbunco + proximas_vitaminizacion + proximas_desparasitacion + proximas_vacunas
        
        # Ordenar por fecha programada
        proximas_vacunaciones = sorted(proximas_vacunaciones, key=lambda x: x['fecha_programada'])
        
        # Limitar a 5 resultados
        proximas_vacunaciones = proximas_vacunaciones[:5]
        
        # Obtener gestaciones próximas para alertas
        cursor.execute("""
            SELECT g.*, a.nombre as nombre_animal, a.numero_arete,
                   (g.fecha_probable_parto - CURRENT_DATE) as dias_restantes
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.fecha_probable_parto BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            AND g.estado = 'En Gestación'
            AND a.usuario_id = %s
            ORDER BY g.fecha_probable_parto ASC
        """, (usuario_id,))
        gestaciones_proximas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"Dashboard - Total animales: {total_animales}, Gestaciones: {total_gestaciones}, Leche: {total_leche}")
        
        return render_template('dashboard.html', 
                               total_animales=total_animales,
                               total_gestaciones=total_gestaciones,
                               total_leche=total_leche,
                               total_vacunaciones_pendientes=total_vacunaciones_pendientes,
                               actividades=actividades,
                               proximos_partos=proximos_partos,
                               proximas_vacunaciones=proximas_vacunaciones,
                               gestaciones_proximas=gestaciones_proximas,
                               now=datetime.now(),
                               timedelta=timedelta)
    except Exception as e:
        app.logger.error(f"Error en dashboard: {str(e)}")
        flash(f'Error al cargar el dashboard: {str(e)}', 'error')
        return render_template('dashboard.html')

@app.route('/configuracion_alarmas')
@login_required
def configuracion_alarmas():
    try:
        # Obtener la configuración actual de alarmas
        config = alarmas.obtener_configuracion_alarmas()
        
        return render_template('configuracion_alarmas.html', config=config)
    except Exception as e:
        flash(f'Error al cargar la configuración de alarmas: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/configurar-alarma', methods=['POST'])
@login_required
def configurar_alarma():
    try:
        tipo = request.form.get('tipo')
        email = request.form.get('email')
        dias_anticipacion = int(request.form.get('dias_anticipacion', 7))
        
        if not tipo or not email:
            flash('Debe proporcionar el tipo de alarma y un correo electrónico', 'error')
            return redirect(url_for('configuracion_alarmas'))
        
        # Configurar la alarma
        if alarmas.configurar_alarma(tipo, email, dias_anticipacion):
            # Registrar la actividad en el sistema de auditoría
            auditoria.registrar_actividad(
                accion='Configurar', 
                modulo='Alarmas', 
                descripcion=f'Se configuró una alarma de tipo {tipo} con {dias_anticipacion} días de anticipación'
            )
            flash(f'Alarma de {tipo} configurada exitosamente', 'success')
        else:
            flash('Error al configurar la alarma', 'error')
        
        return redirect(url_for('configuracion_alarmas'))
    except Exception as e:
        flash(f'Error al configurar la alarma: {str(e)}', 'error')
        return redirect(url_for('configuracion_alarmas'))

@app.route('/verificar-alarmas')
@login_required
def verificar_alarmas():
    try:
        # Verificar partos próximos
        partos = alarmas.verificar_partos_proximos()
        
        # Verificar vacunaciones pendientes
        vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        
        # Verificar desparasitaciones pendientes
        desparasitaciones = alarmas.verificar_desparasitaciones_pendientes()
        
        # Verificar vitaminizaciones pendientes
        vitaminizaciones = alarmas.verificar_vitaminizaciones_pendientes()
        
        total = partos + vacunaciones + desparasitaciones + vitaminizaciones
        
        if total > 0:
            flash(f'Se enviaron {total} notificaciones ({partos} de partos, {vacunaciones} de vacunaciones, {desparasitaciones} de desparasitaciones y {vitaminizaciones} de vitaminizaciones)', 'success')
        else:
            flash('No hay notificaciones pendientes para enviar', 'info')
        
        return redirect(url_for('configuracion_alarmas'))
    except Exception as e:
        flash(f'Error al verificar alarmas: {str(e)}', 'error')
        return redirect(url_for('configuracion_alarmas'))

@app.route('/desactivar-alarma/<tipo>')
@login_required
def desactivar_alarma(tipo):
    try:
        # Desactivar la alarma
        if alarmas.desactivar_alarma(tipo):
            # Registrar la actividad en el sistema de auditoría
            auditoria.registrar_actividad(
                accion='Desactivar', 
                modulo='Alarmas', 
                descripcion=f'Se desactivó la alarma de tipo {tipo}'
            )
            flash(f'Alarma de {tipo} desactivada exitosamente', 'success')
        else:
            flash('Error al desactivar la alarma', 'error')
        
        return redirect(url_for('configuracion_alarmas'))
    except Exception as e:
        flash(f'Error al desactivar la alarma: {str(e)}', 'error')
        return redirect(url_for('configuracion_alarmas'))

@app.route('/activar-alarma/<tipo>')
@login_required
def activar_alarma(tipo):
    try:
        # Obtener la configuración actual de la alarma
        config = alarmas.obtener_configuracion_alarmas()
        
        if tipo in config:
            # Usar la configuración existente para activar la alarma
            email = config[tipo]['email']
            dias_anticipacion = config[tipo]['dias_anticipacion']
            
            if alarmas.configurar_alarma(tipo, email, dias_anticipacion):
                # Registrar la actividad en el sistema de auditoría
                auditoria.registrar_actividad(
                    accion='Activar', 
                    modulo='Alarmas', 
                    descripcion=f'Se activó una alarma de tipo {tipo}'
                )
                flash(f'Alarma de {tipo} activada exitosamente', 'success')
            else:
                flash('Error al activar la alarma', 'error')
        else:
            flash('No se encontró la configuración de la alarma', 'error')
        
        return redirect(url_for('configuracion_alarmas'))
    except Exception as e:
        flash(f'Error al activar la alarma: {str(e)}', 'error')
        return redirect(url_for('configuracion_alarmas'))

@app.route('/configurar-email-alarmas', methods=['POST'])
@login_required
def configurar_email_alarmas():
    try:
        smtp_server = request.form.get('smtp_server')
        port = int(request.form.get('port', 587))
        username = request.form.get('username')
        password = request.form.get('password')
        from_email = request.form.get('from_email', username)
        
        if not smtp_server or not username or not password:
            flash('Debe proporcionar todos los datos de configuración de correo', 'error')
            return redirect(url_for('configuracion_alarmas'))
        
        # Configurar el email
        if alarmas.configurar_email(smtp_server, port, username, password, from_email):
            # Registrar la actividad en el sistema de auditoría
            auditoria.registrar_actividad(
                accion='Configurar', 
                modulo='Alarmas', 
                descripcion='Se configuró el correo electrónico para envío de alarmas'
            )
            flash('Configuración de correo electrónico actualizada exitosamente', 'success')
        else:
            flash('Error al configurar el correo electrónico', 'error')
        
        return redirect(url_for('configuracion_alarmas'))
    except Exception as e:
        flash(f'Error al configurar el correo electrónico: {str(e)}', 'error')
        return redirect(url_for('configuracion_alarmas'))

@app.route('/historial-auditoria')
@login_required
def historial_auditoria():
    try:
        # Obtener todos los registros de auditoría
        actividades = auditoria.obtener_actividad_reciente(limite=100)  # Obtener los últimos 100 registros
        
        return render_template('historial_auditoria.html', actividades=actividades)
    except Exception as e:
        flash(f'Error al cargar el historial de auditoría: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    if request.method == 'POST':
        email = request.form['email']
        
        # Validar formato de correo electrónico
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Por favor, introduce un correo electrónico válido', 'error')
            return render_template('recuperar_contrasena.html')
        
        # Verificar si el correo existe en la base de datos
        if db_connection.email_exists(email):
            # Aquí podrías implementar la lógica de envío de correo de recuperación
            # Por ahora, solo mostraremos un mensaje de éxito
            flash('Se ha enviado un correo de recuperación a tu email', 'success')
            return redirect(url_for('login'))
        else:
            flash('No se encontró ninguna cuenta con este correo electrónico', 'error')
    
    return render_template('recuperar_contrasena.html')

@app.route('/animales')
@login_required
def animales():
    try:
        # Obtener todos los animales del usuario actual
        usuario_id = session.get('usuario_id')
        print(f"Usuario ID en sesión: {usuario_id}")
        
        # Verificar si db_connection está inicializado
        global db_connection
        if db_connection is None:
            print("db_connection es None, inicializando...")
            db_connection = DatabaseConnection(app)
        
        # Verificar si la tabla animales existe y tiene datos
        try:
            connection = db_connection.get_connection()
            with connection.cursor() as cursor:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'animales'
                """)
                result = cursor.fetchone()
                tabla_existe = result['count'] > 0 if result else False
                print(f"Tabla animales existe: {tabla_existe}")
                
                if tabla_existe:
                    # Verificar cuántos animales hay en total
                    cursor.execute("SELECT COUNT(*) FROM animales")
                    result = cursor.fetchone()
                    total_animales = result['count'] if result else 0
                    print(f"Total de animales en la tabla: {total_animales}")
                    
                    # Verificar cuántos animales tiene este usuario
                    cursor.execute("SELECT COUNT(*) FROM animales WHERE usuario_id = %s", (usuario_id,))
                    result = cursor.fetchone()
                    animales_usuario = result['count'] if result else 0
                    print(f"Animales del usuario {usuario_id}: {animales_usuario}")
        except Exception as e:
            print(f"Error al verificar tabla: {str(e)}")
        
        animales = db_connection.obtener_animales(usuario_id)
        print(f"Animales obtenidos para usuario {usuario_id}: {len(animales) if animales else 0}")
        
        if animales:
            print(f"Primer animal: {animales[0]}")
        
        # Importar datetime para calcular la edad
        from datetime import datetime
        now = datetime.now().date()
        
        # Si no hay animales, crear algunos de prueba
        if not animales and usuario_id:
            print("No hay animales, creando algunos de prueba...")
            try:
                connection = db_connection.get_connection()
                with connection.cursor() as cursor:
                    # Insertar animales de prueba
                    animales_prueba = [
                        ('Vaca001', 'Lola', 'Hembra', 'Holstein', 'Vaca', '2020-03-15', 'Juan Pérez', None, None, usuario_id),
                        ('Toro001', 'Max', 'Macho', 'Angus', 'Toro', '2019-05-20', 'Juan Pérez', None, None, usuario_id),
                        ('Ternero001', 'Peque', 'Macho', 'Holstein', 'Ternero', '2024-12-01', 'Juan Pérez', 'Toro001', 'Vaca001', usuario_id)
                    ]
                    
                    for arete, nombre, sexo, raza, condicion, fecha_nac, propietario, padre, madre, user_id in animales_prueba:
                        cursor.execute("""
                            INSERT INTO animales (numero_arete, nombre, sexo, raza, condicion, fecha_nacimiento, propietario, padre_arete, madre_arete, usuario_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (arete, nombre, sexo, raza, condicion, fecha_nac, propietario, padre, madre, user_id))
                    
                    connection.commit()
                    print("Animales de prueba creados exitosamente")
                    
                    # Obtener los animales nuevamente
                    animales = db_connection.obtener_animales(usuario_id)
                    print(f"Animales después de crear prueba: {len(animales) if animales else 0}")
                    
            except Exception as e:
                print(f"Error al crear animales de prueba: {str(e)}")
        
        return render_template('animales.html', animales=animales, now=now)
    except Exception as e:
        print(f"Error al obtener animales: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error al cargar los animales', 'error')
        from datetime import datetime
        return render_template('animales.html', animales=[], now=datetime.now().date())

@app.route('/registrar-animal', methods=['GET', 'POST'])
@login_required
def registrar_animal():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre')
            numero_arete = request.form.get('numero_arete')
            raza = request.form.get('raza')
            sexo = request.form.get('sexo')
            condicion = request.form.get('condicion')
            fecha_nacimiento = request.form.get('fecha_nacimiento')
            propietario = request.form.get('propietario', '')
            padre_arete = request.form.get('padre_arete', '')
            madre_arete = request.form.get('madre_arete', '')
            
            # Validaciones básicas
            if not nombre or len(nombre) < 2:
                flash('El nombre debe tener al menos 2 caracteres', 'error')
                return render_template('registrar_animal.html')
            
            if not numero_arete:
                flash('El número de arete es obligatorio', 'error')
                return render_template('registrar_animal.html')
            
            if not raza:
                flash('La raza es obligatoria', 'error')
                return render_template('registrar_animal.html')
            
            if not sexo:
                flash('El sexo es obligatorio', 'error')
                return render_template('registrar_animal.html')
            
            # Manejar carga de imagen
            foto_path = None
            foto = request.files.get('foto')
            if foto and foto.filename:
                if allowed_file(foto.filename):
                    # Subir imagen a Cloudinary
                    from src.cloudinary_handler import upload_file
                    cloudinary_url = upload_file(foto, folder="animales")
                    if cloudinary_url:
                        foto_path = cloudinary_url
                    else:
                        flash('Error al subir la imagen', 'error')
                        return render_template('registrar_animal.html')
                else:
                    flash('Formato de imagen no permitido. Use JPG, PNG o GIF', 'error')
                    return render_template('registrar_animal.html')
            
            # Preparar datos del animal
            datos_animal = {
                'usuario_id': session.get('usuario_id'),
                'nombre': nombre,
                'numero_arete': numero_arete,
                'raza': raza,
                'sexo': sexo,
                'condicion': condicion or 'Normal',
                'fecha_nacimiento': fecha_nacimiento,
                'propietario': propietario,
                'foto_path': foto_path,
                'padre_arete': padre_arete if padre_arete else None,
                'madre_arete': madre_arete if madre_arete else None
            }
            
            # Registrar el animal en la base de datos
            print(f"Intentando registrar animal con datos: {datos_animal}")
            animal_id = db_connection.registrar_animal(datos_animal)
            print(f"Resultado del registro: {animal_id}")
            
            if animal_id:
                # Registrar la actividad en el sistema de auditoría
                auditoria.registrar_actividad(
                    accion='Registrar', 
                    modulo='Animales', 
                    descripcion=f'Se registró el animal: {nombre} (ID: {animal_id})'
                )
                flash('Animal registrado exitosamente', 'success')
                return redirect(url_for('animales'))
            else:
                flash('Error al registrar el animal en la base de datos', 'error')
                
        except Exception as e:
            flash(f'Error al registrar el animal: {str(e)}', 'error')
    
    return render_template('registrar_animal.html')

@app.route('/editar-animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener información del animal
    animal = db_connection.obtener_animal_por_id(animal_id)
    
    if not animal:
        flash('Animal no encontrado', 'error')
        return redirect(url_for('animales'))
    
    # Si no hay foto o es la imagen por defecto, usar imagen por defecto
    if not animal['foto_path'] or animal['foto_path'] == 'static/images/upload-image-placeholder.svg':
        animal['foto_path'] = 'static/images/upload-image-placeholder.svg'
    
    if request.method == 'POST':
        # Procesar el formulario de edición
        datos_animal = {
            'nombre': request.form.get('nombre'),
            'numero_arete': request.form.get('numero_arete'),
            'raza': request.form.get('raza'),
            'sexo': request.form.get('sexo'),
            'condicion': request.form.get('condicion'),
            'foto_path': animal['foto_path'],
            'fecha_nacimiento': request.form.get('fecha_nacimiento'),
            'propietario': request.form.get('propietario'),
            'padre_arete': request.form.get('padre_arete'),
            'madre_arete': request.form.get('madre_arete')
        }
        
        # Actualizar foto si se proporciona
        foto = request.files.get('foto')
        if foto and allowed_file(foto.filename):
            # Si hay una foto anterior en Cloudinary, eliminarla
            if animal['foto_path'] and 'cloudinary' in animal['foto_path']:
                public_id = get_public_id_from_url(animal['foto_path'])
                if public_id:
                    delete_file(public_id)
            
            # Subir la nueva imagen a Cloudinary
            cloudinary_url = upload_file(foto, folder="animales")
            if cloudinary_url:
                datos_animal['foto_path'] = cloudinary_url
            else:
                flash('Error al subir la imagen', 'error')
                return render_template('editar_animal.html', animal=animal)
        
        # Actualizar el animal en la base de datos
        resultado = db_connection.actualizar_animal(animal_id, datos_animal)
        
        if resultado:
            flash('Animal actualizado exitosamente', 'success')
            return redirect(url_for('animales'))
        else:
            flash('Error al actualizar el animal', 'error')
    
    return render_template('editar_animal.html', animal=animal)

@app.route('/eliminar-animal/<int:animal_id>', methods=['GET'])
def eliminar_animal(animal_id):
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    try:
        # Obtener información del animal antes de eliminarlo
        animal = db_connection.obtener_animal_por_id(animal_id)
        
        if not animal:
            flash('Animal no encontrado', 'error')
            return redirect(url_for('animales'))
        
        # Si el animal tiene una imagen en Cloudinary, eliminarla
        if animal['foto_path'] and 'cloudinary' in animal['foto_path']:
            public_id = get_public_id_from_url(animal['foto_path'])
            if public_id:
                delete_file(public_id)
        
        # Eliminar el animal de la base de datos
        resultado = db_connection.eliminar_animal(animal_id)
        
        if resultado:
            # Registrar la actividad en el sistema de auditoría
            auditoria.registrar_actividad(
                accion='Eliminar', 
                modulo='Animales', 
                descripcion=f'Se eliminó el animal ID: {animal_id}'
            )
            flash('Animal eliminado exitosamente', 'success')
        else:
            flash('Error al eliminar el animal', 'error')
            
    except Exception as e:
        flash(f'Error al eliminar el animal: {str(e)}', 'error')
    
    return redirect(url_for('animales'))

@app.route('/perfil/editar', methods=['GET', 'POST'])
def editar_perfil():
    print("Iniciando función editar_perfil")
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    usuario_id = session.get('usuario_id')
    
    try:
        # Obtener información actual del usuario desde la base de datos
        usuario = db_connection.obtener_usuario_por_id(usuario_id)
        print("Usuario obtenido:", usuario)
        
        if request.method == 'POST':
            print("Entró al POST de editar_perfil")
            # Procesar formulario de edición de perfil
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            cargo = request.form.get('cargo')
            direccion = request.form.get('direccion')
            print("Nombre recibido:", nombre)
            print("Email recibido:", email)
            # Validaciones básicas
            if not nombre or len(nombre) < 3:
                print("Validación fallida: nombre")
                flash('El nombre debe tener al menos 3 caracteres', 'error')
                return render_template('editar_perfil.html', usuario=usuario)
            print("Validación de nombre pasada")
            if not email or '@' not in email:
                print("Validación fallida: email")
                flash('Ingrese un correo electrónico válido', 'error')
                return render_template('editar_perfil.html', usuario=usuario)
            print("Validación de email pasada")
            # Verificar si el correo ya está en uso por otro usuario
            if email != usuario.get('email'):
                usuario_existente = db_connection.obtener_usuario_por_email(email)
                print("Verificando email duplicado:", usuario_existente)
                if usuario_existente and str(usuario_existente.get('id')) != str(usuario_id):
                    print("Validación fallida: email duplicado")
                    flash('Este correo electrónico ya está en uso', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
            print("Validación de email duplicado pasada")
            
            # Manejar carga de imagen de perfil
            foto_perfil = request.files.get('foto_perfil')
            print("Foto perfil recibida:", foto_perfil)
            print("Nombre del archivo:", foto_perfil.filename if foto_perfil else "No hay archivo")
            foto_path = None
            
            print("Evaluando condición:", foto_perfil and foto_perfil.filename)
            print("foto_perfil existe:", foto_perfil is not None)
            print("foto_perfil.filename existe:", foto_perfil.filename if foto_perfil else None)
            if foto_perfil and foto_perfil.filename:
                print("Entrando al bloque de procesamiento de imagen")
                print("Validando archivo:", foto_perfil.filename)
                print("Resultado de allowed_file_perfil:", allowed_file_perfil(foto_perfil.filename))
                if not allowed_file_perfil(foto_perfil.filename):
                    print("Validación fallida: formato no permitido")
                    flash('Formato de imagen no permitido. Use JPG, PNG o GIF', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
                print("Validación de formato pasada")
                
                # Verificar tamaño de la imagen (máximo 5MB)
                print("Archivo recibido:", foto_perfil)
                print("Nombre del archivo:", foto_perfil.filename)
                file_content = foto_perfil.read()
                print("Tamaño del archivo:", len(file_content))
                if len(file_content) > 5 * 1024 * 1024:  # 5MB en bytes
                    foto_perfil.seek(0)  # Reiniciar el puntero del archivo
                    flash('La imagen es demasiado grande. Máximo 5MB', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
                foto_perfil.seek(0)  # Reiniciar el puntero del archivo
                print("Intentando subir imagen a Cloudinary")
                from src.cloudinary_handler import upload_file
                cloudinary_url = upload_file(foto_perfil, folder="perfiles")
                print("Resultado de Cloudinary:", cloudinary_url)
                if cloudinary_url:
                    foto_path = cloudinary_url
                    session['foto_perfil'] = foto_path
                    print("URL de Cloudinary guardada:", foto_path)
                else:
                    flash('Error al subir la imagen a Cloudinary', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
            
            print("Antes de verificar columnas de BD")
            # Verificar si los campos cargo y dirección existen en el usuario
            try:
                # Actualizar información en la base de datos
                # Si los campos no existen, primero intentamos crearlos
                connection = db_connection.get_connection()
                with connection.cursor() as cursor:
                    # Verificar si las columnas cargo y dirección existen
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'usuarios' 
                        AND COLUMN_NAME = 'cargo'
                    """)
                    if cursor.fetchone()[0] == 0:
                        # La columna cargo no existe, la creamos
                        cursor.execute("ALTER TABLE usuarios ADD COLUMN cargo VARCHAR(100) DEFAULT NULL")
                        app.logger.info("Columna 'cargo' agregada a la tabla usuarios")
                    
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'usuarios' 
                        AND COLUMN_NAME = 'direccion'
                    """)
                    if cursor.fetchone()[0] == 0:
                        # La columna dirección no existe, la creamos
                        cursor.execute("ALTER TABLE usuarios ADD COLUMN direccion VARCHAR(255) DEFAULT NULL")
                        app.logger.info("Columna 'direccion' agregada a la tabla usuarios")
                    
                    connection.commit()
                    print("Verificación de columnas completada")
            except Exception as e:
                app.logger.error(f"Error al verificar/crear columnas: {e}")
                print("Error al verificar columnas:", e)
                # Continuamos con la actualización de todas formas
            
            print("Antes de actualizar perfil en BD")
            # Actualizar información en la base de datos
            db_connection.actualizar_perfil_usuario(usuario_id, nombre, email, telefono, foto_path, cargo, direccion)
            print("Después de actualizar perfil en BD")
            
            # Actualizar sesión
            session['nombre'] = nombre
            session['email'] = email
            
            # Registrar en el sistema de auditoría
            print("Antes de registrar auditoría")
            # auditoria.registrar_evento(
            #     usuario_id=usuario_id,
            #     tipo_evento='actualizacion_perfil',
            #     descripcion=f'Usuario {nombre} actualizó su perfil'
            # )
            print("Después de registrar auditoría")
            
            flash('Perfil actualizado exitosamente', 'success')
            return redirect(url_for('dashboard'))
        
        # Cargar foto de perfil de la sesión si existe
        usuario['foto_perfil'] = session.get('foto_perfil', '/static/images/default-avatar.png')
        
        return render_template('editar_perfil.html', usuario=usuario)
    
    except Exception as e:
        print("Error capturado en except:", e)
        app.logger.error(f"Error al editar perfil: {e}")
        flash('Ocurrió un error al editar el perfil', 'error')
        return redirect(url_for('dashboard'))

@app.route('/perfil/cambiar-contrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    usuario_id = session.get('usuario_id')
    
    try:
        if request.method == 'POST':
            contrasena_actual = request.form.get('contrasena_actual')
            nueva_contrasena = request.form.get('nueva_contrasena')
            confirmar_contrasena = request.form.get('confirmar_contrasena')
            
            # Validar que todos los campos estén completos
            if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
                flash('Todos los campos son obligatorios', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Verificar que la contraseña actual sea correcta
            if not db_connection.verificar_contrasena(usuario_id, contrasena_actual):
                flash('La contraseña actual es incorrecta', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Verificar que las contraseñas coincidan
            if nueva_contrasena != confirmar_contrasena:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Validar la fortaleza de la contraseña
            if len(nueva_contrasena) < 8:
                flash('La contraseña debe tener al menos 8 caracteres', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Verificar que la nueva contraseña no sea igual a la actual
            if contrasena_actual == nueva_contrasena:
                flash('La nueva contraseña no puede ser igual a la actual', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Verificar que la contraseña no haya sido utilizada anteriormente
            if db_connection.contrasena_usada_anteriormente(usuario_id, nueva_contrasena):
                flash('La contraseña ya ha sido utilizada anteriormente. Por seguridad, utilice una contraseña diferente', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Validar complejidad de la contraseña (al menos una mayúscula, una minúscula y un número)
            if not (any(c.isupper() for c in nueva_contrasena) and 
                    any(c.islower() for c in nueva_contrasena) and 
                    any(c.isdigit() for c in nueva_contrasena)):
                flash('La contraseña debe contener al menos una mayúscula, una minúscula y un número', 'error')
                return render_template('cambiar_contrasena.html')
            
            # Actualizar la contraseña
            nueva_contrasena_hash = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
            ip = request.remote_addr
            db_connection.actualizar_contrasena_usuario(usuario_id, nueva_contrasena_hash, ip)
            
            # Registrar en el sistema de auditoría
            auditoria.registrar_evento(
                usuario_id=usuario_id,
                tipo_evento='cambio_contrasena',
                descripcion=f'Usuario {session.get("nombre")} cambió su contraseña'
            )
            
            flash('Contraseña cambiada exitosamente', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('cambiar_contrasena.html')
    
    except Exception as e:
        app.logger.error(f"Error al cambiar contraseña: {e}")
        flash('Ocurrió un error al cambiar la contraseña', 'error')
        return redirect(url_for('dashboard'))

@app.route('/generar-qr', methods=['GET', 'POST'])
def generar_qr():
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        if not identificador:
            flash('Por favor, ingresa un identificador de animal', 'error')
            return render_template('generar_qr.html')
        
        # Aquí iría la lógica para buscar el animal
        usuario_id = session.get('usuario_id')
        animales = db_connection.buscar_animal_por_identificador(identificador, usuario_id)
        
        if not animales or len(animales) == 0:
            flash('No se encontró ningún animal con ese identificador', 'error')
            return render_template('generar_qr.html')
        
        # Tomar el primer animal de la lista
        animal = animales[0] if isinstance(animales, list) else animales
        
        # Preparar datos para el código QR
        datos_qr = f"""Información del Animal
Finca: {animal.get('nombre_finca', 'Sin información') if isinstance(animal, dict) else 'Sin información'}
Propietario: {animal.get('propietario', 'Sin información') if isinstance(animal, dict) else animal.propietario if hasattr(animal, 'propietario') else 'Sin información'}
ID: {animal.get('id', 'N/A') if isinstance(animal, dict) else animal.id if hasattr(animal, 'id') else 'N/A'}
Número de Arete: {animal.get('numero_arete', 'N/A') if isinstance(animal, dict) else animal.numero_arete if hasattr(animal, 'numero_arete') else 'N/A'}
Nombre: {animal.get('nombre', 'N/A') if isinstance(animal, dict) else animal.nombre if hasattr(animal, 'nombre') else 'N/A'}
Sexo: {animal.get('sexo', 'N/A') if isinstance(animal, dict) else animal.sexo if hasattr(animal, 'sexo') else 'N/A'}
Raza: {animal.get('raza', 'N/A') if isinstance(animal, dict) else animal.raza if hasattr(animal, 'raza') else 'N/A'}
Condición: {animal.get('condicion', 'N/A') if isinstance(animal, dict) else animal.condicion if hasattr(animal, 'condicion') else 'N/A'}
Fecha de Nacimiento: {animal.get('fecha_nacimiento', 'N/A') if isinstance(animal, dict) else animal.fecha_nacimiento if hasattr(animal, 'fecha_nacimiento') else 'N/A'}
"""
        
        # Generar código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(datos_qr)
        qr.make(fit=True)
        
        # Crear imagen del código QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar imagen en un buffer de bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        # Convertir a base64 para mostrar en HTML
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return render_template('generar_qr.html', imagen_qr=imagen_base64, animal=animal)
    
    return render_template('generar_qr.html')

@app.route('/gestacion')
@login_required
def gestacion():
    try:
        # Obtener solo animales hembra (vacas y vaconas) del usuario actual
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si hay animales para este usuario
        cursor.execute("""
            SELECT COUNT(*) 
            FROM animales 
            WHERE usuario_id = %s AND sexo = 'Hembra' 
            AND condicion IN ('Vaca', 'Vacona')
        """, (session['usuario_id'],))
        result = cursor.fetchone()
        count = result['count'] if result else 0
        print(f"Animales hembra para gestación del usuario {session['usuario_id']}: {count}")
        
        # Obtener animales hembra del usuario actual
        cursor.execute("""
            SELECT id, nombre, numero_arete, condicion 
            FROM animales 
            WHERE usuario_id = %s AND sexo = 'Hembra' 
            AND condicion IN ('Vaca', 'Vacona')
            ORDER BY nombre
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        print(f"Animales obtenidos para gestación: {len(animales)}")
        if animales:
            print(f"Primer animal: {animales[0]}")
        
        # Si no hay animales hembra, crear algunos de prueba
        if not animales and session['usuario_id']:
            print("No hay animales hembra, creando algunos de prueba...")
            try:
                # Crear algunas vacas de prueba
                animales_prueba = [
                    ('Vaca001', 'Lola', 'Hembra', 'Vaca', 'Holstein', session['usuario_id']),
                    ('Vaca002', 'Rosita', 'Hembra', 'Vaca', 'Angus', session['usuario_id']),
                    ('Vacona001', 'Estrella', 'Hembra', 'Vacona', 'Holstein', session['usuario_id'])
                ]
                
                for arete, nombre, sexo, condicion, raza, user_id in animales_prueba:
                    cursor.execute("""
                        INSERT INTO animales (numero_arete, nombre, sexo, condicion, raza, usuario_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (arete, nombre, sexo, condicion, raza, user_id))
                
                conn.commit()
                print("Animales hembra de prueba creados exitosamente")
                
                # Obtener los animales nuevamente
                cursor.execute("""
                    SELECT id, nombre, numero_arete, condicion 
                    FROM animales 
                    WHERE usuario_id = %s AND sexo = 'Hembra' 
                    AND condicion IN ('Vaca', 'Vacona')
                    ORDER BY nombre
                """, (session['usuario_id'],))
                animales = cursor.fetchall()
                print(f"Animales después de crear prueba: {len(animales)}")
                
            except Exception as e:
                print(f"Error al crear animales de prueba: {str(e)}")
        
        # Obtener todas las gestaciones del usuario actual
        gestaciones = obtener_gestaciones(session['usuario_id'])
        
        cursor.close()
        conn.close()
        
        return render_template('gestacion.html', animales=animales, gestaciones=gestaciones)
        
    except Exception as e:
        print(f"Error en gestación: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error al cargar la página de gestación', 'error')
        return render_template('gestacion.html', animales=[], gestaciones=[])

@app.route('/registrar_gestacion', methods=['POST'])
@login_required
def registrar_gestacion_route():
    animal_id = request.form.get('animal_id')
    fecha_monta = request.form.get('fecha_monta')
    observaciones = request.form.get('observaciones')
    
    success, message = registrar_gestacion(
        animal_id=animal_id,
        fecha_monta=fecha_monta,
        observaciones=observaciones
    )
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('gestacion'))

@app.route('/eliminar_gestacion', methods=['POST'])
@login_required
def eliminar_gestacion_route():
    try:
        data = request.get_json()
        gestacion_id = data.get('gestacion_id')
        
        if not gestacion_id:
            return jsonify({
                'success': False,
                'message': 'ID de gestación no proporcionado'
            }), 400
        
        success, message = eliminar_gestacion(gestacion_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al eliminar el registro de gestación: {str(e)}'
        }), 500

@app.route('/actualizar_estado_gestacion', methods=['POST'])
@login_required
def actualizar_estado_gestacion_route():
    data = request.get_json()
    gestacion_id = data.get('gestacion_id')
    nuevo_estado = data.get('estado')
    observaciones = data.get('observaciones')
    
    success, message = actualizar_estado_gestacion(
        gestacion_id=gestacion_id,
        nuevo_estado=nuevo_estado,
        observaciones=observaciones
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/chatbot', methods=['POST'])
def chatbot_endpoint():
    if 'username' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        mensaje = request.json.get('mensaje', '')
        usuario_id = session.get('usuario_id')
        
        if not mensaje:
            return jsonify({"error": "Mensaje vacío"}), 400
        
        # Verificar si el chatbot está inicializado
        global chatbot
        if chatbot is None:
            try:
                # Intentar inicializar el chatbot con db_connection
                chatbot = GanaderiaChatbot(db_connection)
            except NameError:
                # Si db_connection no está disponible, usar DatabaseConnection directamente
                chatbot = GanaderiaChatbot(DatabaseConnection(app))
        
        respuesta = chatbot.generar_respuesta(mensaje, usuario_id)
        
        return jsonify({
            "respuesta": respuesta
        })
    
    except Exception as e:
        app.logger.error(f'Error al procesar mensaje del chatbot: {str(e)}')
        return jsonify({"error": "Error al procesar mensaje"}), 500

@app.route('/vacunas')
@login_required
def vacunas():
    return render_template('vacunas.html')

@app.route('/desparasitacion')
@login_required
def desparasitacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(d.fecha_aplicacion) 
                    FROM desparasitaciones d 
                    WHERE d.animal_id = a.id AND d.usuario_id = %s) as ultima_desparasitacion
            FROM animales a
            WHERE a.usuario_id = %s
            ORDER BY a.id DESC
        """, (session['usuario_id'], session['usuario_id']))
        animales = cursor.fetchall()
        
        # Obtener registros de desparasitación
        cursor.execute("""
            SELECT d.*, 
                   a.nombre as nombre_animal,
                   a.numero_arete as arete_animal,
                   TO_CHAR(d.fecha_aplicacion, 'DD/MM/YYYY') as fecha_aplicacion_formato,
                   TO_CHAR(d.fecha_proxima, 'DD/MM/YYYY') as fecha_proxima_formato
            FROM desparasitaciones d
            JOIN animales a ON d.animal_id = a.id
            WHERE d.usuario_id = %s
            ORDER BY d.fecha_aplicacion DESC
        """, (session['usuario_id'],))
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('desparasitacion.html', 
                             animales=animales, 
                             registros=registros,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de desparasitación: {str(e)}')
        flash('Error al cargar la página de desparasitación', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/registrar_desparasitacion', methods=['POST'])
@login_required
def registrar_desparasitacion():
    try:
        fecha_registro = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        if producto == 'Otro':
            producto = request.form.get('otro_producto')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        vacunador = request.form.get('vacunador')
        
        # Calcular próxima aplicación (3 meses después)
        fecha_registro_dt = datetime.strptime(fecha_registro, '%Y-%m-%d')
        proxima_aplicacion = fecha_registro_dt + timedelta(days=90)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener animales seleccionados
        animales_seleccionados = request.form.getlist('animales_seleccionados[]')
        
        # Insertar registro para cada animal seleccionado
        for animal_id in animales_seleccionados:
            cursor.execute("""
                INSERT INTO desparasitaciones 
                (animal_id, fecha_aplicacion, producto, dosis, fecha_proxima, observaciones, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (animal_id, fecha_registro, producto, tipo_aplicacion, proxima_aplicacion.strftime('%Y-%m-%d'), vacunador, session['usuario_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Registro de desparasitación guardado exitosamente', 'success')
        return redirect(url_for('desparasitacion'))
    except Exception as e:
        app.logger.error(f'Error al registrar desparasitación: {str(e)}')
        flash('Error al registrar la desparasitación', 'danger')
        return redirect(url_for('desparasitacion'))

@app.route('/desparasitacion/detalles/<int:id>')
@login_required
def detalles_desparasitacion(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener detalles del registro
        cursor.execute("""
            SELECT d.*, 
                   a.nombre as nombre_animal,
                   a.numero_arete as arete_animal,
                   TO_CHAR(d.fecha_aplicacion, 'DD/MM/YYYY') as fecha_aplicacion_formato,
                   TO_CHAR(d.fecha_proxima, 'DD/MM/YYYY') as proxima_aplicacion_formato
            FROM desparasitaciones d
            JOIN animales a ON d.animal_id = a.id
            WHERE d.id = %s AND d.usuario_id = %s
        """, (id, session['usuario_id']))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        # Formatear fechas
        registro['fecha_aplicacion'] = registro['fecha_aplicacion_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        cursor.close()
        conn.close()
        
        return jsonify(registro)
    except Exception as e:
        app.logger.error(f'Error al obtener detalles de desparasitación: {str(e)}')
        return jsonify({'error': 'Error al obtener detalles'}), 500

@app.route('/eliminar_desparasitacion/<int:id>', methods=['POST'])
@login_required
def eliminar_desparasitacion(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eliminar el registro de desparasitación
        cursor.execute("DELETE FROM desparasitaciones WHERE id = %s AND usuario_id = %s", (id, session['usuario_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Registro de desparasitación eliminado exitosamente', 'success')
        return redirect(url_for('desparasitacion'))
    except Exception as e:
        app.logger.error(f'Error al eliminar desparasitación: {str(e)}')
        flash('Error al eliminar el registro de desparasitación', 'danger')
        return redirect(url_for('desparasitacion'))

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/menu/desparasitacion')
@login_required
def menu_desparasitacion():
    return render_template('menu_desparasitacion.html')

@app.route('/obtener_cantones/<int:provincia_id>')
def obtener_cantones(provincia_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la provincia existe
        cursor.execute("SELECT id FROM provincias WHERE id = %s", (provincia_id,))
        provincia = cursor.fetchone()
        
        if not provincia:
            app.logger.error(f'Provincia no encontrada: {provincia_id}')
            return jsonify({'error': 'Provincia no encontrada'}), 404
        
        # Obtener cantones
        cursor.execute("""
            SELECT id, nombre 
            FROM cantones 
            WHERE provincia_id = %s 
            ORDER BY nombre
        """, (provincia_id,))
        
        cantones = cursor.fetchall()
        app.logger.info(f'Cantones encontrados para provincia {provincia_id}: {cantones}')
        
        cursor.close()
        conn.close()
        
        return jsonify(cantones)
    
    except Exception as e:
        app.logger.error(f'Error al obtener cantones: {str(e)}')
        return jsonify({'error': 'Error al obtener cantones'}), 500

@app.route('/obtener_parroquias/<int:canton_id>')
def obtener_parroquias(canton_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si el cantón existe
        cursor.execute("SELECT id FROM cantones WHERE id = %s", (canton_id,))
        canton = cursor.fetchone()
        
        if not canton:
            app.logger.error(f'Cantón no encontrado: {canton_id}')
            return jsonify({'error': 'Cantón no encontrado'}), 404
        
        # Obtener parroquias
        cursor.execute("""
            SELECT id, nombre 
            FROM parroquias 
            WHERE canton_id = %s 
            ORDER BY nombre
        """, (canton_id,))
        
        parroquias = cursor.fetchall()
        app.logger.info(f'Parroquias encontradas para cantón {canton_id}: {parroquias}')
        
        cursor.close()
        conn.close()
        
        return jsonify(parroquias)
    
    except Exception as e:
        app.logger.error(f'Error al obtener parroquias: {str(e)}')
        return jsonify({'error': 'Error al obtener parroquias'}), 500

@app.route('/registrar_fiebre_aftosa', methods=['POST'])
@login_required
def registrar_fiebre_aftosa():
    conn = None
    cursor = None
    try:
        # Obtener datos del formulario
        fecha_registro = request.form['fecha_registro']
        numero_certificado = request.form['numero_certificado']
        nombre_propietario = request.form['propietario_nombre']
        identificacion = request.form['propietario_documento']
        nombre_predio = request.form['nombre_predio']
        provincia_id = request.form['provincia_id']
        canton_id = request.form['canton_id']
        parroquia_id = request.form['parroquia_id']
        tipo_explotacion = request.form['tipo_explotacion']
        vacunador_nombre = request.form['vacunador_nombre']
        vacunador_cedula = request.form['vacunador_cedula']
        tipo_aplicacion = request.form['tipo_aplicacion']
        
        app.logger.info(f'Datos recibidos: fecha={fecha_registro}, cert={numero_certificado}, prop={nombre_propietario}')
        
        # Calcular próxima aplicación (6 meses después)
        fecha_registro_obj = datetime.strptime(fecha_registro, '%Y-%m-%d')
        proxima_aplicacion = fecha_registro_obj + relativedelta(months=6)
        
        app.logger.info(f'Próxima aplicación calculada: {proxima_aplicacion}')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insertar registro de fiebre aftosa
            insert_query = """
                INSERT INTO fiebre_aftosa (
                    fecha_registro, numero_certificado, nombre_propietario,
                    identificacion, nombre_predio, provincia_id, canton_id,
                    parroquia_id, tipo_explotacion, nombre_vacunador,
                    cedula_vacunador, fecha_proxima_aplicacion,
                    usuario_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                fecha_registro, numero_certificado, nombre_propietario,
                identificacion, nombre_predio, provincia_id, canton_id,
                parroquia_id, tipo_explotacion, vacunador_nombre,
                vacunador_cedula, proxima_aplicacion, session['usuario_id']
            )
            
            app.logger.info(f'Ejecutando query: {insert_query}')
            app.logger.info(f'Con valores: {values}')
            
            cursor.execute(insert_query, values)
            fiebre_aftosa_id = cursor.lastrowid
            
            app.logger.info(f'Registro insertado con ID: {fiebre_aftosa_id}')

            # Registrar animales vacunados
            if tipo_aplicacion == 'general':
                app.logger.info('Aplicando vacunación general')
                # Aplicar a todos los animales
                cursor.execute("""
                    INSERT INTO fiebre_aftosa_animal (fiebre_aftosa_id, animal_id)
                    SELECT %s, id FROM animales
                """, (fiebre_aftosa_id,))
            else:
                app.logger.info('Aplicando vacunación específica')
                # Aplicar solo a los animales seleccionados
                animales_seleccionados = request.form.getlist('animales_seleccionados[]')
                app.logger.info(f'Animales seleccionados: {animales_seleccionados}')
                for animal_id in animales_seleccionados:
                    cursor.execute("""
                        INSERT INTO fiebre_aftosa_animal (fiebre_aftosa_id, animal_id)
                        VALUES (%s, %s)
                    """, (fiebre_aftosa_id, animal_id))
        
            conn.commit()
            app.logger.info('Transacción completada exitosamente')
            flash('Vacunación registrada exitosamente', 'success')
            return redirect(url_for('fiebre_aftosa'))
        
        except Exception as e:
            if conn:
                conn.rollback()
            app.logger.error(f'Error al guardar el registro: {str(e)}')
            app.logger.error(f'Tipo de error: {type(e).__name__}')
            flash(f'Error al guardar el registro: {str(e)}', 'danger')
            return redirect(url_for('fiebre_aftosa'))

    except Exception as e:
        app.logger.error(f'Error al registrar vacunación: {str(e)}')
        app.logger.error(f'Tipo de error: {type(e).__name__}')
        flash(f'Error al registrar la vacunación: {str(e)}', 'danger')
        return redirect(url_for('fiebre_aftosa'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/detalles_fiebre_aftosa/<int:id>')
@login_required
def detalles_fiebre_aftosa(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener detalles de la vacunación
        cursor.execute("""
            SELECT fa.*, 
                   p.nombre as provincia,
                   c.nombre as canton,
                   pa.nombre as parroquia
            FROM fiebre_aftosa fa
            JOIN provincias p ON fa.provincia_id = p.id
            JOIN cantones c ON fa.canton_id = c.id
            JOIN parroquias pa ON fa.parroquia_id = pa.id
            WHERE fa.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
        
        # Obtener animales vacunados
        cursor.execute("""
            SELECT a.numero_arete, a.nombre, a.condicion
            FROM animales a
            JOIN fiebre_aftosa_animal faa ON a.id = faa.animal_id
            WHERE faa.fiebre_aftosa_id = %s
            ORDER BY a.numero_arete
        """, (id,))
        animales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        registro['animales'] = animales
        return jsonify(registro)
        
    except Exception as e:
        app.logger.error(f'Error al obtener detalles de vacunación: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/pastizales')
@login_required
def pastizales():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener todos los pastizales del usuario
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT ap.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN animales_pastizal ap ON p.id = ap.pastizal_id AND ap.fecha_retiro IS NULL
            WHERE p.usuario_id = %s
            GROUP BY p.id
        """, (session['usuario_id'],))
        
        pastizales = cursor.fetchall()
        
        return render_template('pastizales.html', pastizales=pastizales)
    
    except Exception as e:
        flash(f'Error al cargar los pastizales: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/registrar_pastizal', methods=['POST'])
@login_required
def registrar_pastizal():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        nombre = request.form['nombre']
        dimension = float(request.form['dimension'])
        tipo_hierba = request.form['tipo_hierba']
        
        cursor.execute("""
            INSERT INTO pastizales (
                nombre, area, estado, descripcion, usuario_id
            ) VALUES (%s, %s, 'Activo', %s, %s)
        """, (nombre, dimension, f"Tipo de hierba: {tipo_hierba}", session['usuario_id']))
        
        conn.commit()
        flash('Pastizal registrado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al registrar el pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/obtener_animales_disponibles/<int:pastizal_id>')
@login_required
def obtener_animales_disponibles(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener información del pastizal
        cursor.execute("""
            SELECT p.*,
                   COUNT(DISTINCT ap.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN animales_pastizal ap ON p.id = ap.pastizal_id AND ap.fecha_retiro IS NULL
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            return jsonify({'error': 'Pastizal no encontrado'}), 404
        
        # Obtener animales disponibles
        cursor.execute("""
            SELECT 
                a.id,
                a.nombre,
                a.condicion as categoria,
                a.estado
            FROM animales a
            LEFT JOIN animales_pastizal ap ON a.id = ap.animal_id AND ap.fecha_retiro IS NULL
            WHERE ap.id IS NULL
                AND a.usuario_id = %s
            ORDER BY a.nombre
        """, (session['usuario_id'],))
        
        animales = cursor.fetchall()
        
        # Calcular capacidad máxima basada en el área (3.5m² por animal)
        capacidad_maxima = int(pastizal['area'] / 3.5) if pastizal['area'] else 0
        
        return jsonify({
            'capacidad_maxima': capacidad_maxima,
            'animales_actuales': pastizal['animales_actuales'] or 0,
            'animales': animales
        })
        
    except Exception as e:
        app.logger.error(f"Error al obtener datos del pastizal: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/asignar_animales/<int:pastizal_id>', methods=['POST'])
@login_required
def asignar_animales(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        animales = request.form.getlist('animales[]')
        fecha_actual = datetime.now().date()
        
        # Verificar capacidad y animales actuales
        cursor.execute("""
            SELECT 
                p.area,
                COUNT(DISTINCT ap.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN animales_pastizal ap ON p.id = ap.pastizal_id AND ap.fecha_retiro IS NULL
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id, p.area
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            flash('Pastizal no encontrado', 'danger')
            return redirect(url_for('pastizales'))
        
        area_pastizal = pastizal[0]
        animales_actuales = pastizal[1] or 0
        capacidad_maxima = int(area_pastizal / 3.5) if area_pastizal else 0
        
        if len(animales) + animales_actuales > capacidad_maxima:
            flash(f'No se pueden asignar más de {capacidad_maxima} animales a este pastizal', 'danger')
            return redirect(url_for('pastizales'))
        
        # Actualizar estado del pastizal
        cursor.execute("""
            UPDATE pastizales 
            SET estado = 'En uso'
            WHERE id = %s AND usuario_id = %s
        """, (pastizal_id, session['usuario_id']))
        
        # Registrar animales en el pastizal
        for animal_id in animales:
            cursor.execute("""
                INSERT INTO animales_pastizal (
                    pastizal_id, animal_id, fecha_asignacion
                ) VALUES (%s, %s, %s)
            """, (pastizal_id, animal_id, fecha_actual))
            
            # Actualizar estado del animal
            cursor.execute("""
                UPDATE animales
                SET estado = 'En pastizal'
                WHERE id = %s AND usuario_id = %s
            """, (animal_id, session['usuario_id']))
        
        conn.commit()
        flash(f'Se han asignado {len(animales)} animales al pastizal exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al asignar animales: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('pastizales'))

@app.route('/inseminaciones')
@login_required
def inseminaciones():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener todas las inseminaciones del usuario actual con detalles del animal
        cursor.execute("""
            SELECT 
                i.id, 
                i.animal_id, 
                TO_CHAR(i.fecha_inseminacion, 'DD/MM/YYYY') as fecha_inseminacion, 
                i.tipo_inseminacion, 
                COALESCE(i.semental, '') as semental, 
                COALESCE(i.raza_semental, '') as raza_semental, 
                COALESCE(i.codigo_pajuela, '') as codigo_pajuela, 
                COALESCE(i.inseminador, '') as inseminador, 
                i.exitosa, 
                COALESCE(i.observaciones, '') as observaciones,
                COALESCE(a.nombre, '') as nombre_animal, 
                COALESCE(a.numero_arete, '') as numero_arete, 
                COALESCE(a.condicion, '') as condicion_animal
            FROM inseminaciones i 
            LEFT JOIN animales a ON i.animal_id = a.id 
            WHERE a.usuario_id = %s
            ORDER BY i.fecha_inseminacion DESC
        """, (session['usuario_id'],))
        
        # Debug: Imprimir los campos de cada registro para verificar
        print("\n==== DATOS DE INSEMINACIONES RECUPERADOS ====")
        inseminaciones = cursor.fetchall()
        for i in inseminaciones:
            print(f"ID: {i['id']} | Raza: '{i['raza_semental']}' | Código: '{i['codigo_pajuela']}' | Inseminador: '{i['inseminador']}'")
        
        
        # Depuración: imprimir los registros para ver qué campos contienen
        print("\n\n==== REGISTROS DE INSEMINACIONES ====")
        if inseminaciones:
            # Imprimir las claves (nombres de columnas) del primer registro
            print("Columnas disponibles:", list(inseminaciones[0].keys()))
            # Imprimir el primer registro completo
            print("Primer registro:", inseminaciones[0])
            # Imprimir todos los registros para depuración
            print("Total de registros:", len(inseminaciones))
            for i, reg in enumerate(inseminaciones):
                print(f"Registro {i+1}:")
                for key, value in reg.items():
                    print(f"  {key}: {value}")
        else:
            print("No hay registros de inseminaciones")
        print("==== FIN DE REGISTROS ====\n\n")
        
        # Obtener animales hembras del usuario actual disponibles para inseminación
        cursor.execute("""
            SELECT id, nombre, numero_arete, condicion
            FROM animales 
            WHERE usuario_id = %s AND sexo = 'Hembra'
            AND condicion IN ('Vaca', 'Vacona')
            ORDER BY nombre
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        return render_template('inseminaciones.html', 
                             inseminaciones=inseminaciones,
                             animales=animales)
    
    except Exception as e:
        flash(f'Error al cargar las inseminaciones: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/agregar_inseminacion', methods=['POST'])
@login_required
def agregar_inseminacion():
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha_inseminacion']
        tipo = request.form['tipo']
        semental = request.form.get('semental', '')
        raza_semental = request.form.get('raza_semental', '')
        codigo_pajuela = request.form.get('codigo_pajuela', '')
        inseminador = request.form['inseminador']
        observaciones = request.form.get('observaciones', '')
        exitosa = bool(int(request.form.get('exitosa', 0)))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO inseminaciones (
                animal_id, fecha_inseminacion, tipo, semental, 
                raza_semental, codigo_pajuela, inseminador, observaciones,
                exitosa
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (animal_id, fecha, tipo, semental, raza_semental,
              codigo_pajuela, inseminador, observaciones, exitosa))
        
        db.commit()
        flash('Inseminación registrada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar la inseminación: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('inseminaciones'))

@app.route('/eliminar_inseminacion', methods=['POST'])
@login_required
def eliminar_inseminacion():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        data = request.get_json()
        
        inseminacion_id = data.get('inseminacion_id')
        if not inseminacion_id:
            return jsonify({
                'success': False,
                'message': 'ID de inseminación no proporcionado'
            }), 400
        
        # Verificar que la inseminación existe
        cursor.execute("SELECT id FROM inseminaciones WHERE id = %s", (inseminacion_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'La inseminación no existe'
            }), 404
        
        cursor.execute("DELETE FROM inseminaciones WHERE id = %s", (inseminacion_id,))
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Inseminación eliminada correctamente'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error al eliminar la inseminación: {str(e)}'
        }), 500
        
    finally:
        cursor.close()
        db.close()

@app.route('/editar_inseminacion/<int:id>', methods=['POST'])
@login_required
def editar_inseminacion(id):
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha_inseminacion']
        tipo = request.form['tipo']
        semental = request.form.get('semental', '')
        raza_semental = request.form.get('raza_semental', '')
        codigo_pajuela = request.form.get('codigo_pajuela', '')
        inseminador = request.form['inseminador']
        observaciones = request.form.get('observaciones', '')
        exitosa = bool(int(request.form.get('exitosa', 0)))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que la inseminación existe
        cursor.execute("SELECT id FROM inseminaciones WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("La inseminación no existe")
        
        # Verificar que el animal existe y es válido
        cursor.execute("""
            SELECT id FROM animales 
            WHERE id = %s AND sexo = 'Hembra' 
            AND condicion IN ('Vaca', 'Vacona')
        """, (animal_id,))
        if not cursor.fetchone():
            raise Exception("El animal seleccionado no es válido")
        
        cursor.execute("""
            UPDATE inseminaciones 
            SET animal_id = %s, fecha_inseminacion = %s, tipo = %s,
                semental = %s, raza_semental = %s, codigo_pajuela = %s,
                inseminador = %s, observaciones = %s, exitosa = %s
            WHERE id = %s
        """, (animal_id, fecha, tipo, semental, raza_semental,
              codigo_pajuela, inseminador, observaciones, exitosa, id))
        
        db.commit()
        flash('Inseminación actualizada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar la inseminación: {str(e)}', 'danger')
        
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('inseminaciones'))

@app.route('/genealogia')
@login_required
def genealogia():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener registros genealógicos del usuario actual con nombres de animales
        cursor.execute("""
            SELECT g.*, 
                   a.nombre as nombre_animal,
                   a.numero_arete as animal_arete
            FROM genealogia g
            JOIN animales a ON g.animal_id = a.id
            WHERE a.usuario_id = %s
            ORDER BY a.nombre
        """, (session['usuario_id'],))
        genealogia = cursor.fetchall()
        
        # Obtener lista de animales del usuario actual para los selectores
        cursor.execute("""
            SELECT id, nombre, numero_arete 
            FROM animales 
            WHERE usuario_id = %s 
            ORDER BY nombre
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        return render_template('genealogia.html', 
                             genealogia=genealogia,
                             animales=animales)
    
    except Exception as e:
        flash(f'Error al cargar los registros genealógicos: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/agregar_genealogia', methods=['POST'])
@login_required
def agregar_genealogia():
    try:
        animal_id = request.form['animal_id']
        padre_arete = request.form.get('padre_arete', '')
        madre_arete = request.form.get('madre_arete', '')
        abuelo_paterno_arete = request.form.get('abuelo_paterno_arete', '')
        abuela_paterna_arete = request.form.get('abuela_paterna_arete', '')
        abuelo_materno_arete = request.form.get('abuelo_materno_arete', '')
        abuela_materna_arete = request.form.get('abuela_materna_arete', '')
        observaciones = request.form.get('observaciones', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO genealogia (animal_id, padre_arete, madre_arete, 
                                  abuelo_paterno_arete, abuela_paterna_arete,
                                  abuelo_materno_arete, abuela_materna_arete, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (animal_id, padre_arete, madre_arete, abuelo_paterno_arete, 
              abuela_paterna_arete, abuelo_materno_arete, abuela_materna_arete, observaciones))
        
        db.commit()
        flash('Registro genealógico agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el registro genealógico: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('genealogia'))

@app.route('/obtener_genealogia/<int:id>')
@login_required
def obtener_genealogia(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT g.*, 
                   a.nombre as nombre_animal,
                   a.numero_arete as animal_arete
            FROM genealogia g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.id = %s
        """, (id,))
        genealogia = cursor.fetchone()
        if not genealogia:
            raise Exception("Registro genealógico no encontrado")
            
        cursor.close()
        db.close()
        return jsonify(genealogia)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404

@app.route('/editar_genealogia/<int:id>', methods=['POST'])
@login_required
def editar_genealogia(id):
    try:
        animal_id = request.form['animal_id']
        padre_arete = request.form.get('padre_arete', '')
        madre_arete = request.form.get('madre_arete', '')
        abuelo_paterno_arete = request.form.get('abuelo_paterno_arete', '')
        abuela_paterna_arete = request.form.get('abuela_paterna_arete', '')
        abuelo_materno_arete = request.form.get('abuelo_materno_arete', '')
        abuela_materna_arete = request.form.get('abuela_materna_arete', '')
        observaciones = request.form.get('observaciones', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que el registro existe
        cursor.execute("SELECT id FROM genealogia WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("Registro genealógico no encontrado")
        
        # Verificar que el animal existe
        cursor.execute("SELECT id FROM animales WHERE id = %s", (animal_id,))
        if not cursor.fetchone():
            raise Exception("Animal no encontrado")
        
        cursor.execute("""
            UPDATE genealogia 
            SET animal_id = %s, padre_arete = %s, madre_arete = %s,
                abuelo_paterno_arete = %s, abuela_paterna_arete = %s,
                abuelo_materno_arete = %s, abuela_materna_arete = %s, observaciones = %s
            WHERE id = %s
        """, (animal_id, padre_arete, madre_arete, abuelo_paterno_arete,
              abuela_paterna_arete, abuelo_materno_arete, abuela_materna_arete, observaciones, id))
        
        db.commit()
        flash('Registro genealógico actualizado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar el registro genealógico: {str(e)}', 'danger')
        
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('genealogia'))

@app.route('/eliminar_genealogia/<int:id>', methods=['DELETE'])
@login_required
def eliminar_genealogia(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que el registro existe
        cursor.execute("SELECT id FROM genealogia WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("Registro genealógico no encontrado")
        
        cursor.execute("DELETE FROM genealogia WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Registro genealógico eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
        
    finally:
        cursor.close()
        db.close()

@app.route('/registro_leche')
@login_required
def registro_leche_redirect():
    return redirect(url_for('registro_leche.vista_registro_leche'))

@app.route('/registro_leche/obtener/<int:id>')
@login_required
def obtener_registro_leche(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT p.*, a.nombre as nombre_animal,
                   TO_CHAR(p.fecha, 'YYYY-MM-DD') as fecha_formato
            FROM produccion_leche p
            JOIN animales a ON p.animal_id = a.id
            WHERE p.id = %s
        """, (id,))
        
        registro = cursor.fetchone()
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        # Asegurarse de que la fecha esté en el formato correcto para el input date
        registro['fecha'] = registro['fecha_formato']
        return jsonify(registro)
        
    except Exception as e:
        app.logger.error(f'Error al obtener registro de leche: {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/registro_leche/editar/<int:id>', methods=['POST'])
@login_required
def editar_registro_leche(id):
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha']
        cantidad_manana = request.form['cantidad_manana']
        calidad = request.form['calidad']
        observaciones = request.form.get('observaciones', '')
        
        # Validar que la fecha no esté vacía
        if not fecha:
            raise ValueError('La fecha es requerida')
            
        # Convertir la fecha al formato correcto para PostgreSQL
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_postgres = fecha_obj.strftime('%Y-%m-%d')
        except ValueError as e:
            raise ValueError('Formato de fecha inválido. Use YYYY-MM-DD')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE produccion_leche
            SET animal_id = %s,
                fecha = %s,
                cantidad_manana = %s,
                cantidad_tarde = 0,
                calidad = %s,
                observaciones = %s
            WHERE id = %s
        """, (animal_id, fecha_postgres, cantidad_manana,
              calidad, observaciones, id))
        
        db.commit()
        flash('Registro de producción actualizado exitosamente', 'success')
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar el registro: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('registro_leche'))

@app.route('/ventas_leche')
@login_required
def ventas_leche():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        estado = request.args.get('estado')
        
        # Construir consulta base
        query = """
            SELECT *
            FROM ventas_leche
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(fecha) = %s"
            params.append(fecha)
        if estado:
            query += " AND estado_pago = %s"
            params.append(estado)
            
        query += " ORDER BY fecha DESC"
        
        cursor.execute(query, params)
        ventas = cursor.fetchall()
        
        # Calcular totales para hoy
        cursor.execute("""
            SELECT 
                SUM(cantidad_litros) as total_litros,
                SUM(total) as total_ingresos
            FROM ventas_leche 
            WHERE DATE(fecha) = CURRENT_DATE
        """)
        totales_hoy = cursor.fetchone()
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT 
                SUM(cantidad_litros) as total_litros,
                SUM(total) as total_ingresos
            FROM ventas_leche 
            WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE) 
            AND EXTRACT(MONTH FROM fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
        """)
        totales_mes = cursor.fetchone()
        
        return render_template('ventas_leche.html',
                             ventas=ventas,
                             total_hoy=totales_hoy['total_litros'] or 0,
                             ingresos_hoy=totales_hoy['total_ingresos'] or 0,
                             total_mes=totales_mes['total_litros'] or 0,
                             ingresos_mes=totales_mes['total_ingresos'] or 0)
    
    except Exception as e:
        flash(f'Error al cargar las ventas: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/ventas_leche/agregar', methods=['POST'])
@login_required
def agregar_venta_leche():
    try:
        fecha = request.form['fecha']
        cantidad_litros = float(request.form['cantidad_litros'])
        precio_litro = float(request.form['precio_litro'])
        comprador = request.form['comprador']
        forma_pago = request.form['forma_pago']
        estado_pago = request.form['estado_pago']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        total = cantidad_litros * precio_litro
        cursor.execute("""
            INSERT INTO ventas_leche (
                fecha, cantidad_litros, precio_litro, total,
                comprador, forma_pago, estado_pago
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fecha, cantidad_litros, precio_litro, total,
              comprador, forma_pago, estado_pago))
        
        db.commit()
        flash('Venta registrada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar la venta: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ventas_leche'))

@app.route('/ventas_leche/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_venta_leche(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM ventas_leche WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Venta eliminada correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/ventas_leche/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_venta_leche(id):
    try:
        if request.method == 'POST':
            fecha = request.form['fecha']
            cantidad_litros = float(request.form['cantidad_litros'])
            precio_litro = float(request.form['precio_litro'])
            comprador = request.form['comprador']
            forma_pago = request.form['forma_pago']
            estado_pago = request.form['estado_pago']
            
            db = get_db_connection()
            cursor = db.cursor()
            
            total = cantidad_litros * precio_litro
            cursor.execute("""
                UPDATE ventas_leche 
                SET fecha = %s,
                    cantidad_litros = %s,
                    precio_litro = %s,
                    total = %s,
                    comprador = %s,
                    forma_pago = %s,
                    estado_pago = %s
                WHERE id = %s
            """, (fecha, cantidad_litros, precio_litro, total,
                  comprador, forma_pago, estado_pago, id))
            
            db.commit()
            cursor.close()
            db.close()
            
            # Devolver respuesta JSON para solicitudes AJAX
            return jsonify({'success': True, 'message': 'Venta actualizada exitosamente'})
        else:
            # Obtener datos de la venta para el formulario
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM ventas_leche WHERE id = %s", (id,))
            venta = cursor.fetchone()
            cursor.close()
            db.close()
            
            if not venta:
                flash('Venta no encontrada', 'danger')
                return redirect(url_for('ventas_leche'))
                
            return jsonify(venta)
            
    except Exception as e:
        app.logger.error(f"Error al editar venta de leche: {str(e)}")
        if request.method == 'GET':
            return jsonify({'error': str(e)}), 500
        else:
            # Devolver respuesta JSON con error para solicitudes AJAX
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ingresos')
@login_required
def ingresos():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        categoria_id = request.args.get('categoria')
        
        # Construir consulta base
        query = """
            SELECT i.*, c.nombre as categoria_nombre
            FROM ingresos i
            JOIN categorias_ingreso c ON i.categoria_id = c.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(i.fecha) = %s"
            params.append(fecha)
        if categoria_id:
            query += " AND i.categoria_id = %s"
            params.append(categoria_id)
            
        query += " ORDER BY i.fecha DESC"
        
        cursor.execute(query, params)
        ingresos = cursor.fetchall()
        
        # Obtener categorías para el selector
        cursor.execute("SELECT * FROM categorias_ingreso ORDER BY nombre")
        categorias = cursor.fetchall()
        
        # Calcular totales para hoy
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE DATE(fecha) = CURRENT_DATE
        """)
        total_hoy = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE) 
            AND EXTRACT(MONTH FROM fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
        """)
        total_mes = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el año actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
        """)
        total_anio = cursor.fetchone()['total'] or 0
        
        return render_template('ingresos.html',
                             ingresos=ingresos,
                             categorias=categorias,
                             total_hoy=total_hoy,
                             total_mes=total_mes,
                             total_anio=total_anio)
    
    except Exception as e:
        flash(f'Error al cargar los ingresos: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/ingresos/agregar', methods=['POST'])
@login_required
def agregar_ingreso():
    try:
        fecha = request.form['fecha']
        categoria_id = request.form['categoria_id']
        monto = float(request.form['monto'])
        descripcion = request.form.get('descripcion', '')
        
        # Manejar el archivo de comprobante
        comprobante = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename:
                # Subir comprobante a Cloudinary
                cloudinary_url = upload_file(file, folder="comprobantes")
                if cloudinary_url:
                    comprobante = cloudinary_url
                    app.logger.info(f"Comprobante subido a Cloudinary: {cloudinary_url}")
                else:
                    flash('Error al subir el comprobante a Cloudinary', 'error')
                    return redirect(url_for('ingresos'))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO ingresos (
                fecha, categoria_id, monto, descripcion, comprobante
            ) VALUES (%s, %s, %s, %s, %s)
        """, (fecha, categoria_id, monto, descripcion, comprobante))
        
        db.commit()
        flash('Ingreso registrado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar el ingreso: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ingresos'))

@app.route('/ingresos/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_ingreso(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Primero obtenemos la información del ingreso para eliminar el comprobante si existe
        cursor.execute("SELECT comprobante FROM ingresos WHERE id = %s", (id,))
        ingreso = cursor.fetchone()
        
        if ingreso and ingreso['comprobante']:
            # Si es una URL de Cloudinary, eliminar de Cloudinary
            if 'cloudinary' in ingreso['comprobante']:
                public_id = get_public_id_from_url(ingreso['comprobante'])
                if public_id:
                    delete_file(public_id)
            # Si es un archivo local, intentar eliminarlo (para compatibilidad)
            else:
                try:
                    os.remove(ingreso['comprobante'])
                except OSError:
                    # Si el archivo no existe o no se puede eliminar, continuamos
                    pass
        
        cursor.execute("DELETE FROM ingresos WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Ingreso eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/ingresos/obtener/<int:id>', methods=['GET'])
@login_required
def obtener_ingreso(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT i.*, c.nombre as categoria_nombre 
            FROM ingresos i
            JOIN categorias_ingreso c ON i.categoria_id = c.id
            WHERE i.id = %s
        """, (id,))
        
        ingreso = cursor.fetchone()
        
        if not ingreso:
            return jsonify({'success': False, 'message': 'Ingreso no encontrado'}), 404
            
        # Formatear la fecha para que sea compatible con el input date
        if 'fecha' in ingreso and ingreso['fecha']:
            ingreso['fecha_formato'] = ingreso['fecha'].strftime('%Y-%m-%d')
            
        return jsonify({'success': True, 'ingreso': ingreso})
    except Exception as e:
        app.logger.error(f"Error al obtener ingreso: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/ingresos/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_ingreso(id):
    try:
        fecha = request.form['fecha']
        categoria_id = request.form['categoria_id']
        monto = float(request.form['monto'])
        descripcion = request.form.get('descripcion', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar si el ingreso existe
        cursor.execute("SELECT * FROM ingresos WHERE id = %s", (id,))
        ingreso_actual = cursor.fetchone()
        
        if not ingreso_actual:
            db.close()
            flash('Ingreso no encontrado', 'danger')
            return redirect(url_for('ingresos'))
        
        # Manejar el archivo de comprobante
        comprobante = ingreso_actual['comprobante']
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename:
                # Si hay un comprobante anterior en Cloudinary, eliminarlo
                if comprobante and 'cloudinary' in comprobante:
                    public_id = get_public_id_from_url(comprobante)
                    if public_id:
                        delete_file(public_id)
                
                # Subir nuevo comprobante a Cloudinary
                cloudinary_url = upload_file(file, folder="comprobantes")
                if cloudinary_url:
                    comprobante = cloudinary_url
                else:
                    flash('Error al subir el comprobante a Cloudinary', 'error')
                    return redirect(url_for('ingresos'))
        
        # Actualizar el ingreso
        cursor.execute("""
            UPDATE ingresos SET 
                fecha = %s, 
                categoria_id = %s, 
                monto = %s, 
                descripcion = %s, 
                comprobante = %s
            WHERE id = %s
        """, (fecha, categoria_id, monto, descripcion, comprobante, id))
        
        db.commit()
        flash('Ingreso actualizado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar el ingreso: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ingresos'))

@app.route('/gastos')
@login_required
def gastos():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        categoria_id = request.args.get('categoria')
        
        # Construir consulta base
        query = """
            SELECT g.*, c.nombre as categoria_nombre
            FROM gastos g
            JOIN categorias_gasto c ON g.categoria_id = c.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(g.fecha) = %s"
            params.append(fecha)
        if categoria_id:
            query += " AND g.categoria_id = %s"
            params.append(categoria_id)
            
        query += " ORDER BY g.fecha DESC"
        
        cursor.execute(query, params)
        gastos = cursor.fetchall()
        
        # Obtener categorías para el selector
        cursor.execute("SELECT * FROM categorias_gasto ORDER BY nombre")
        categorias = cursor.fetchall()
        
        # Calcular totales para hoy
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE DATE(fecha) = CURRENT_DATE
        """)
        total_hoy = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE) 
            AND EXTRACT(MONTH FROM fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
        """)
        total_mes = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el año actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
        """)
        total_anio = cursor.fetchone()['total'] or 0
        
        return render_template('gastos.html',
                             gastos=gastos,
                             categorias=categorias,
                             total_hoy=total_hoy,
                             total_mes=total_mes,
                             total_anio=total_anio)
    
    except Exception as e:
        flash(f'Error al cargar los gastos: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/gastos/agregar', methods=['POST'])
@login_required
def agregar_gasto():
    try:
        fecha = request.form['fecha']
        categoria_id = request.form['categoria_id']
        monto = float(request.form['monto'])
        descripcion = request.form.get('descripcion', '')
        
        # Manejar el archivo de comprobante
        comprobante = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename:
                # Subir comprobante a Cloudinary
                cloudinary_url = upload_file(file, folder="comprobantes")
                if cloudinary_url:
                    comprobante = cloudinary_url
                    app.logger.info(f"Comprobante subido a Cloudinary: {cloudinary_url}")
                else:
                    flash('Error al subir el comprobante a Cloudinary', 'error')
                    return redirect(url_for('gastos'))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO gastos (
                fecha, categoria_id, monto, descripcion, comprobante
            ) VALUES (%s, %s, %s, %s, %s)
        """, (fecha, categoria_id, monto, descripcion, comprobante))
        
        db.commit()
        flash('Gasto registrado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar el gasto: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('gastos'))

@app.route('/gastos/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_gasto(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Primero obtenemos la información del gasto para eliminar el comprobante si existe
        cursor.execute("SELECT comprobante FROM gastos WHERE id = %s", (id,))
        gasto = cursor.fetchone()
        
        if gasto and gasto['comprobante']:
            # Si es una URL de Cloudinary, eliminar de Cloudinary
            if 'cloudinary' in gasto['comprobante']:
                public_id = get_public_id_from_url(gasto['comprobante'])
                if public_id:
                    delete_file(public_id)
            # Si es un archivo local, intentar eliminarlo (para compatibilidad)
            else:
                try:
                    os.remove(gasto['comprobante'])
                except OSError:
                    # Si el archivo no existe o no se puede eliminar, continuamos
                    pass
        
        cursor.execute("DELETE FROM gastos WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Gasto eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/gastos/obtener/<int:id>', methods=['GET'])
@login_required
def obtener_gasto(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener los datos del gasto
        cursor.execute("""
            SELECT g.*, c.nombre as categoria_nombre
            FROM gastos g
            JOIN categorias_gasto c ON g.categoria_id = c.id
            WHERE g.id = %s
        """, (id,))
        
        gasto = cursor.fetchone()
        
        if not gasto:
            return jsonify({'success': False, 'message': 'Gasto no encontrado'}), 404
        
        # Formatear la fecha para que sea compatible con el input date
        if isinstance(gasto['fecha'], datetime):
            gasto['fecha'] = gasto['fecha'].strftime('%Y-%m-%d')
        
        return jsonify({'success': True, 'gasto': gasto})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/gastos/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_gasto(id):
    try:
        fecha = request.form['fecha']
        categoria_id = request.form['categoria_id']
        monto = float(request.form['monto'])
        descripcion = request.form.get('descripcion', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Primero obtenemos la información actual del gasto
        cursor.execute("SELECT comprobante FROM gastos WHERE id = %s", (id,))
        gasto_actual = cursor.fetchone()
        
        if not gasto_actual:
            flash('Gasto no encontrado', 'danger')
            return redirect(url_for('gastos'))
        
        # Manejar el archivo de comprobante
        comprobante = gasto_actual['comprobante']
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename:
                # Si hay un comprobante anterior en Cloudinary, eliminarlo
                if comprobante and 'cloudinary' in comprobante:
                    public_id = get_public_id_from_url(comprobante)
                    if public_id:
                        delete_file(public_id)
                
                # Subir nuevo comprobante a Cloudinary
                cloudinary_url = upload_file(file, folder="comprobantes")
                if cloudinary_url:
                    comprobante = cloudinary_url
                else:
                    flash('Error al subir el comprobante a Cloudinary', 'error')
                    return redirect(url_for('gastos'))
        
        # Actualizar el gasto en la base de datos
        cursor.execute("""
            UPDATE gastos 
            SET fecha = %s, categoria_id = %s, monto = %s, descripcion = %s, comprobante = %s
            WHERE id = %s
        """, (fecha, categoria_id, monto, descripcion, comprobante, id))
        
        db.commit()
        flash('Gasto actualizado exitosamente', 'success')
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        flash(f'Error al actualizar el gasto: {str(e)}', 'danger')
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()
    
    return redirect(url_for('gastos'))

@app.route('/reportes_financieros')
@login_required
def reportes_financieros():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener el año y mes actual
        fecha_actual = datetime.now()
        
        # Obtener los parámetros de filtrado
        año_filtro = request.args.get('anio', str(fecha_actual.year))
        mes_filtro = request.args.get('mes', str(fecha_actual.month))
        
        # Convertir a enteros
        año_actual = int(año_filtro)
        mes_actual = int(mes_filtro)
        
        # Nombres de los meses en español
        nombres_meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Obtener el nombre del mes actual
        nombre_mes_actual = nombres_meses[mes_actual]
        
        # Ya no necesitamos obtener los datos mensuales para el gráfico de evolución mensual
        
        # Obtener ingresos por categoría para el mes seleccionado
        cursor.execute("""
            SELECT 
                c.nombre as categoria, 
                COALESCE(SUM(i.monto), 0) as total
            FROM categorias_ingreso c
            LEFT JOIN ingresos i ON c.id = i.categoria_id 
                AND EXTRACT(YEAR FROM i.fecha) = %s 
                AND EXTRACT(MONTH FROM i.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año_actual, mes_actual))
        ingresos_por_categoria = cursor.fetchall()
        
        # Obtener gastos por categoría para el mes seleccionado
        cursor.execute("""
            SELECT 
                c.nombre as categoria, 
                COALESCE(SUM(g.monto), 0) as total
            FROM categorias_gasto c
            LEFT JOIN gastos g ON c.id = g.categoria_id 
                AND EXTRACT(YEAR FROM g.fecha) = %s 
                AND EXTRACT(MONTH FROM g.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año_actual, mes_actual))
        gastos_por_categoria = cursor.fetchall()
        
        # Calcular totales generales
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM ingresos 
            WHERE EXTRACT(YEAR FROM fecha) = %s
        """, (año_actual,))
        total_ingresos_anual = float(cursor.fetchone()['total'])
        
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM gastos 
            WHERE EXTRACT(YEAR FROM fecha) = %s
        """, (año_actual,))
        total_gastos_anual = float(cursor.fetchone()['total'])
        
        balance_anual = total_ingresos_anual - total_gastos_anual
        
        # Ya no necesitamos preparar datos para las gráficas
        
        return render_template('reportes_financieros.html', 
                               año_actual=año_actual,
                               mes_actual=mes_actual,
                               nombre_mes_actual=nombre_mes_actual,
                               ingresos_por_categoria=ingresos_por_categoria,
                               gastos_por_categoria=gastos_por_categoria,
                               total_ingresos_anual="%.2f" % total_ingresos_anual,
                               total_gastos_anual="%.2f" % total_gastos_anual,
                               balance_anual="%.2f" % balance_anual)
                             
    except Exception as e:
        flash(f'Error al generar el reporte financiero: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# Función global para agregar números de página y marca de agua en PDFs
def add_page_number(canvas, doc):
    canvas.saveState()
    
    # Agregar marca de agua
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'images', 'logo.png'))
    if os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            img_width = 350  # ancho de la imagen en puntos
            img_height = 350  # alto de la imagen en puntos
            # Calcular posición central
            x = (doc.pagesize[0] - img_width) / 2
            y = (doc.pagesize[1] - img_height) / 2
            # Dibujar imagen con transparencia
            canvas.saveState()
            canvas.setFillAlpha(0.6)  # 60% de opacidad
            canvas.drawImage(img, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
            canvas.restoreState()
        except Exception as e:
            print(f'Error al cargar la imagen: {str(e)}')
    
    # Agregar número de página
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(doc.pagesize[0] - 30, 30, f'Página {doc.page}')
    canvas.restoreState()

@app.route('/descargar_reporte_pdf')
@login_required
def descargar_reporte_pdf():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener los parámetros de filtrado
        año_filtro = request.args.get('anio', str(datetime.now().year))
        mes_filtro = request.args.get('mes', str(datetime.now().month))
        
        # Convertir a enteros
        año = int(año_filtro)
        mes = int(mes_filtro)
        
        # Nombres de los meses en español
        nombres_meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Obtener el nombre del mes
        nombre_mes = nombres_meses[mes]
        
        # Obtener ingresos por categoría para el mes seleccionado
        cursor.execute("""
            SELECT 
                c.nombre as categoria, 
                COALESCE(SUM(i.monto), 0) as total
            FROM categorias_ingreso c
            LEFT JOIN ingresos i ON c.id = i.categoria_id 
                AND EXTRACT(YEAR FROM i.fecha) = %s 
                AND EXTRACT(MONTH FROM i.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año, mes))
        ingresos_por_categoria = cursor.fetchall()
        
        # Obtener gastos por categoría para el mes seleccionado
        cursor.execute("""
            SELECT 
                c.nombre as categoria, 
                COALESCE(SUM(g.monto), 0) as total
            FROM categorias_gasto c
            LEFT JOIN gastos g ON c.id = g.categoria_id 
                AND EXTRACT(YEAR FROM g.fecha) = %s 
                AND EXTRACT(MONTH FROM g.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año, mes))
        gastos_por_categoria = cursor.fetchall()
        
        # Calcular totales
        total_ingresos = sum(float(ingreso['total']) for ingreso in ingresos_por_categoria)
        total_gastos = sum(float(gasto['total']) for gasto in gastos_por_categoria)
        balance = total_ingresos - total_gastos
        
        # Preparar contexto para la plantilla
        context = {
            'nombre_mes': nombre_mes,
            'año': año,
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'balance': balance,
            'ingresos_por_categoria': ingresos_por_categoria,
            'gastos_por_categoria': gastos_por_categoria,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "SISTEMA GANADERO FINCA ABIGAIL",
            'subtitulo': f"Reporte Financiero - {nombre_mes} {año}"
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/reporte_financiero.html', context)
        
    except Exception as e:
        flash(f'Error al generar el reporte PDF: {str(e)}', 'danger')
        if 'db' in locals() and db:
            db.close()
        return redirect(url_for('reportes_financieros'))
    finally:
        cursor.close()
        db.close()

@app.route('/planes_alimentacion')
@login_required
def planes_alimentacion():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM planes_alimentacion")
    planes = cursor.fetchall()
    return render_template('planes_alimentacion.html', planes=planes)

@app.route('/planes_alimentacion/agregar', methods=['POST'])
@login_required
def agregar_plan_alimentacion():
    try:
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO planes_alimentacion (nombre, descripcion)
            VALUES (%s, %s)
        """, (nombre, descripcion))
        
        db.commit()
        flash('Plan de alimentación agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el plan de alimentación: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('planes_alimentacion'))

@app.route('/registro_alimentacion')
@login_required
def registro_alimentacion():
    db = get_db_connection()
    cursor = db.cursor()
    
    # Obtener registros de alimentación
    cursor.execute("""
        SELECT ra.*, a.nombre as nombre_animal, pa.nombre as plan_nombre 
        FROM registro_alimentacion ra 
        JOIN animales a ON ra.animal_id = a.id 
        JOIN planes_alimentacion pa ON ra.plan_id = pa.id 
        WHERE ra.usuario_id = %s
        ORDER BY ra.fecha DESC
    """, (session['usuario_id'],))
    registros = cursor.fetchall()
    
    # Obtener animales para los dropdowns
    cursor.execute("""
        SELECT id, nombre, numero_arete 
        FROM animales 
        WHERE usuario_id = %s 
        ORDER BY nombre
    """, (session['usuario_id'],))
    animales = cursor.fetchall()
    
    # Obtener planes de alimentación
    cursor.execute("""
        SELECT id, nombre 
        FROM planes_alimentacion 
        WHERE usuario_id = %s 
        ORDER BY nombre
    """, (session['usuario_id'],))
    planes = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('registro_alimentacion.html', 
                         registros=registros, 
                         animales=animales, 
                         planes=planes)

@app.route('/registro_alimentacion/agregar', methods=['POST'])
@login_required
def agregar_registro_alimentacion():
    try:
        animal_id = request.form['animal_id']
        plan_id = request.form['plan_id']
        fecha = request.form['fecha']
        cantidad = request.form['cantidad']
        observaciones = request.form.get('observaciones', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO registro_alimentacion (
                animal_id, plan_id, fecha, cantidad, observaciones
            ) VALUES (%s, %s, %s, %s, %s)
        """, (animal_id, plan_id, fecha, cantidad, observaciones))
        
        db.commit()
        flash('Registro de alimentación agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el registro de alimentación: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('registro_alimentacion'))

@app.route('/mantenimientos')
@login_required
def mantenimientos():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT m.*, e.nombre as equipo_nombre 
        FROM mantenimientos m 
        JOIN equipos e ON m.equipo_id = e.id 
        ORDER BY m.fecha_programada
    """)
    mantenimientos = cursor.fetchall()
    return render_template('mantenimientos.html', mantenimientos=mantenimientos)

@app.route('/mantenimientos/agregar', methods=['POST'])
@login_required
def agregar_mantenimiento():
    try:
        equipo_id = request.form['equipo_id']
        tipo_mantenimiento = request.form['tipo_mantenimiento']
        fecha = request.form['fecha']
        descripcion = request.form['descripcion']
        costo = request.form.get('costo', 0)
        responsable = request.form.get('responsable', '')
        estado = request.form['estado']
        proxima_fecha = request.form.get('proxima_fecha', None)
        observaciones = request.form.get('observaciones', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO mantenimientos (
                equipo_id, tipo_mantenimiento, fecha, descripcion,
                costo, responsable, estado, proxima_fecha, observaciones
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (equipo_id, tipo_mantenimiento, fecha, descripcion,
              costo, responsable, estado, proxima_fecha, observaciones))
        
        db.commit()
        flash('Mantenimiento registrado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar el mantenimiento: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('mantenimientos'))

@app.route('/clima')
@login_required
def clima():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM registros_clima ORDER BY fecha DESC LIMIT 30")
    registros = cursor.fetchall()
    return render_template('clima.html', registros=registros)

@app.route('/trazabilidad')
@login_required
def trazabilidad():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT e.*, a.nombre as nombre_animal 
        FROM eventos_animal e 
        JOIN animales a ON e.animal_id = a.id 
        ORDER BY e.fecha DESC
    """)
    eventos = cursor.fetchall()
    return render_template('trazabilidad.html', eventos=eventos)

@app.route('/editar_pastizal/<int:pastizal_id>', methods=['POST'])
@login_required
def editar_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        nombre = request.form['nombre']
        dimension = float(request.form['dimension'])
        tipo_hierba = request.form['tipo_hierba']
        
        cursor.execute("""
            UPDATE pastizales 
            SET nombre = %s, area = %s, descripcion = %s 
            WHERE id = %s AND usuario_id = %s
        """, (nombre, dimension, f"Tipo de hierba: {tipo_hierba}", pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Pastizal actualizado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar el pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/eliminar_pastizal/<int:pastizal_id>', methods=['POST'])
@login_required
def eliminar_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si hay animales en el pastizal
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pastizales_animales 
            WHERE pastizal_id = %s
        """, (pastizal_id,))
        
        count = cursor.fetchone()[0]  # Acceder al primer elemento de la tupla
        
        if count > 0:
            flash('No se puede eliminar el pastizal porque tiene animales asignados', 'danger')
            return redirect(url_for('pastizales'))
        
        # Eliminar el pastizal
        cursor.execute("""
            DELETE FROM pastizales 
            WHERE id = %s AND usuario_id = %s
        """, (pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Pastizal eliminado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar el pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/cambiar_estado_pastizal/<int:pastizal_id>', methods=['POST'])
@login_required
def cambiar_estado_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        nuevo_estado = request.form['estado']
        fecha_disponible = None
        
        if nuevo_estado == 'En regeneración':
            # Si pasa a regeneración, calcular fecha disponible (30 días después)
            fecha_disponible = (datetime.now() + timedelta(days=30)).date()
        
        cursor.execute("""
            UPDATE pastizales 
            SET estado = %s
            WHERE id = %s AND usuario_id = %s
        """, (nuevo_estado, pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Estado del pastizal actualizado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar el estado del pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/retirar_animales/<int:pastizal_id>', methods=['POST'])
@login_required
def retirar_animales(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Marcar todas las asignaciones de animales como retiradas para este pastizal
        cursor.execute("""
            UPDATE animales_pastizal 
            SET fecha_retiro = CURRENT_DATE
            WHERE pastizal_id = %s AND fecha_retiro IS NULL
        """, (pastizal_id,))
        
        # Actualizar el estado del pastizal a "Inactivo"
        cursor.execute("""
            UPDATE pastizales 
            SET estado = 'Inactivo'
            WHERE id = %s AND usuario_id = %s
        """, (pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Animales retirados exitosamente del pastizal.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al retirar los animales: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/detalles_pastizal/<int:pastizal_id>')
@login_required
def detalles_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener detalles del pastizal
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT ap.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN animales_pastizal ap ON p.id = ap.pastizal_id AND ap.fecha_retiro IS NULL
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            flash('Pastizal no encontrado', 'danger')
            return redirect(url_for('pastizales'))
        
        # Obtener lista de animales en el pastizal
        cursor.execute("""
            SELECT a.*, ap.fecha_asignacion
            FROM animales a
            JOIN animales_pastizal ap ON a.id = ap.animal_id
            WHERE ap.pastizal_id = %s AND ap.fecha_retiro IS NULL
            ORDER BY ap.fecha_asignacion DESC
        """, (pastizal_id,))
        
        animales = cursor.fetchall()
        
        return render_template('detalles_pastizal.html', pastizal=pastizal, animales=animales)
        
    except Exception as e:
        flash(f'Error al cargar los detalles del pastizal: {str(e)}', 'danger')
        return redirect(url_for('pastizales'))
    finally:
        cursor.close()
        conn.close()

@app.route('/obtener_inseminacion/<int:id>')
@login_required
def obtener_inseminacion(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT i.*, a.nombre as nombre_animal, a.numero_arete as arete_animal
            FROM inseminaciones i 
            JOIN animales a ON i.animal_id = a.id 
            WHERE i.id = %s
        """, (id,))
        
        inseminacion = cursor.fetchone()
        if not inseminacion:
            raise Exception("Inseminación no encontrada")
            
        cursor.close()
        db.close()
        return jsonify(inseminacion)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404

@app.route('/ver_registro_fiebre_aftosa/<int:registro_id>')
@login_required
def ver_registro_fiebre_aftosa(registro_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener detalles del registro
        cursor.execute("""
            SELECT f.*, 
                   TO_CHAR(f.fecha_registro, 'DD/MM/YYYY') as fecha_registro_formato,
                   TO_CHAR(f.fecha_proxima_aplicacion, 'DD/MM/YYYY') as fecha_proxima_aplicacion_formato,
                   p.nombre as provincia, c.nombre as canton, pa.nombre as parroquia
            FROM fiebre_aftosa f
            LEFT JOIN provincias p ON f.provincia_id = p.id
            LEFT JOIN cantones c ON f.canton_id = c.id
            LEFT JOIN parroquias pa ON f.parroquia_id = pa.id
            WHERE f.id = %s
        """, (registro_id,))
        
        registro = cursor.fetchone()
        
        if not registro:
            flash('Registro no encontrado', 'danger')
            return redirect(url_for('fiebre_aftosa'))
        
        # Obtener los animales vacunados para este registro
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN fiebre_aftosa_animal fa ON a.id = fa.animal_id
            WHERE fa.fiebre_aftosa_id = %s
        """, (registro_id,))
        
        animales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('ver_registro_fiebre_aftosa.html', registro=registro, animales=animales)
    except Exception as e:
        app.logger.error(f'Error al ver detalles de fiebre aftosa: {str(e)}')
        flash(f'Error al cargar los detalles: {str(e)}', 'danger')
        return redirect(url_for('fiebre_aftosa'))

@app.route('/obtener_animales_vacunados/<int:registro_id>')
@login_required
def obtener_animales_vacunados(registro_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener los animales vacunados para este registro
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN fiebre_aftosa_animal fa ON a.id = fa.animal_id
            WHERE fa.fiebre_aftosa_id = %s
        """, (registro_id,))
        
        animales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(animales)
    except Exception as e:
        app.logger.error(f'Error al obtener animales vacunados: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/fiebre_aftosa')
@login_required
def fiebre_aftosa():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los animales del usuario actual
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(f.fecha_registro) 
                    FROM fiebre_aftosa f 
                    JOIN fiebre_aftosa_animal fa ON f.id = fa.fiebre_aftosa_id 
                    WHERE fa.animal_id = a.id) as ultima_vacunacion
            FROM animales a
            WHERE a.usuario_id = %s
            ORDER BY a.id DESC
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        # Obtener registros de fiebre aftosa del usuario actual
        cursor.execute("""
            SELECT f.*, 
                   (SELECT COUNT(*) 
                    FROM fiebre_aftosa_animal fa 
                    WHERE fa.fiebre_aftosa_id = f.id) as cantidad_animales,
                   f.nombre_propietario as propietario_nombre,
                   f.nombre_vacunador as vacunador_nombre,
                   p.nombre as provincia, 
                   c.nombre as canton, 
                   pa.nombre as parroquia
            FROM fiebre_aftosa f
            LEFT JOIN provincias p ON f.provincia_id = p.id
            LEFT JOIN cantones c ON f.canton_id = c.id
            LEFT JOIN parroquias pa ON f.parroquia_id = pa.id
            WHERE f.usuario_id = %s
            ORDER BY f.fecha_registro DESC
        """, (session['usuario_id'],))
        registros = cursor.fetchall()
        
        # Obtener provincias para el formulario
        cursor.execute("SELECT * FROM provincias ORDER BY nombre")
        provincias = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('fiebre_aftosa.html', 
                             animales=animales, 
                             registros=registros,
                             provincias=provincias)
                             
    except Exception as e:
        flash(f'Error al cargar la página: {str(e)}', 'danger')
        return render_template('fiebre_aftosa.html', animales=[], registros=[], provincias=[])

@app.route('/eliminar_fiebre_aftosa/<int:id>', methods=['POST'])
@login_required
def eliminar_fiebre_aftosa(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Primero eliminamos los registros relacionados en la tabla fiebre_aftosa_animal
        cursor.execute("DELETE FROM fiebre_aftosa_animal WHERE fiebre_aftosa_id = %s", (id,))
        
        # Luego eliminamos el registro principal en la tabla fiebre_aftosa
        cursor.execute("DELETE FROM fiebre_aftosa WHERE id = %s", (id,))
        
        conn.commit()
        flash('Registro de vacunación contra fiebre aftosa eliminado exitosamente', 'success')
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error al eliminar el registro: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect(url_for('fiebre_aftosa'))

@app.route('/registrar_inseminacion', methods=['POST'])
@login_required
def registrar_inseminacion():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        animal_id = request.form.get('animal_id')
        fecha_inseminacion = request.form.get('fecha_inseminacion')
        tipo_inseminacion = request.form.get('tipo_inseminacion')
        semental = request.form.get('semental')
        raza_semental = request.form.get('raza_semental', '')
        codigo_pajuela = request.form.get('codigo_pajuela', '')
        inseminador = request.form.get('inseminador', '')
        observaciones = request.form.get('observaciones', '')
        
        cursor.execute("""
            INSERT INTO inseminaciones (
                animal_id, fecha_inseminacion, tipo_inseminacion, 
                semental, raza_semental, codigo_pajuela, inseminador, observaciones, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pendiente')
        """, (animal_id, fecha_inseminacion, tipo_inseminacion, semental, raza_semental, codigo_pajuela, inseminador, observaciones))
        
        conn.commit()
        flash('Inseminación registrada exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('inseminaciones'))

@app.route('/actualizar_estado_inseminacion', methods=['POST'])
@login_required
def actualizar_estado_inseminacion():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        datos = request.get_json()
        inseminacion_id = datos.get('inseminacion_id')
        exitosa = datos.get('exitosa')  # Recibimos el valor booleano exitosa
        observaciones = datos.get('observaciones', '')
        
        # Verificar si la inseminación existe
        cursor.execute("""
            SELECT i.*, a.usuario_id, i.tipo_inseminacion 
            FROM inseminaciones i
            JOIN animales a ON i.animal_id = a.id
            WHERE i.id = %s
        """, (inseminacion_id,))
        
        inseminacion = cursor.fetchone()
        if not inseminacion or inseminacion['usuario_id'] != session['usuario_id']:
            raise Exception("Inseminación no encontrada")
        
        # Actualizar tanto el campo exitosa como el campo estado
        nuevo_estado = "Exitosa" if exitosa else "Fallida"
        cursor.execute("""
            UPDATE inseminaciones 
            SET exitosa = %s,
                estado = %s,
                observaciones = COALESCE(observaciones, '') || '\n' || %s
            WHERE id = %s
        """, (exitosa, nuevo_estado, "Estado actualizado: " + nuevo_estado, inseminacion_id))
        
        # Si la inseminación es exitosa, crear registro de gestación
        if exitosa:
            # Verificar si ya existe una gestación para este animal que esté activa
            cursor.execute("""
                SELECT id FROM gestaciones 
                WHERE animal_id = %s AND estado = 'En Gestación'
            """, (inseminacion['animal_id'],))
            
            if not cursor.fetchone():  # Si no existe, crear nueva gestación
                # Calcular fecha probable de parto (283 días después de la inseminación)
                fecha_inseminacion_obj = inseminacion['fecha_inseminacion']
                fecha_probable_parto = fecha_inseminacion_obj + timedelta(days=283)
                
                cursor.execute("""
                    INSERT INTO gestaciones (
                        animal_id, fecha_monta, fecha_probable_parto, observaciones, estado
                    ) VALUES (%s, %s, %s, %s, 'En Gestación')
                """, (inseminacion['animal_id'], inseminacion['fecha_inseminacion'], 
                     fecha_probable_parto,
                     f"Gestación iniciada por inseminación {inseminacion['tipo_inseminacion']}")
                )
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Estado actualizado correctamente'})
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error al actualizar estado de inseminación: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/vitaminizacion')
@login_required
def vitaminizacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los animales del usuario actual
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(v.fecha_aplicacion) 
                    FROM vitaminizaciones v 
                    WHERE v.animal_id = a.id) as ultima_vitaminizacion
            FROM animales a
            WHERE a.usuario_id = %s
            ORDER BY a.id DESC
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        # Obtener registros de vitaminización del usuario actual
        cursor.execute("""
            SELECT v.*, a.numero_arete, a.nombre, a.condicion
            FROM vitaminizaciones v
            JOIN animales a ON v.animal_id = a.id
            WHERE v.usuario_id = %s
            ORDER BY v.fecha_aplicacion DESC
        """, (session['usuario_id'],))
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('vitaminizacion.html', 
                             animales=animales, 
                             registros=registros,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de vitaminización: {str(e)}')
        flash('Error al cargar la página de vitaminización', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/registrar_vitaminizacion', methods=['POST'])
@login_required
def registrar_vitaminizacion():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        fecha_aplicacion = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        dosis = request.form.get('dosis', '')
        observaciones = request.form.get('observaciones', '')
        proxima_aplicacion = (datetime.strptime(fecha_aplicacion, '%Y-%m-%d') + timedelta(days=90)).strftime('%Y-%m-%d')
        
        if tipo_aplicacion == 'general':
            # Aplicar a todos los animales
            cursor.execute("""
                INSERT INTO vitaminizaciones 
                (animal_id, fecha_aplicacion, producto, dosis, fecha_proxima, observaciones, usuario_id)
                SELECT id, %s, %s, %s, %s, %s, %s FROM animales
            """, (fecha_aplicacion, producto, dosis, proxima_aplicacion, observaciones, session['user_id']))
        else:
            # Aplicar solo a animales seleccionados
            for animal_id in request.form.getlist('animales_seleccionados[]'):
                cursor.execute("""
                    INSERT INTO vitaminizaciones 
                    (animal_id, fecha_aplicacion, producto, dosis, fecha_proxima, observaciones, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (animal_id, fecha_aplicacion, producto, dosis, proxima_aplicacion, observaciones, session['user_id']))
        
        conn.commit()
        flash('Vitaminización registrada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('vitaminizacion'))

@app.route('/vitaminizacion/detalles/<int:id>')
@login_required
def detalles_vitaminizacion(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT v.*, a.numero_arete, a.nombre, a.condicion,
                   TO_CHAR(v.fecha_aplicacion, 'DD/MM/YYYY') as fecha_aplicacion_formato,
                   TO_CHAR(v.fecha_proxima, 'DD/MM/YYYY') as proxima_aplicacion_formato
            FROM vitaminizaciones v
            JOIN animales a ON v.animal_id = a.id
            WHERE v.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        registro['fecha_aplicacion'] = registro['fecha_aplicacion_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        return jsonify(registro)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/eliminar_vitaminizacion/<int:id>', methods=['POST'])
@login_required
def eliminar_vitaminizacion(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eliminar el registro de vitaminización
        cursor.execute("DELETE FROM vitaminizaciones WHERE id = %s", (id,))
        
        conn.commit()
        flash('Registro de vitaminización eliminado exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        app.logger.error(f'Error al eliminar vitaminización: {str(e)}')
        flash(f'Error al eliminar el registro de vitaminización: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('vitaminizacion'))

@app.route('/carbunco')
@login_required
def carbunco():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los animales del usuario actual
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(c.fecha_registro) 
                    FROM carbunco c 
                    JOIN carbunco_animal ca ON c.id = ca.carbunco_id 
                    WHERE ca.animal_id = a.id) as ultima_vacunacion
            FROM animales a
            WHERE a.usuario_id = %s
            ORDER BY a.id DESC
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        # Obtener registros de carbunco del usuario actual
        cursor.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) 
                    FROM carbunco_animal ca 
                    WHERE ca.carbunco_id = c.id) as cantidad_animales
            FROM carbunco c
            WHERE c.usuario_id = %s
            ORDER BY c.fecha_registro DESC
        """, (session['usuario_id'],))
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('carbunco.html', 
                             animales=animales, 
                             registros=registros,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de carbunco: {str(e)}')
        flash('Error al cargar la página de carbunco', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/registrar_carbunco', methods=['POST'])
@login_required
def registrar_carbunco():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        fecha_registro = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        if producto == 'otro':
            producto = request.form.get('otro_producto')
        lote = request.form.get('lote')
        vacunador = request.form.get('vacunador')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        
        # Calcular próxima aplicación (6 meses después)
        proxima_aplicacion = (datetime.strptime(fecha_registro, '%Y-%m-%d') + timedelta(days=180)).strftime('%Y-%m-%d')
        
        # Consulta corregida sin usuario_id
        cursor.execute("""
            INSERT INTO carbunco 
            (fecha_registro, producto, lote, vacunador, aplicacion_general, fecha_proxima)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (fecha_registro, producto, lote, vacunador, tipo_aplicacion == 'general', proxima_aplicacion))
        
        carbunco_id = cursor.lastrowid
        
        if tipo_aplicacion == 'general':
            cursor.execute("INSERT INTO carbunco_animal (carbunco_id, animal_id) SELECT %s, id FROM animales", (carbunco_id,))
        else:
            for animal_id in request.form.getlist('animales_seleccionados[]'):
                cursor.execute("INSERT INTO carbunco_animal (carbunco_id, animal_id) VALUES (%s, %s)", (carbunco_id, animal_id))
        
        conn.commit()
        flash('Vacunación contra Carbunco registrada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al registrar la vacunación: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('carbunco'))

@app.route('/eliminar_carbunco/<int:id>', methods=['POST'])
@login_required
def eliminar_carbunco(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Primero eliminamos los registros relacionados en la tabla carbunco_animal
        cursor.execute("DELETE FROM carbunco_animal WHERE carbunco_id = %s", (id,))
        
        # Luego eliminamos el registro principal en la tabla carbunco
        cursor.execute("DELETE FROM carbunco WHERE id = %s", (id,))
        
        conn.commit()
        flash('Registro de vacunación contra Carbunco eliminado exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar el registro: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('carbunco'))


@app.route('/carbunco/detalles/<int:id>')
@login_required
def detalles_carbunco(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener detalles del registro de carbunco
        cursor.execute("""
            SELECT c.*, TO_CHAR(c.fecha_registro, 'DD/MM/YYYY') as fecha_formato,
                   TO_CHAR(c.fecha_proxima, 'DD/MM/YYYY') as proxima_aplicacion_formato
            FROM carbunco c
            WHERE c.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            flash('Registro no encontrado', 'danger')
            return redirect(url_for('carbunco'))
        
        # Obtener animales vacunados
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN carbunco_animal ca ON a.id = ca.animal_id
            WHERE ca.carbunco_id = %s
        """, (id,))
        animales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Depurar los datos para ver qué contienen
        app.logger.info(f"Registro: {registro}")
        app.logger.info(f"Animales: {animales[:2]}")
        
        # Preparar los datos en el formato esperado por el frontend
        return jsonify({
            'fecha_registro': registro['fecha_formato'],
            'producto': registro['producto'] if 'producto' in registro else 'No especificado',
            'lote': registro['lote'] if 'lote' in registro else 'No especificado',
            'vacunador': registro['vacunador'] if 'vacunador' in registro else 'No especificado',
            'proxima_aplicacion': registro['proxima_aplicacion_formato'] if 'proxima_aplicacion_formato' in registro else 'No especificada',
            'animales': [{
                'id': animal['id'],
                'identificacion': animal['numero_arete'] if 'numero_arete' in animal else str(animal['id']),
                'categoria': animal['raza'] if 'raza' in animal else 'No especificada'
            } for animal in animales]
        })
    except Exception as e:
        app.logger.error(f'Error al obtener detalles de carbunco: {str(e)}')
        return jsonify({'error': str(e)}), 500

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Crear tabla de usuarios si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                nombre VARCHAR(100),
                apellido VARCHAR(100),
                telefono VARCHAR(20),
                direccion TEXT,
                foto_perfil VARCHAR(500),
                cargo VARCHAR(100),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de animales si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animales (
                id SERIAL PRIMARY KEY,
                numero_arete VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(100),
                sexo VARCHAR(10) NOT NULL CHECK (sexo IN ('Macho', 'Hembra')),
                raza VARCHAR(100),
                condicion VARCHAR(20) NOT NULL CHECK (condicion IN ('Toro', 'Torete', 'Vaca', 'Vacona', 'Ternero', 'Ternera')),
                fecha_nacimiento DATE,
                propietario VARCHAR(200),
                foto_path VARCHAR(500),
                padre_arete VARCHAR(50),
                madre_arete VARCHAR(50),
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de inseminaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inseminaciones (
                id SERIAL PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha_inseminacion DATE NOT NULL,
                tipo_inseminacion VARCHAR(50) NOT NULL,
                semental VARCHAR(100) NOT NULL,
                raza_semental VARCHAR(100),
                codigo_pajuela VARCHAR(100),
                inseminador VARCHAR(100),
                observaciones TEXT,
                estado VARCHAR(50) DEFAULT 'Pendiente',
                exitosa BOOLEAN DEFAULT FALSE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Crear tabla de carbunco si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carbunco (
                id SERIAL PRIMARY KEY,
                fecha_registro DATE NOT NULL,
                producto VARCHAR(100) NOT NULL,
                lote VARCHAR(50),
                vacunador VARCHAR(100),
                aplicacion_general BOOLEAN DEFAULT TRUE,
                proxima_aplicacion DATE,
                usuario_id INT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de relación carbunco_animal si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carbunco_animal (
                id SERIAL PRIMARY KEY,
                carbunco_id INT NOT NULL,
                animal_id INT NOT NULL,
                FOREIGN KEY (carbunco_id) REFERENCES carbunco(id),
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Verificar si la tabla inseminaciones existe y tiene las columnas necesarias
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'inseminaciones'
        """)
        
        if cursor.fetchone()[0] == 0:
            # La tabla no existe, ya se creó arriba
            pass
        else:
            # Verificar si faltan columnas y agregarlas
            columnas_faltantes = [
                ("raza_semental", "VARCHAR(100)", "semental"),
                ("codigo_pajuela", "VARCHAR(100)", "raza_semental"),
                ("inseminador", "VARCHAR(100)", "codigo_pajuela"),
                ("exitosa", "BOOLEAN DEFAULT FALSE", "observaciones")
            ]
            
            for columna, definicion, after in columnas_faltantes:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = 'inseminaciones' 
                    AND column_name = %s
                """, (columna,))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute(f"""
                        ALTER TABLE inseminaciones 
                        ADD COLUMN {columna} {definicion}
                    """)
        
        # Crear tabla de genealogía si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genealogia (
                id SERIAL PRIMARY KEY,
                animal_id INT NOT NULL,
                padre_arete VARCHAR(50),
                madre_arete VARCHAR(50),
                abuelo_paterno_arete VARCHAR(50),
                abuela_paterna_arete VARCHAR(50),
                abuelo_materno_arete VARCHAR(50),
                abuela_materna_arete VARCHAR(50),
                observaciones TEXT,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de animales_pastizal si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animales_pastizal (
                id SERIAL PRIMARY KEY,
                animal_id INT NOT NULL,
                pastizal_id INT NOT NULL,
                fecha_asignacion DATE NOT NULL,
                fecha_retiro DATE,
                observaciones TEXT,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id),
                FOREIGN KEY (pastizal_id) REFERENCES pastizales(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de pastizales si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pastizales (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                ubicacion TEXT,
                area DECIMAL(10,2),
                estado VARCHAR(20) DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo', 'Mantenimiento')),
                descripcion TEXT,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de registro_leche si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_leche (
                id SERIAL PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha DATE NOT NULL,
                cantidad_manana DECIMAL(10,2),
                cantidad_tarde DECIMAL(10,2),
                total_dia DECIMAL(10,2),
                observaciones TEXT,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de ventas_leche si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas_leche (
                id SERIAL PRIMARY KEY,
                fecha DATE NOT NULL,
                cantidad_litros DECIMAL(10,2) NOT NULL,
                precio_litro DECIMAL(10,2) NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                comprador VARCHAR(200),
                forma_pago VARCHAR(20) DEFAULT 'Efectivo' CHECK (forma_pago IN ('Efectivo', 'Transferencia', 'Cheque', 'Otro')),
                estado_pago VARCHAR(20) DEFAULT 'Pendiente' CHECK (estado_pago IN ('Pagado', 'Pendiente', 'Parcial')),
                observaciones TEXT,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de ingresos si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingresos (
                id SERIAL PRIMARY KEY,
                fecha DATE NOT NULL,
                categoria VARCHAR(100) NOT NULL,
                monto DECIMAL(10,2) NOT NULL,
                descripcion TEXT,
                comprobante VARCHAR(255),
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de gastos si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY,
                fecha DATE NOT NULL,
                categoria VARCHAR(100) NOT NULL,
                monto DECIMAL(10,2) NOT NULL,
                descripcion TEXT,
                comprobante VARCHAR(255),
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de desparasitaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS desparasitaciones (
                id SERIAL PRIMARY KEY,
                fecha_registro DATE NOT NULL,
                producto VARCHAR(100) NOT NULL,
                lote VARCHAR(50),
                aplicacion_general BOOLEAN DEFAULT TRUE,
                proxima_aplicacion DATE,
                usuario_id INT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de vitaminizaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vitaminizaciones (
                id SERIAL PRIMARY KEY,
                fecha_registro DATE NOT NULL,
                producto VARCHAR(100) NOT NULL,
                lote VARCHAR(50),
                aplicacion_general BOOLEAN DEFAULT TRUE,
                proxima_aplicacion DATE,
                usuario_id INT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de fiebre_aftosa si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fiebre_aftosa (
                id SERIAL PRIMARY KEY,
                fecha_registro DATE NOT NULL,
                producto VARCHAR(100) NOT NULL,
                lote VARCHAR(50),
                aplicacion_general BOOLEAN DEFAULT TRUE,
                proxima_aplicacion DATE,
                usuario_id INT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de gestaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gestaciones (
                id SERIAL PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha_monta DATE NOT NULL,
                fecha_probable_parto DATE NOT NULL,
                estado VARCHAR(20) NOT NULL DEFAULT 'En Gestación' CHECK (estado IN ('En Gestación', 'Finalizado', 'Abortado')),
                observaciones TEXT,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de auditoria si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditoria (
                id SERIAL PRIMARY KEY,
                usuario_id INT,
                accion VARCHAR(50) NOT NULL,
                modulo VARCHAR(50) NOT NULL,
                descripcion TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de config_alarmas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_alarmas (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                activo BOOLEAN DEFAULT TRUE,
                dias_antes INTEGER DEFAULT 7,
                usuario_id INT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear tabla de alarmas_enviadas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarmas_enviadas (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                descripcion TEXT,
                fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        
        conn.commit()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# Función equipos restaurada de manera segura
@app.route('/equipos')
@login_required
def equipos():
    # Versión segura que no accede a la base de datos
    flash('El módulo de equipos está temporalmente deshabilitado por mantenimiento.', 'warning')
    return render_template('mantenimiento.html', 
                          titulo="Módulo en Mantenimiento", 
                          mensaje="El módulo de gestión de equipos está temporalmente deshabilitado por mantenimiento.")
@app.route('/generar_reporte_pdf/<tipo>')
@login_required
def generar_reporte_pdf(tipo):
    try:
        app.logger.info(f'Iniciando generación de reporte PDF para tipo: {tipo}')
        
        # Verificar tipo válido
        tipos_validos = ['todos', 'toros', 'vacas', 'terneros', 'vaconas']
        if tipo not in tipos_validos:
            raise ValueError(f'Tipo de reporte no válido: {tipo}')

        # Obtener datos de los animales
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir consulta SQL
        query = "SELECT numero_arete, nombre, raza, condicion, sexo FROM animales WHERE usuario_id = %s"
        params = [session.get('usuario_id')]
        
        if tipo == 'toros':
            query += " AND sexo = 'Macho' AND condicion = 'Toro'"
        elif tipo == 'vacas':
            query += " AND sexo = 'Hembra' AND condicion = 'Vaca'"
        elif tipo == 'terneros':
            query += " AND (condicion = 'Ternero' OR condicion = 'Ternera')"
        elif tipo == 'vaconas':
            query += " AND sexo = 'Hembra' AND condicion = 'Vacona'"
        
        cursor.execute(query, params)
        animales = cursor.fetchall()
        
        if not animales:
            flash('No hay animales para generar el reporte', 'warning')
            return redirect(url_for('animales'))
            
        app.logger.info(f'Obtenidos {len(animales)} animales para el reporte')
        
        # Preparar contexto para la plantilla
        context = {
            'animales': animales,
            'tipo': tipo,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "SISTEMA GANADERO FINCA ABIGAIL",
            'subtitulo': "Reporte de " + ("Todos los Animales" if tipo == 'todos' else tipo.capitalize())
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/reporte_animales.html', context)
        
    except Exception as e:
        app.logger.error(f'Error al generar reporte PDF: {str(e)}')
        flash('Error al generar el reporte PDF', 'error')
        return redirect(url_for('animales'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        
        app.logger.info('PDF generado exitosamente')
        return response
        
    except Exception as e:
        app.logger.error(f'Error al generar reporte PDF: {str(e)}')
        app.logger.error('Traceback completo:', exc_info=True)
        flash(f'Error al generar el reporte PDF: {str(e)}', 'error')
        return redirect(url_for('animales'))
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/generar_reporte_gestacion')
@login_required
def generar_reporte_gestacion():
    try:
        # Obtener todas las gestaciones
        gestaciones = obtener_gestaciones()
        
        if not gestaciones:
            flash('No hay gestaciones registradas para generar el reporte', 'warning')
            return redirect(url_for('gestacion'))
            
        app.logger.info(f'Obtenidas {len(gestaciones)} gestaciones para el reporte')
        
        # Preparar contexto para la plantilla
        context = {
            'gestaciones': gestaciones,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "SISTEMA GANADERO FINCA ABIGAIL",
            'subtitulo': "Reporte de Gestaciones"
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/reporte_gestacion.html', context)
        
    except Exception as e:
        app.logger.error(f'Error al generar reporte de gestación: {str(e)}')
        flash('Error al generar el reporte PDF', 'error')
        return redirect(url_for('gestacion'))

@app.route('/generar_reporte_desparasitacion')
@app.route('/generar_reporte_desparasitacion/<fecha_inicio>/<fecha_fin>')
@login_required
def generar_reporte_desparasitacion(fecha_inicio=None, fecha_fin=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir la consulta base
        query = """
            SELECT d.*, a.numero_arete, a.nombre, a.condicion
            FROM desparasitaciones d
            INNER JOIN animales a ON d.animal_id = a.id
            WHERE d.usuario_id = %s
        """
        params = [session['usuario_id']]
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            query += " AND d.fecha_aplicacion BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
            
        query += " ORDER BY d.fecha_aplicacion DESC"
        
        cursor.execute(query, params)
        desparasitaciones = cursor.fetchall()
        
        if not desparasitaciones:
            flash('No hay registros de desparasitaciones para generar el reporte', 'warning')
            return redirect(url_for('desparasitacion'))
        
        # Preparar contexto para la plantilla
        context = {
            'desparasitaciones': desparasitaciones,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "SISTEMA GANADERO FINCA ABIGAIL",
            'subtitulo': "Reporte de Desparasitaciones",
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/reporte_desparasitacion.html', context)
        
    except Exception as e:
        app.logger.error(f'Error al generar reporte de desparasitación: {str(e)}')
        flash('Error al generar el reporte PDF', 'error')
        return redirect(url_for('desparasitacion'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        

        app.logger.error(f'Error al generar reporte PDF de desparasitaciones: {str(e)}')
        app.logger.error('Traceback completo:', exc_info=True)
        flash(f'Error al generar el reporte PDF: {str(e)}', 'error')
        return redirect(url_for('desparasitacion'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/generar_reporte_vitaminizacion')
@app.route('/generar_reporte_vitaminizacion/<fecha_inicio>/<fecha_fin>')
@login_required
def generar_reporte_vitaminizacion(fecha_inicio=None, fecha_fin=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir la consulta base
        query = """
            SELECT v.*, a.numero_arete, a.nombre, a.condicion
            FROM vitaminizaciones v
            INNER JOIN animales a ON v.animal_id = a.id
            WHERE 1 = 1
        """
        params = []
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            # Convertir las fechas a objetos datetime
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            # Ajustar fecha_fin para incluir todo el día
            fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
            
            query += " AND DATE(v.fecha_aplicacion) BETWEEN DATE(%s) AND DATE(%s)"
            params.extend([fecha_inicio, fecha_fin])
            
        query += " ORDER BY v.fecha_aplicacion DESC"
        
        cursor.execute(query, params)
        vitaminizaciones = cursor.fetchall()
        
        if not vitaminizaciones:
            flash('No hay registros de vitaminización para generar el reporte', 'warning')
            return redirect(url_for('vitaminizacion'))
        
        # Preparar contexto para la plantilla
        context = {
            'vitaminizaciones': vitaminizaciones,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "SISTEMA GANADERO FINCA ABIGAIL",
            'subtitulo': "Reporte de Vitaminización",
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/reporte_vitaminizacion.html', context)
        
        # Crear y estilizar la tabla

        
        # Generar PDF
        app.logger.info('Generando el documento PDF de vitaminización...')
        doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
        
        # Preparar descarga
        buffer.seek(0)
        response = send_file(
            buffer,
            download_name=f'reporte_vitaminizacion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
        app.logger.info('PDF de vitaminización generado exitosamente')
        return response
        
    except Exception as e:
        app.logger.error(f'Error al generar reporte PDF de vitaminización: {str(e)}')
        app.logger.error('Traceback completo:', exc_info=True)
        flash(f'Error al generar el reporte PDF: {str(e)}', 'error')
        return redirect(url_for('vitaminizacion'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/generar_certificado_aftosa/<int:certificado_id>')
@login_required
def generar_certificado_aftosa(certificado_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener información del registro de vacunación
        cursor.execute("""
            SELECT f.*, 
                   f.nombre_propietario as propietario_nombre,
                   f.nombre_vacunador as vacunador_nombre,
                   p.nombre as provincia, 
                   c.nombre as canton, 
                   pa.nombre as parroquia
            FROM fiebre_aftosa f
            LEFT JOIN provincias p ON f.provincia_id = p.id
            LEFT JOIN cantones c ON f.canton_id = c.id
            LEFT JOIN parroquias pa ON f.parroquia_id = pa.id
            WHERE f.id = %s
        """, (certificado_id,))
        registro = cursor.fetchone()
        
        if not registro:
            flash('Certificado no encontrado', 'error')
            return redirect(url_for('fiebre_aftosa'))
        
        # Obtener los animales vacunados
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            INNER JOIN fiebre_aftosa_animal fa ON a.id = fa.animal_id
            WHERE fa.fiebre_aftosa_id = %s
        """, (certificado_id,))
        animales = cursor.fetchall()
        
        # Preparar contexto para la plantilla
        context = {
            'registro': registro,
            'animales': animales,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "CERTIFICADO DE VACUNACIÓN - FIEBRE AFTOSA"
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/certificado_aftosa.html', context)
        
    except Exception as e:
        app.logger.error(f'Error al generar certificado de aftosa: {str(e)}')
        flash('Error al generar el certificado PDF', 'error')
        return redirect(url_for('fiebre_aftosa'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

        app.logger.error(f'Error al generar certificado PDF: {str(e)}')
        app.logger.error('Traceback completo:', exc_info=True)
        flash(f'Error al generar el certificado PDF: {str(e)}', 'error')
        return redirect(url_for('fiebre_aftosa'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/carbunco/generar_pdf/<int:registro_id>')
def generar_pdf_carbunco(registro_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener datos del registro de carbunco
        cursor.execute('''
            SELECT * 
            FROM carbunco
            WHERE id = %s
        ''', (registro_id,))
        registro = cursor.fetchone()
        
        if not registro:
            flash('Registro de vacunación no encontrado', 'error')
            return redirect(url_for('carbunco'))
        
        # Obtener los animales vacunados
        cursor.execute('''
            SELECT a.* 
            FROM animales a
            JOIN carbunco_animal ca ON a.id = ca.animal_id
            WHERE ca.carbunco_id = %s
        ''', (registro_id,))
        animales = cursor.fetchall()
        
        # Preparar contexto para la plantilla
        context = {
            'registro': registro,
            'animales': animales,
            'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'titulo': "CERTIFICADO DE VACUNACIÓN CONTRA CARBUNCO"
        }
        
        # Generar PDF usando xhtml2pdf
        return render_pdf_from_template('reportes_pdf/certificado_carbunco.html', context)
        
    except Exception as e:
        app.logger.error(f'Error al generar certificado de carbunco: {str(e)}')
        flash('Error al generar el certificado PDF', 'error')
        return redirect(url_for('carbunco'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para mostrar la página de registro de leche
@app.route('/registro_leche')
@login_required
def vista_registro_leche():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener registros de leche
        cursor.execute('''
            SELECT 
                animal_id, 
                fecha,
                cantidad_manana,
                cantidad_tarde,
                total_dia,
                observaciones
            FROM registro_leche
            ORDER BY fecha DESC
        ''')
        registros = cursor.fetchall()
        
        # Obtener IDs de animales
        animal_ids = {reg['animal_id'] for reg in registros}
        
        # Obtener detalles de animales
        animales_dict = {}
        if animal_ids:
            cursor.execute('SELECT id, nombre, numero_arete FROM animales WHERE id IN (%s)' % 
                         ','.join(str(id) for id in animal_ids))
            animales_dict = {a['id']: a for a in cursor.fetchall()}
        
        # Combinar información
        for reg in registros:
            animal = animales_dict.get(reg['animal_id'], {})
            reg['nombre_animal'] = animal.get('nombre', 'N/A')
            reg['numero_arete'] = animal.get('numero_arete', 'N/A')
            reg['fecha'] = reg['fecha'].strftime('%Y-%m-%d') if reg['fecha'] else 'N/A'
        
        # Obtener lista de animales para el formulario
        cursor.execute('SELECT id, nombre, numero_arete FROM animales WHERE sexo = "Hembra" AND condicion IN ("Vaca", "Vacona")')
        animales = cursor.fetchall()
        
        print('Registros encontrados:', len(registros))
        print('Primer registro:', registros[0] if registros else 'No hay registros')
        
        return render_template('registro_leche.html', registros=registros, animales=animales)
    except Exception as e:
        print(f"Error en vista_registro_leche: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('Error al cargar los registros de leche', 'error')
        return render_template('registro_leche.html', registros=[], animales=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# Esta ruta ha sido reemplazada por el blueprint registro_leche_bp

# Esta ruta ha sido reemplazada por el blueprint registro_leche_bp

# Esta ruta ha sido reemplazada por el blueprint registro_leche_bp

def render_pdf_from_template(template_name, context):
    html = render_template(template_name, **context)
    response = make_response()
    pdf = pisa.CreatePDF(html, dest=response)
    if not pdf.err:
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte.pdf'
        return response
    return 'Error al generar PDF', 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
