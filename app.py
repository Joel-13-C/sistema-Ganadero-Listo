from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, send_file
from src.database import DatabaseConnection, get_db_connection
from datetime import datetime, timedelta
from io import BytesIO
from src.auditoria import SistemaAuditoria
from src.alarmas import SistemaAlarmas
from src.chatbot import GanaderiaChatbot
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
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
from src.chatbot import GanaderiaChatbot
from src.gestacion import registrar_gestacion, obtener_gestaciones, actualizar_estado_gestacion, obtener_gestaciones_proximas, eliminar_gestacion
from datetime import date
from src.routes.registro_leche_routes import registro_leche_bp

# Asegurarse de que existe la carpeta static/comprobantes
if not os.path.exists('static/comprobantes'):
    os.makedirs('static/comprobantes', exist_ok=True)

# Copiar todos los comprobantes existentes a la carpeta static
if os.path.exists('uploads/comprobantes'):
    for archivo in os.listdir('uploads/comprobantes'):
        origen = os.path.join('uploads/comprobantes', archivo)
        destino = os.path.join('static/comprobantes', archivo)
        if os.path.isfile(origen) and not os.path.exists(destino):
            shutil.copy2(origen, destino)

# Inicializar el chatbot
chatbot = None

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)  # Clave secreta para sesiones
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Registrar el blueprint de registro_leche
app.register_blueprint(registro_leche_bp, url_prefix='/registro_leche')

# Ruta de redirección para /registro_leche
@app.route('/registro_leche')
def redirect_registro_leche():
    return redirect('/registro_leche/')

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
        
        app.logger.info(f'Verificación programada de alarmas: {partos} notificaciones de partos y {vacunaciones} de vacunaciones enviadas')
    except Exception as e:
        app.logger.error(f'Error en la verificación programada de alarmas: {str(e)}')

# Inicializar el planificador
scheduler = BackgroundScheduler()
# Ejecutar cada 6 horas en lugar de cada 24 horas para verificar más frecuentemente
scheduler.add_job(func=verificar_alarmas_programadas, trigger="interval", hours=6)

# Ejecutar la verificación de alarmas al iniciar la aplicación (después de 10 segundos)
scheduler.add_job(func=verificar_alarmas_programadas, trigger="date", run_date=datetime.now() + timedelta(seconds=10))
app.logger.info('Verificación inicial de alarmas programada')

# Iniciar el planificador
scheduler.start()

# Asegurar que el planificador se detenga cuando la aplicación se cierre
atexit.register(lambda: scheduler.shutdown())

# Ruta para servir archivos estáticos de uploads
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    app.logger.info(f"Solicitando archivo: {filename}")
    return send_from_directory(os.path.abspath('uploads'), filename)

# Ruta específica para comprobantes
@app.route('/ver_comprobante/<path:filepath>')
def ver_comprobante(filepath):
    app.logger.info(f"Solicitando comprobante: {filepath}")
    
    # Asegurarse de que la ruta no contenga intentos de acceder a directorios superiores
    if '..' in filepath:
        app.logger.error("Intento de acceso a directorios superiores detectado")
        return "Acceso denegado", 403
    
    # Limpiar la ruta para obtener solo el nombre del archivo
    if '/' in filepath:
        filename = filepath.split('/')[-1]
    elif '\\' in filepath:
        filename = filepath.split('\\')[-1]
    else:
        filename = filepath
    
    app.logger.info(f"Nombre de archivo extraído: {filename}")
    
    # Primero buscar en static/comprobantes
    ruta_static = os.path.join(os.path.abspath('static/comprobantes'), filename)
    if os.path.exists(ruta_static):
        app.logger.info(f"Archivo encontrado en static/comprobantes: {ruta_static}")
        # Obtener la extensión del archivo
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        # Establecer el tipo MIME adecuado según la extensión
        mimetype = None
        if extension in ['jpg', 'jpeg']:
            mimetype = 'image/jpeg'
        elif extension == 'png':
            mimetype = 'image/png'
        elif extension == 'gif':
            mimetype = 'image/gif'
        elif extension == 'pdf':
            mimetype = 'application/pdf'
        
        return send_from_directory(os.path.abspath('static/comprobantes'), filename, mimetype=mimetype)
    
    # Si no está en static, buscar en uploads/comprobantes
    ruta_uploads = os.path.join(os.path.abspath('uploads/comprobantes'), filename)
    if os.path.exists(ruta_uploads):
        app.logger.info(f"Archivo encontrado en uploads/comprobantes: {ruta_uploads}")
        # Obtener la extensión del archivo
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        # Establecer el tipo MIME adecuado según la extensión
        mimetype = None
        if extension in ['jpg', 'jpeg']:
            mimetype = 'image/jpeg'
        elif extension == 'png':
            mimetype = 'image/png'
        elif extension == 'gif':
            mimetype = 'image/gif'
        elif extension == 'pdf':
            mimetype = 'application/pdf'
        
        return send_from_directory(os.path.abspath('uploads/comprobantes'), filename, mimetype=mimetype)
    
    # Si no se encuentra en ninguna ubicación
    app.logger.error(f"El archivo no existe: {filename}")
    return f"Archivo no encontrado: {filename}", 404

# Ruta alternativa para servir comprobantes directamente
@app.route('/comprobantes/<path:filename>')
def serve_comprobante(filename):
    app.logger.info(f"Solicitando comprobante directo: {filename}")
    return send_from_directory(os.path.abspath('uploads/comprobantes'), filename)

# Ruta para servir comprobantes desde la carpeta static
@app.route('/static_comprobante/<path:filename>')
def static_comprobante(filename):
    app.logger.info(f"Solicitando comprobante desde static: {filename}")
    
    # Obtener la extensión del archivo
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Establecer el tipo MIME adecuado según la extensión
    mimetype = None
    if extension in ['jpg', 'jpeg']:
        mimetype = 'image/jpeg'
    elif extension == 'png':
        mimetype = 'image/png'
    elif extension == 'gif':
        mimetype = 'image/gif'
    elif extension == 'pdf':
        mimetype = 'application/pdf'
    
    return send_from_directory(os.path.abspath('static/comprobantes'), filename, mimetype=mimetype)

# Configuración del sistema de registro
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Iniciando Sistema Ganadero')

# Inicializar conexión de base de datos
try:
    db_connection = DatabaseConnection(app)
    # Inicializar el sistema de auditoría
    auditoria = SistemaAuditoria(get_db_connection)
    app.logger.info('Sistema de auditoría inicializado correctamente')
except Exception as e:
    app.logger.error(f"Error fatal al inicializar la base de datos: {e}")

# Inicializar chatbot
try:
    chatbot = GanaderiaChatbot(db_connection)
except NameError:
    app.logger.warning("db_connection no está definido, utilizando get_db_connection() como alternativa")
    chatbot = None  # Inicializamos como None y lo configuraremos más adelante

# Configuración de carga de archivos
UPLOAD_FOLDER = 'static/uploads/animales'
UPLOAD_FOLDER_PERFIL = 'static/uploads/perfiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ya tenemos la configuración de carga de imagen de perfil definida arriba

def allowed_file_perfil(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def inicio():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    return render_template('inicio.html')

@app.route('/login')
def login():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    username = request.form['username']
    password = request.form['password']
    
    user = db_connection.validate_user(username, password)
    if user:
        # Redirigir a la página principal del sistema
        session['username'] = username
        session['usuario_id'] = user['id']  # Guardar el ID de usuario en la sesión
        return redirect(url_for('dashboard'))
    else:
        flash('Credenciales incorrectas', 'error')
        return redirect(url_for('login'))

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

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener estadísticas generales
        cursor.execute("SELECT COUNT(*) as total FROM animales")
        total_animales = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM gestaciones WHERE estado = 'En Gestación'")
        total_gestaciones = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(cantidad) as total FROM registro_leche")
        total_leche = cursor.fetchone()['total'] or 0
        
        # Contar vacunaciones pendientes de todas las tablas
        # 1. Carbunco
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as total 
            FROM carbunco c 
            WHERE c.proxima_aplicacion BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """)
        total_carbunco = cursor.fetchone()['total']
        
        # 2. Vitaminización
        cursor.execute("""
            SELECT COUNT(DISTINCT v.id) as total 
            FROM vitaminizacion v 
            WHERE v.proxima_aplicacion BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """)
        total_vitaminizacion = cursor.fetchone()['total']
        
        # 3. Desparasitación
        cursor.execute("""
            SELECT COUNT(DISTINCT d.id) as total 
            FROM desparasitacion d 
            WHERE d.proxima_aplicacion BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """)
        total_desparasitacion = cursor.fetchone()['total']
        
        # 4. Vacunas tradicionales (si existen)
        try:
            cursor.execute("SELECT COUNT(*) as total FROM vacuna WHERE estado = 'Activo' AND fecha_proxima BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)")
            total_vacunas = cursor.fetchone()['total']
        except Exception as e:
            app.logger.error(f"Error al contar vacunas tradicionales: {str(e)}")
            total_vacunas = 0
            
        # Sumar todos los totales
        total_vacunaciones_pendientes = total_carbunco + total_vitaminizacion + total_desparasitacion + total_vacunas
        
        # Registrar en el log para depuración
        app.logger.info(f"Vacunaciones pendientes - Carbunco: {total_carbunco}, Vitaminización: {total_vitaminizacion}, Desparasitación: {total_desparasitacion}, Vacunas: {total_vacunas}, Total: {total_vacunaciones_pendientes}")
        
        
        # Obtener actividades recientes
        actividades = auditoria.obtener_actividad_reciente(limite=5)
        
        # Obtener próximos partos (próximos 30 días)
        cursor.execute("""
            SELECT g.*, a.nombre as nombre_animal, a.numero_arete
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE DATE_ADD(g.fecha_inseminacion, INTERVAL 283 DAY) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            AND g.estado = 'En Gestación'
            ORDER BY g.fecha_inseminacion ASC
            LIMIT 5
        """)
        proximos_partos = cursor.fetchall()
        
        # Obtener próximas vacunaciones (próximos 30 días) de todas las tablas
        # 1. Carbunco
        cursor.execute("""
            SELECT 
                c.id, 
                c.fecha_registro, 
                c.proxima_aplicacion as fecha_programada, 
                'Carbunco' as tipo_vacuna,
                c.producto,
                a.nombre as nombre_animal, 
                a.numero_arete,
                a.id as animal_id
            FROM carbunco c
            JOIN carbunco_animal ca ON c.id = ca.carbunco_id
            JOIN animales a ON ca.animal_id = a.id
            WHERE c.proxima_aplicacion BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            GROUP BY c.id, a.id
        """)
        proximas_carbunco = cursor.fetchall()
        
        # 2. Vitaminización
        cursor.execute("""
            SELECT 
                v.id, 
                v.fecha_registro, 
                v.proxima_aplicacion as fecha_programada, 
                'Vitaminización' as tipo_vacuna,
                v.producto,
                a.nombre as nombre_animal, 
                a.numero_arete,
                a.id as animal_id
            FROM vitaminizacion v
            JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id
            JOIN animales a ON va.animal_id = a.id
            WHERE v.proxima_aplicacion BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            GROUP BY v.id, a.id
        """)
        proximas_vitaminizacion = cursor.fetchall()
        
        # 3. Desparasitación
        cursor.execute("""
            SELECT 
                d.id, 
                d.fecha_registro, 
                d.proxima_aplicacion as fecha_programada, 
                'Desparasitación' as tipo_vacuna,
                d.producto,
                a.nombre as nombre_animal, 
                a.numero_arete,
                a.id as animal_id
            FROM desparasitacion d
            JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id
            JOIN animales a ON da.animal_id = a.id
            WHERE d.proxima_aplicacion BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            GROUP BY d.id, a.id
        """)
        proximas_desparasitacion = cursor.fetchall()
        
        # 4. Vacunas tradicionales (si existen)
        try:
            cursor.execute("""
                SELECT v.*, a.nombre as nombre_animal, a.numero_arete, v.tipo as tipo_vacuna,
                       v.fecha_proxima as fecha_programada
                FROM vacuna v
                JOIN animales a ON v.animal_id = a.id
                WHERE v.fecha_proxima BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                AND v.estado = 'Activo'
                ORDER BY v.fecha_proxima ASC
            """)
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
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', 
                               total_animales=total_animales,
                               total_gestaciones=total_gestaciones,
                               total_leche=total_leche,
                               total_vacunaciones_pendientes=total_vacunaciones_pendientes,
                               actividades=actividades,
                               proximos_partos=proximos_partos,
                               proximas_vacunaciones=proximas_vacunaciones,
                               now=datetime.now(),
                               timedelta=timedelta)
    except Exception as e:
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

@app.route('/verificar-alarmas-manual')
@login_required
def verificar_alarmas_manual():
    try:
        # Verificar partos próximos y vacunaciones pendientes
        notificaciones_partos = alarmas.verificar_partos_proximos()
        notificaciones_vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        
        total_notificaciones = notificaciones_partos + notificaciones_vacunaciones
        
        if total_notificaciones > 0:
            flash(f'Se enviaron {total_notificaciones} notificaciones', 'success')
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

@app.route('/verificar-alarmas')
@login_required
def verificar_alarmas():
    try:
        # Verificar partos próximos
        partos = alarmas.verificar_partos_proximos()
        
        # Verificar vacunaciones pendientes
        vacunaciones = alarmas.verificar_vacunaciones_pendientes()
        
        total = partos + vacunaciones
        
        if total > 0:
            flash(f'Se enviaron {total} notificaciones ({partos} de partos y {vacunaciones} de vacunaciones)', 'success')
        else:
            flash('No hay notificaciones pendientes para enviar', 'info')
        
        return redirect(url_for('configuracion_alarmas'))
    except Exception as e:
        flash(f'Error al verificar alarmas: {str(e)}', 'error')
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
def animales():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener el ID del usuario de la sesión
    usuario_id = session.get('usuario_id')
    
    if not usuario_id:
        flash('No se pudo identificar al usuario', 'error')
        return redirect(url_for('login'))
    
    # Obtener la lista de animales del usuario
    animales = db_connection.obtener_animales(usuario_id)
    
    # Pasar la fecha actual al contexto para calcular edades
    now = datetime.now().date()
    
    return render_template('animales.html', animales=animales, now=now)

@app.route('/registrar-animal', methods=['GET', 'POST'])
def registrar_animal():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
        datos_animal = {
            'numero_arete': request.form['numero_arete'],
            'nombre': request.form['nombre'],
            'sexo': request.form['sexo'],
            'raza': request.form['raza'],
            'condicion': request.form['condicion'],
            'fecha_nacimiento': request.form['fecha_nacimiento'],
            'propietario': request.form['propietario'],
            'padre_arete': request.form.get('padre_arete', None),
            'madre_arete': request.form.get('madre_arete', None),
            'usuario_id': session.get('usuario_id')
        }
        
        # Manejar la carga de la foto
        foto = request.files['foto']
        if foto and allowed_file(foto.filename):
            # Generar un nombre de archivo único
            filename = str(uuid.uuid4()) + '.' + foto.filename.rsplit('.', 1)[1].lower()
            
            # Asegurar que el directorio exista
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Guardar el archivo
            foto.save(filepath)
            
            # Ruta para la base de datos
            datos_animal['foto_path'] = f'static/uploads/animales/{filename}'
        else:
            # Si no se sube imagen, usar imagen de marcador de posición
            datos_animal['foto_path'] = 'static/images/upload-image-placeholder.svg'
            app.logger.error("No se subió imagen, usando marcador de posición")
        
        # Registrar el animal
        resultado = db_connection.registrar_animal(datos_animal)
        
        if resultado:
            # Registrar la actividad en el sistema de auditoría
            auditoria.registrar_actividad(
                accion='Registrar', 
                modulo='Animales', 
                descripcion=f'Se registró un nuevo animal: {datos_animal["nombre"]} (Arete: {datos_animal["numero_arete"]})'
            )
            flash('Animal registrado exitosamente', 'success')
            return redirect(url_for('animales'))
        else:
            flash('Error al registrar el animal', 'error')
    
    return render_template('registrar_animal.html')

@app.route('/editar-animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener el animal a editar sin verificar el usuario_id
    try:
        # No pasamos el usuario_id para permitir editar cualquier animal
        animal = db_connection.obtener_animal_por_id(animal_id)
        
        if not animal:
            flash('Animal no encontrado', 'error')
            return redirect(url_for('animales'))
        
        # Normalizar la ruta de la imagen
        if animal['foto_path']:
            # Si la ruta no comienza con 'static/', agregarla
            if not animal['foto_path'].startswith('static/'):
                animal['foto_path'] = f'static/{animal["foto_path"]}'
        else:
            # Usar imagen de marcador de posición
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
                filename = secure_filename(foto.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                foto.save(filepath)
                datos_animal['foto_path'] = f'static/uploads/animales/{filename}'
            
            # Llamar al método de actualización en la base de datos
            try:
                db_connection.actualizar_animal(animal_id, datos_animal)
                # Registrar la actividad en el sistema de auditoría
                auditoria.registrar_actividad(
                    accion='Actualizar', 
                    modulo='Animales', 
                    descripcion=f'Se actualizó la información del animal ID: {animal_id}'
                )
                return jsonify({
                    'success': True,
                    'message': 'Animal actualizado exitosamente'
                })
            except Exception as e:
                app.logger.error(f'Error al actualizar el animal: {str(e)}')
                return jsonify({
                    'success': False,
                    'message': f'Error al actualizar el animal: {str(e)}'
                })
        
        return render_template('editar_animal.html', animal=animal)
    
    except Exception as e:
        app.logger.error(f'Error al editar el animal: {str(e)}')
        flash(f'Error al editar el animal: {str(e)}', 'error')
        return redirect(url_for('animales'))

@app.route('/eliminar-animal/<int:animal_id>', methods=['GET'])
def eliminar_animal(animal_id):
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    try:
        # Obtener el ID de usuario de la sesión
        usuario_id = session.get('usuario_id')
        
        # Eliminar el animal de la base de datos
        resultado = db_connection.eliminar_animal(animal_id, usuario_id)
        
        # Registrar la actividad en el sistema de auditoría
        auditoria.registrar_actividad(
            accion='Eliminar', 
            modulo='Animales', 
            descripcion=f'Se eliminó el animal con ID: {animal_id}'
        )
        
        flash('Animal eliminado exitosamente', 'success')
        return redirect(url_for('animales'))
    
    except Exception as e:
        app.logger.error(f'Error al eliminar el animal: {str(e)}')
        flash(f'Error al eliminar el animal: {str(e)}', 'error')
        return redirect(url_for('animales'))

# La ruta de configuración ha sido eliminada ya que no es necesaria para el funcionamiento del sistema

@app.route('/perfil/editar', methods=['GET', 'POST'])
def editar_perfil():
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    usuario_id = session.get('usuario_id')
    
    try:
        # Obtener información actual del usuario desde la base de datos
        usuario = db_connection.obtener_usuario_por_id(usuario_id)
        
        if request.method == 'POST':
            # Procesar formulario de edición de perfil
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            cargo = request.form.get('cargo')
            direccion = request.form.get('direccion')
            
            # Validaciones básicas
            if not nombre or len(nombre) < 3:
                flash('El nombre debe tener al menos 3 caracteres', 'error')
                return render_template('editar_perfil.html', usuario=usuario)
                
            if not email or '@' not in email:
                flash('Ingrese un correo electrónico válido', 'error')
                return render_template('editar_perfil.html', usuario=usuario)
            
            # Verificar si el correo ya está en uso por otro usuario
            if email != usuario.get('email'):
                usuario_existente = db_connection.obtener_usuario_por_email(email)
                if usuario_existente and str(usuario_existente.get('id')) != str(usuario_id):
                    flash('Este correo electrónico ya está en uso', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
            
            # Manejar carga de imagen de perfil
            foto_perfil = request.files.get('foto_perfil')
            foto_path = None
            
            if foto_perfil and foto_perfil.filename:
                if not allowed_file_perfil(foto_perfil.filename):
                    flash('Formato de imagen no permitido. Use JPG, PNG o GIF', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
                    
                # Verificar tamaño de la imagen (máximo 5MB)
                if len(foto_perfil.read()) > 5 * 1024 * 1024:  # 5MB en bytes
                    foto_perfil.seek(0)  # Reiniciar el puntero del archivo
                    flash('La imagen es demasiado grande. Máximo 5MB', 'error')
                    return render_template('editar_perfil.html', usuario=usuario)
                
                foto_perfil.seek(0)  # Reiniciar el puntero del archivo
                filename = secure_filename(f"{usuario_id}_{foto_perfil.filename}")
                filepath = os.path.join(app.root_path, UPLOAD_FOLDER_PERFIL, filename)
                
                # Crear directorio si no existe
                os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER_PERFIL), exist_ok=True)
                
                foto_perfil.save(filepath)
                foto_path = f'/static/uploads/perfiles/{filename}'
                
                # Guardar foto en sesión
                session['foto_perfil'] = foto_path
            
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
            except Exception as e:
                app.logger.error(f"Error al verificar/crear columnas: {e}")
                # Continuamos con la actualización de todas formas
            
            # Actualizar información en la base de datos
            db_connection.actualizar_perfil_usuario(usuario_id, nombre, email, telefono, foto_path, cargo, direccion)
            
            # Actualizar sesión
            session['nombre'] = nombre
            session['email'] = email
            
            # Registrar en el sistema de auditoría
            auditoria.registrar_evento(
                usuario_id=usuario_id,
                tipo_evento='actualizacion_perfil',
                descripcion=f'Usuario {nombre} actualizó su perfil'
            )
            
            flash('Perfil actualizado exitosamente', 'success')
            return redirect(url_for('dashboard'))
        
        # Cargar foto de perfil de la sesión si existe
        usuario['foto_perfil'] = session.get('foto_perfil', '/static/images/default-avatar.png')
        
        return render_template('editar_perfil.html', usuario=usuario)
    
    except Exception as e:
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
    # Obtener solo animales hembra (vacas y vaconas)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nombre, numero_arete, condicion 
        FROM animales 
        WHERE sexo = 'Hembra' 
        AND condicion IN ('Vaca', 'Vacona')
        ORDER BY nombre
    """)
    animales = cursor.fetchall()
    cursor.close()
    conn.close()

    # Obtener todas las gestaciones
    gestaciones = obtener_gestaciones()
    
    return render_template('gestacion.html', animales=animales, gestaciones=gestaciones)

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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(d.fecha_registro) 
                    FROM desparasitacion d 
                    JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id 
                    WHERE da.animal_id = a.id) as ultima_desparasitacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de desparasitación
        cursor.execute("""
            SELECT d.*, 
                   (SELECT COUNT(*) 
                    FROM desparasitacion_animal da 
                    WHERE da.desparasitacion_id = d.id) as cantidad_animales
            FROM desparasitacion d
            ORDER BY d.fecha_registro DESC
        """)
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
        
        # Insertar registro de desparasitación
        cursor.execute("""
            INSERT INTO desparasitacion 
            (fecha_registro, producto, aplicacion_general, vacunador, proxima_aplicacion)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha_registro, producto, tipo_aplicacion == 'general', vacunador, proxima_aplicacion.strftime('%Y-%m-%d')))
        
        desparasitacion_id = cursor.lastrowid
        
        # Relacionar con animales
        if tipo_aplicacion == 'general':
            # Aplicar a todos los animales
            cursor.execute("""
                INSERT INTO desparasitacion_animal (desparasitacion_id, animal_id)
                SELECT %s, id FROM animales
            """, (desparasitacion_id,))
        else:
            # Aplicar solo a los animales seleccionados
            animales_seleccionados = request.form.getlist('animales_seleccionados[]')
            for animal_id in animales_seleccionados:
                cursor.execute("""
                    INSERT INTO desparasitacion_animal (desparasitacion_id, animal_id)
                    VALUES (%s, %s)
                """, (desparasitacion_id, animal_id))
        
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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener detalles del registro
        cursor.execute("""
            SELECT d.*, 
                   DATE_FORMAT(d.fecha_registro, '%d/%m/%Y') as fecha_registro_formato,
                   DATE_FORMAT(d.proxima_aplicacion, '%d/%m/%Y') as proxima_aplicacion_formato
            FROM desparasitacion d
            WHERE d.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        # Formatear fechas
        registro['fecha_registro'] = registro['fecha_registro_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        # Obtener animales relacionados
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN desparasitacion_animal da ON a.id = da.animal_id
            WHERE da.desparasitacion_id = %s
        """, (id,))
        registro['animales'] = cursor.fetchall()
        
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
        
        # Primero eliminar registros relacionados en desparasitacion_animal
        cursor.execute("DELETE FROM desparasitacion_animal WHERE desparasitacion_id = %s", (id,))
        
        # Luego eliminar el registro principal
        cursor.execute("DELETE FROM desparasitacion WHERE id = %s", (id,))
        
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
        cursor = conn.cursor(dictionary=True)
        
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
        cursor = conn.cursor(dictionary=True)
        
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
        cursor = conn.cursor(dictionary=True)

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
        cursor = conn.cursor(dictionary=True)
        
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
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener todos los pastizales del usuario
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
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
                nombre, dimension, tipo_hierba, estado, usuario_id
            ) VALUES (%s, %s, %s, 'Disponible', %s)
        """, (nombre, dimension, tipo_hierba, session['usuario_id']))
        
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
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener información del pastizal
        cursor.execute("""
            SELECT p.*,
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
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
                a.categoria,
                a.estado
            FROM animales a
            LEFT JOIN pastizales_animales pa ON a.id = pa.animal_id
            WHERE pa.id IS NULL
                AND a.usuario_id = %s
                AND a.estado = 'Activo'
            ORDER BY a.nombre
        """, (session['usuario_id'],))
        
        animales = cursor.fetchall()
        
        return jsonify({
            'capacidad_maxima': pastizal['capacidad_maxima'],
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
                p.capacidad_maxima,
                COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id, p.capacidad_maxima
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            flash('Pastizal no encontrado', 'danger')
            return redirect(url_for('pastizales'))
        
        capacidad_maxima = pastizal[0]
        animales_actuales = pastizal[1] or 0
        
        if len(animales) + animales_actuales > capacidad_maxima:
            flash(f'No se pueden asignar más de {capacidad_maxima} animales a este pastizal', 'danger')
            return redirect(url_for('pastizales'))
        
        # Actualizar estado del pastizal
        cursor.execute("""
            UPDATE pastizales 
            SET estado = 'En uso',
                fecha_ultimo_uso = %s
            WHERE id = %s AND usuario_id = %s
        """, (fecha_actual, pastizal_id, session['usuario_id']))
        
        # Registrar animales en el pastizal
        for animal_id in animales:
            cursor.execute("""
                INSERT INTO pastizales_animales (
                    pastizal_id, animal_id, fecha_ingreso
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
        cursor = db.cursor(dictionary=True)
        
        # Obtener todas las inseminaciones con detalles del animal
        cursor.execute("""
            SELECT 
                i.id, 
                i.animal_id, 
                DATE_FORMAT(i.fecha_inseminacion, '%d/%m/%Y') as fecha_inseminacion, 
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
            ORDER BY i.fecha_inseminacion DESC
        """)
        
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
        
        # Obtener animales hembras disponibles para inseminación
        cursor.execute("""
            SELECT id, nombre, numero_arete, condicion
            FROM animales 
            WHERE sexo = 'Hembra'
            AND condicion IN ('Vaca', 'Vacona')
            ORDER BY nombre
        """)
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
        cursor = db.cursor(dictionary=True)
        
        # Obtener registros genealógicos con nombres de animales
        cursor.execute("""
            SELECT g.*, 
                   a.nombre as nombre_animal,
                   p.nombre as padre_nombre,
                   m.nombre as madre_nombre
            FROM genealogia g
            JOIN animales a ON g.animal_id = a.id
            LEFT JOIN animales p ON g.padre_id = p.id
            LEFT JOIN animales m ON g.madre_id = m.id
            ORDER BY a.nombre
        """)
        genealogia = cursor.fetchall()
        
        # Obtener lista de animales para los selectores
        cursor.execute("SELECT id, nombre, numero_arete FROM animales ORDER BY nombre")
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
        padre_id = request.form['padre_id'] or None
        madre_id = request.form['madre_id'] or None
        caracteristicas = request.form.get('caracteristicas_heredadas', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO genealogia (animal_id, padre_id, madre_id, caracteristicas_heredadas)
            VALUES (%s, %s, %s, %s)
        """, (animal_id, padre_id, madre_id, caracteristicas))
        
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
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT g.*, 
                   a.nombre as nombre_animal,
                   p.nombre as padre_nombre,
                   m.nombre as madre_nombre
            FROM genealogia g
            JOIN animales a ON g.animal_id = a.id
            LEFT JOIN animales p ON g.padre_id = p.id
            LEFT JOIN animales m ON g.madre_id = m.id
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
        padre_id = request.form['padre_id'] or None
        madre_id = request.form['madre_id'] or None
        caracteristicas = request.form.get('caracteristicas_heredadas', '')
        
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
        
        # Si se especifica un padre, verificar que existe
        if padre_id:
            cursor.execute("SELECT id FROM animales WHERE id = %s", (padre_id,))
            if not cursor.fetchone():
                raise Exception("Padre no encontrado")
        
        # Si se especifica una madre, verificar que existe
        if madre_id:
            cursor.execute("SELECT id FROM animales WHERE id = %s", (madre_id,))
            if not cursor.fetchone():
                raise Exception("Madre no encontrada")
        
        cursor.execute("""
            UPDATE genealogia 
            SET animal_id = %s, padre_id = %s, madre_id = %s, 
                caracteristicas_heredadas = %s
            WHERE id = %s
        """, (animal_id, padre_id, madre_id, caracteristicas, id))
        
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
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, a.nombre as nombre_animal,
                   DATE_FORMAT(p.fecha, '%Y-%m-%d') as fecha_formato
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
            
        # Convertir la fecha al formato correcto para MySQL
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_mysql = fecha_obj.strftime('%Y-%m-%d')
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
        """, (animal_id, fecha_mysql, cantidad_manana,
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
        cursor = db.cursor(dictionary=True)
        
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
                SUM(total_venta) as total_ingresos
            FROM ventas_leche 
            WHERE DATE(fecha) = CURDATE()
        """)
        totales_hoy = cursor.fetchone()
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT 
                SUM(cantidad_litros) as total_litros,
                SUM(total_venta) as total_ingresos
            FROM ventas_leche 
            WHERE YEAR(fecha) = YEAR(CURDATE()) 
            AND MONTH(fecha) = MONTH(CURDATE())
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
        
        cursor.execute("""
            INSERT INTO ventas_leche (
                fecha, cantidad_litros, precio_litro,
                comprador, forma_pago, estado_pago
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (fecha, cantidad_litros, precio_litro,
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
            
            cursor.execute("""
                UPDATE ventas_leche 
                SET fecha = %s,
                    cantidad_litros = %s,
                    precio_litro = %s,
                    comprador = %s,
                    forma_pago = %s,
                    estado_pago = %s
                WHERE id = %s
            """, (fecha, cantidad_litros, precio_litro, 
                  comprador, forma_pago, estado_pago, id))
            
            db.commit()
            cursor.close()
            db.close()
            
            # Devolver respuesta JSON para solicitudes AJAX
            return jsonify({'success': True, 'message': 'Venta actualizada exitosamente'})
        else:
            # Obtener datos de la venta para el formulario
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
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
        cursor = db.cursor(dictionary=True)
        
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
            WHERE DATE(fecha) = CURDATE()
        """)
        total_hoy = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE YEAR(fecha) = YEAR(CURDATE()) 
            AND MONTH(fecha) = MONTH(CURDATE())
        """)
        total_mes = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el año actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE YEAR(fecha) = YEAR(CURDATE())
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
                # Generar un nombre único para el archivo para evitar colisiones
                # Usar timestamp + nombre original
                nombre_base = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{nombre_base}"
                
                # Asegurarse de que los directorios existen
                os.makedirs('uploads/comprobantes', exist_ok=True)
                os.makedirs('static/comprobantes', exist_ok=True)
                
                # Guardar el archivo en uploads/comprobantes
                filepath_uploads = os.path.join('uploads/comprobantes', filename)
                file.save(filepath_uploads)
                
                # Copiar el archivo a static/comprobantes para acceso directo
                filepath_static = os.path.join('static/comprobantes', filename)
                import shutil
                shutil.copy2(filepath_uploads, filepath_static)
                
                # Guardar solo el nombre del archivo en la base de datos
                comprobante = filename
                
                app.logger.info(f"Comprobante guardado: {filename} en ambas ubicaciones")
        
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
        cursor = db.cursor(dictionary=True)
        
        # Primero obtenemos la información del ingreso para eliminar el comprobante si existe
        cursor.execute("SELECT comprobante FROM ingresos WHERE id = %s", (id,))
        ingreso = cursor.fetchone()
        
        if ingreso and ingreso['comprobante']:
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
        cursor = db.cursor(dictionary=True)
        
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
        cursor = db.cursor(dictionary=True)
        
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
                # Si hay un comprobante anterior, eliminarlo
                if comprobante:
                    try:
                        os.remove(comprobante)
                    except OSError:
                        pass
                
                # Generar un nombre seguro para el archivo
                filename = secure_filename(file.filename)
                # Asegurarse de que el directorio existe
                os.makedirs('uploads/comprobantes', exist_ok=True)
                # Guardar el archivo
                filepath = os.path.join('uploads/comprobantes', filename)
                file.save(filepath)
                comprobante = filepath
        
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
        cursor = db.cursor(dictionary=True)
        
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
            WHERE DATE(fecha) = CURDATE()
        """)
        total_hoy = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE YEAR(fecha) = YEAR(CURDATE()) 
            AND MONTH(fecha) = MONTH(CURDATE())
        """)
        total_mes = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el año actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE YEAR(fecha) = YEAR(CURDATE())
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
                # Generar un nombre único para el archivo para evitar colisiones
                # Usar timestamp + nombre original
                nombre_base = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{nombre_base}"
                
                # Asegurarse de que los directorios existen
                os.makedirs('uploads/comprobantes', exist_ok=True)
                os.makedirs('static/comprobantes', exist_ok=True)
                
                # Guardar el archivo en uploads/comprobantes
                filepath_uploads = os.path.join('uploads/comprobantes', filename)
                file.save(filepath_uploads)
                
                # Copiar el archivo a static/comprobantes para acceso directo
                filepath_static = os.path.join('static/comprobantes', filename)
                import shutil
                shutil.copy2(filepath_uploads, filepath_static)
                
                # Guardar solo el nombre del archivo en la base de datos
                comprobante = filename
                
                app.logger.info(f"Comprobante guardado: {filename} en ambas ubicaciones")
        
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
        cursor = db.cursor(dictionary=True)
        
        # Primero obtenemos la información del gasto para eliminar el comprobante si existe
        cursor.execute("SELECT comprobante FROM gastos WHERE id = %s", (id,))
        gasto = cursor.fetchone()
        
        if gasto and gasto['comprobante']:
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
        cursor = db.cursor(dictionary=True)
        
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
        cursor = db.cursor(dictionary=True)
        
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
                # Si hay un comprobante anterior, intentamos eliminarlo
                if comprobante:
                    try:
                        # Eliminar de ambas ubicaciones
                        uploads_path = os.path.join('uploads/comprobantes', comprobante)
                        static_path = os.path.join('static/comprobantes', comprobante)
                        
                        if os.path.exists(uploads_path):
                            os.remove(uploads_path)
                        if os.path.exists(static_path):
                            os.remove(static_path)
                    except OSError:
                        # Si el archivo no existe o no se puede eliminar, continuamos
                        pass
                
                # Generar un nombre único para el nuevo archivo
                nombre_base = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{nombre_base}"
                
                # Asegurarse de que los directorios existen
                os.makedirs('uploads/comprobantes', exist_ok=True)
                os.makedirs('static/comprobantes', exist_ok=True)
                
                # Guardar el archivo en uploads/comprobantes
                filepath_uploads = os.path.join('uploads/comprobantes', filename)
                file.save(filepath_uploads)
                
                # Copiar el archivo a static/comprobantes para acceso directo
                filepath_static = os.path.join('static/comprobantes', filename)
                shutil.copy2(filepath_uploads, filepath_static)
                
                # Actualizar el nombre del comprobante
                comprobante = filename
        
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
        cursor = db.cursor(dictionary=True)
        
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
                AND YEAR(i.fecha) = %s 
                AND MONTH(i.fecha) = %s
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
                AND YEAR(g.fecha) = %s 
                AND MONTH(g.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año_actual, mes_actual))
        gastos_por_categoria = cursor.fetchall()
        
        # Calcular totales generales
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM ingresos 
            WHERE YEAR(fecha) = %s
        """, (año_actual,))
        total_ingresos_anual = float(cursor.fetchone()['total'])
        
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM gastos 
            WHERE YEAR(fecha) = %s
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
        cursor = db.cursor(dictionary=True)
        
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
                AND YEAR(i.fecha) = %s 
                AND MONTH(i.fecha) = %s
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
                AND YEAR(g.fecha) = %s 
                AND MONTH(g.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año, mes))
        gastos_por_categoria = cursor.fetchall()
        
        # Calcular totales
        total_ingresos = sum(float(ingreso['total']) for ingreso in ingresos_por_categoria)
        total_gastos = sum(float(gasto['total']) for gasto in gastos_por_categoria)
        balance = total_ingresos - total_gastos
        
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Título del reporte
        elements.append(Paragraph(f"Reporte Financiero - {nombre_mes} {año}", title_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Resumen general
        elements.append(Paragraph("Resumen General", subtitle_style))
        resumen_data = [
            ["Concepto", "Monto (MXN)"],
            ["Total Ingresos", f"${total_ingresos:,.2f}"],
            ["Total Gastos", f"${total_gastos:,.2f}"],
            ["Balance", f"${balance:,.2f}"]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, -1), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Ingresos por categoría
        elements.append(Paragraph(f"Ingresos por Categoría - {nombre_mes} {año}", subtitle_style))
        
        if ingresos_por_categoria:
            ingresos_data = [["Categoría", "Monto (MXN)"]]
            for ingreso in ingresos_por_categoria:
                if float(ingreso['total']) > 0:  # Solo incluir categorías con montos mayores a cero
                    ingresos_data.append([ingreso['categoria'], f"${float(ingreso['total']):,.2f}"])
            
            if len(ingresos_data) > 1:  # Si hay datos para mostrar
                ingresos_table = Table(ingresos_data, colWidths=[3.5*inch, 1.5*inch])
                ingresos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]))
                elements.append(ingresos_table)
            else:
                elements.append(Paragraph("No hay ingresos registrados para este período.", normal_style))
        else:
            elements.append(Paragraph("No hay ingresos registrados para este período.", normal_style))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Gastos por categoría
        elements.append(Paragraph(f"Gastos por Categoría - {nombre_mes} {año}", subtitle_style))
        
        if gastos_por_categoria:
            gastos_data = [["Categoría", "Monto (MXN)"]]
            for gasto in gastos_por_categoria:
                if float(gasto['total']) > 0:  # Solo incluir categorías con montos mayores a cero
                    gastos_data.append([gasto['categoria'], f"${float(gasto['total']):,.2f}"])
            
            if len(gastos_data) > 1:  # Si hay datos para mostrar
                gastos_table = Table(gastos_data, colWidths=[3.5*inch, 1.5*inch])
                gastos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.salmon),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]))
                elements.append(gastos_table)
            else:
                elements.append(Paragraph("No hay gastos registrados para este período.", normal_style))
        else:
            elements.append(Paragraph("No hay gastos registrados para este período.", normal_style))
        
        # Construir el PDF
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        # Preparar la respuesta
        buffer.seek(0)
        
        # Cerrar la conexión a la base de datos
        if 'db' in locals() and db:
            db.close()
        
        # Devolver el PDF como respuesta para descargar
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"reporte_financiero_{nombre_mes.lower()}_{año}.pdf",
            mimetype='application/pdf'
        )
        
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
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT ra.*, a.nombre as nombre_animal, pa.nombre as plan_nombre 
        FROM registro_alimentacion ra 
        JOIN animales a ON ra.animal_id = a.id 
        JOIN planes_alimentacion pa ON ra.plan_id = pa.id 
        ORDER BY ra.fecha DESC
    """)
    registros = cursor.fetchall()
    return render_template('registro_alimentacion.html', registros=registros)

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

# Función equipos eliminada para evitar problemas en el sistema

# Función agregar_equipo eliminada para evitar problemas en el sistema

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
            SET nombre = %s, dimension = %s, tipo_hierba = %s 
            WHERE id = %s AND usuario_id = %s
        """, (nombre, dimension, tipo_hierba, pastizal_id, session['usuario_id']))
        
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
            SET estado = %s, 
                fecha_ultimo_uso = CASE 
                    WHEN %s = 'En regeneración' THEN CURRENT_DATE 
                    ELSE fecha_ultimo_uso 
                END,
                fecha_disponible = %s
            WHERE id = %s AND usuario_id = %s
        """, (nuevo_estado, nuevo_estado, fecha_disponible, pastizal_id, session['usuario_id']))
        
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
        # Eliminar todas las asignaciones de animales para este pastizal
        cursor.execute("""
            DELETE FROM pastizales_animales 
            WHERE pastizal_id = %s
        """, (pastizal_id,))
        
        # Actualizar el estado del pastizal a "En regeneración"
        fecha_disponible = (datetime.now() + timedelta(days=30)).date()
        cursor.execute("""
            UPDATE pastizales 
            SET estado = 'En regeneración',
                fecha_ultimo_uso = CURRENT_DATE,
                fecha_disponible = %s
            WHERE id = %s AND usuario_id = %s
        """, (fecha_disponible, pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Animales retirados exitosamente. El pastizal ha entrado en período de regeneración.', 'success')
        
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
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener detalles del pastizal
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            flash('Pastizal no encontrado', 'danger')
            return redirect(url_for('pastizales'))
        
        # Obtener lista de animales en el pastizal
        cursor.execute("""
            SELECT a.*, pa.fecha_ingreso
            FROM animales a
            JOIN pastizales_animales pa ON a.id = pa.animal_id
            WHERE pa.pastizal_id = %s
            ORDER BY pa.fecha_ingreso DESC
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
        cursor = db.cursor(dictionary=True)
        
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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener detalles del registro
        cursor.execute("""
            SELECT f.*, 
                   DATE_FORMAT(f.fecha_registro, '%d/%m/%Y') as fecha_registro_formato,
                   DATE_FORMAT(f.fecha_proxima_aplicacion, '%d/%m/%Y') as fecha_proxima_aplicacion_formato,
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
        cursor = conn.cursor(dictionary=True)
        
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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(f.fecha_registro) 
                    FROM fiebre_aftosa f 
                    JOIN fiebre_aftosa_animal fa ON f.id = fa.fiebre_aftosa_id 
                    WHERE fa.animal_id = a.id) as ultima_vacunacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de fiebre aftosa con información completa
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
            ORDER BY f.fecha_registro DESC
        """)
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
    cursor = conn.cursor(dictionary=True)
    
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
    cursor = conn.cursor(dictionary=True)
    
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
                observaciones = CONCAT(COALESCE(observaciones, ''), '\n', %s)
            WHERE id = %s
        """, (exitosa, nuevo_estado, "Estado actualizado: " + nuevo_estado, inseminacion_id))
        
        # Si la inseminación es exitosa, crear registro de gestación
        if exitosa:
            # Verificar si ya existe una gestación para este animal que esté activa
            cursor.execute("""
                SELECT id FROM gestacion 
                WHERE animal_id = %s AND estado = 'En Gestación'
            """, (inseminacion['animal_id'],))
            
            if not cursor.fetchone():  # Si no existe, crear nueva gestación
                # Calcular fecha probable de parto (283 días después de la inseminación)
                fecha_inseminacion_obj = inseminacion['fecha_inseminacion']
                fecha_probable_parto = fecha_inseminacion_obj + timedelta(days=283)
                
                cursor.execute("""
                    INSERT INTO gestacion (
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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(v.fecha_registro) 
                    FROM vitaminizacion v 
                    JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id 
                    WHERE va.animal_id = a.id) as ultima_vitaminizacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de vitaminización
        cursor.execute("""
            SELECT v.*, 
                   (SELECT COUNT(*) 
                    FROM vitaminizacion_animal va 
                    WHERE va.vitaminizacion_id = v.id) as cantidad_animales
            FROM vitaminizacion v
            ORDER BY v.fecha_registro DESC
        """)
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
        fecha_registro = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        aplicador = request.form.get('aplicador')
        proxima_aplicacion = (datetime.strptime(fecha_registro, '%Y-%m-%d') + timedelta(days=90)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO vitaminizacion 
            (fecha_registro, producto, aplicacion_general, aplicador, proxima_aplicacion)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha_registro, producto, tipo_aplicacion == 'general', aplicador, proxima_aplicacion))
        
        vitaminizacion_id = cursor.lastrowid
        
        if tipo_aplicacion == 'general':
            cursor.execute("INSERT INTO vitaminizacion_animal (vitaminizacion_id, animal_id) SELECT %s, id FROM animales", (vitaminizacion_id,))
        else:
            for animal_id in request.form.getlist('animales_seleccionados[]'):
                cursor.execute("INSERT INTO vitaminizacion_animal (vitaminizacion_id, animal_id) VALUES (%s, %s)", (vitaminizacion_id, animal_id))
        
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
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT v.*, DATE_FORMAT(v.fecha_registro, '%d/%m/%Y') as fecha_registro_formato,
                   DATE_FORMAT(v.proxima_aplicacion, '%d/%m/%Y') as proxima_aplicacion_formato
            FROM vitaminizacion v
            WHERE v.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        registro['fecha_registro'] = registro['fecha_registro_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN vitaminizacion_animal va ON a.id = va.animal_id
            WHERE va.vitaminizacion_id = %s
        """, (id,))
        registro['animales'] = cursor.fetchall()
        
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
        
        # Primero eliminamos los registros relacionados en la tabla vitaminizacion_animal
        cursor.execute("DELETE FROM vitaminizacion_animal WHERE vitaminizacion_id = %s", (id,))
        
        # Luego eliminamos el registro principal de vitaminizacion
        cursor.execute("DELETE FROM vitaminizacion WHERE id = %s", (id,))
        
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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(c.fecha_registro) 
                    FROM carbunco c 
                    JOIN carbunco_animal ca ON c.id = ca.carbunco_id 
                    WHERE ca.animal_id = a.id) as ultima_vacunacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de carbunco con información completa
        cursor.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) 
                    FROM carbunco_animal ca 
                    WHERE ca.carbunco_id = c.id) as cantidad_animales
            FROM carbunco c
            ORDER BY c.fecha_registro DESC
        """)
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
            (fecha_registro, producto, lote, vacunador, aplicacion_general, proxima_aplicacion)
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
        cursor = conn.cursor(dictionary=True)
        
        # Obtener detalles del registro de carbunco
        cursor.execute("""
            SELECT c.*, DATE_FORMAT(c.fecha_registro, '%d/%m/%Y') as fecha_formato,
                   DATE_FORMAT(c.proxima_aplicacion, '%d/%m/%Y') as proxima_aplicacion_formato
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
        # Crear tabla de inseminaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inseminaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha_inseminacion DATE NOT NULL,
                tipo_inseminacion VARCHAR(50) NOT NULL,
                semental VARCHAR(100) NOT NULL,
                observaciones TEXT,
                estado VARCHAR(50) DEFAULT 'Pendiente',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Crear tabla de carbunco si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carbunco (
                id INT AUTO_INCREMENT PRIMARY KEY,
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
                id INT AUTO_INCREMENT PRIMARY KEY,
                carbunco_id INT NOT NULL,
                animal_id INT NOT NULL,
                FOREIGN KEY (carbunco_id) REFERENCES carbunco(id),
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Lista de columnas a verificar y agregar si no existen
        columnas = [
            ("tipo_inseminacion", "VARCHAR(50) NOT NULL", "fecha_inseminacion"),
            ("semental", "VARCHAR(100) NOT NULL", "tipo_inseminacion"),
            ("estado", "VARCHAR(50) DEFAULT 'Pendiente'", "observaciones"),
            ("exitosa", "BOOLEAN NULL", "observaciones")
        ]
        
        for columna, definicion, after in columnas:
            # Verificar si la columna existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'inseminaciones' 
                AND column_name = %s
            """, (columna,))
            
            if cursor.fetchone()[0] == 0:
                # Agregar columna si no existe
                cursor.execute(f"""
                    ALTER TABLE inseminaciones 
                    ADD COLUMN {columna} {definicion} 
                    AFTER {after}
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
    conn = None
    cursor = None
    try:
        app.logger.info(f'Iniciando generación de reporte PDF para tipo: {tipo}')
        
        # Verificar tipo válido
        tipos_validos = ['todos', 'toros', 'vacas', 'terneros', 'vaconas']
        if tipo not in tipos_validos:
            raise ValueError(f'Tipo de reporte no válido: {tipo}')

        # Obtener datos de los animales
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
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
        
        # Configurar el documento PDF con fondo personalizado
        buffer = BytesIO()
        
        def draw_background(canvas, doc):
            try:
                # Dibujar el logo como marca de agua
                logo_path = os.path.join('static', 'images', 'logo.png')
                if os.path.exists(logo_path):
                    # Guardar el estado actual del canvas
                    canvas.saveState()
                    
                    # Configurar transparencia (0.15 = 15% opacidad)
                    canvas.setFillAlpha(0.15)
                    canvas.setStrokeAlpha(0.15)
                    
                    # Reducir tamaño de la imagen para marca de agua
                    img_width = 180  # ancho deseado en puntos
                    img_height = 180  # alto deseado en puntos
                    
                    # Calcular posición para centrar la imagen
                    x = (doc.pagesize[0] - img_width) / 2
                    y = doc.pagesize[1] - 180  # Ajustar posición vertical
                    
                    # Dibujar la imagen como marca de agua
                    canvas.drawImage(logo_path, x, y, 
                                   width=img_width, height=img_height, 
                                   mask='auto',
                                   preserveAspectRatio=True)
                    
                    # Restaurar el estado original del canvas
                    canvas.restoreState()
                else:
                    app.logger.error(f'No se encontró el logo en: {logo_path}')
            except Exception as e:
                app.logger.error(f'Error al dibujar el logo: {str(e)}')
            
            # Agregar línea decorativa en la parte superior
            canvas.setStrokeColor(colors.darkgreen)
            canvas.setLineWidth(2)
            canvas.line(doc.leftMargin, doc.pagesize[1] - 50,
                      doc.pagesize[0] - doc.rightMargin, doc.pagesize[1] - 50)
            
            # Agregar pie de página con estilo mejorado
            canvas.setFont('Helvetica-Bold', 9)
            canvas.setFillColor(colors.darkgreen)
            
            # Línea superior del pie de página
            canvas.setStrokeColor(colors.darkgreen)
            canvas.setLineWidth(1)
            canvas.line(doc.leftMargin, doc.bottomMargin, 
                      doc.pagesize[0] - doc.rightMargin, doc.bottomMargin)
            
            # Texto del pie de página
            canvas.drawString(doc.leftMargin, doc.bottomMargin - 15, 
                            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Número de página
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            text_width = canvas.stringWidth(text, 'Helvetica-Bold', 9)
            canvas.drawString(doc.pagesize[0] - doc.rightMargin - text_width, 
                            doc.bottomMargin - 15, text)
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=80,  # Ajustar margen superior ya que el logo es marca de agua
            bottomMargin=50
        )
        
        # Preparar estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=colors.darkgreen
        )
        
        # Elementos del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph("SISTEMA GANADERO FINCA ABIGAIL", title_style))
        elements.append(Spacer(1, 20))
        
        # Subtítulo del reporte
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,
            textColor=colors.darkgreen
        )
        subtitulo_texto = "Reporte de " + ("Todos los Animales" if tipo == 'todos' else tipo.capitalize())
        elements.append(Paragraph(subtitulo_texto, subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Encabezados de la tabla
        headers = ["Número de Arete", "Nombre", "Raza", "Condición", "Sexo"]
        data = [headers]
        
        # Datos de la tabla
        for animal in animales:
            row = [
                str(animal['numero_arete']),
                str(animal['nombre']),
                str(animal['raza']),
                str(animal['condicion']),
                str(animal['sexo'])
            ]
            data.append(row)
        
        # Crear y estilizar la tabla
        table = Table(data, colWidths=[doc.width/5.0]*5)
        table.setStyle(TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Estilo del contenido
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWHEIGHT', (0, 0), (-1, -1), 30)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Agregar pie de página con fecha
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pie_pagina = Paragraph(
            f"Reporte generado el: {fecha_generacion}",
            styles['Normal']
        )
        elements.append(pie_pagina)
        
        # Construir el PDF con el fondo personalizado
        app.logger.info('Generando el documento PDF...')
        doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
        
        # Preparar para descarga
        buffer.seek(0)
        response = send_file(
            buffer,
            download_name=f'reporte_animales_{tipo}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
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
        
        # Configurar el documento PDF con fondo personalizado
        buffer = BytesIO()
        
        def draw_background(canvas, doc):
            try:
                # Dibujar el logo como marca de agua
                logo_path = os.path.join('static', 'images', 'logo.png')
                if os.path.exists(logo_path):
                    # Guardar el estado actual del canvas
                    canvas.saveState()
                    
                    # Configurar transparencia (0.15 = 15% opacidad)
                    canvas.setFillAlpha(0.15)
                    canvas.setStrokeAlpha(0.15)
                    
                    # Reducir tamaño de la imagen para marca de agua
                    img_width = 180  # ancho deseado en puntos
                    img_height = 180  # alto deseado en puntos
                    
                    # Calcular posición para centrar la imagen
                    x = (doc.pagesize[0] - img_width) / 2
                    y = doc.pagesize[1] - 180  # Ajustar posición vertical
                    
                    # Dibujar la imagen como marca de agua
                    canvas.drawImage(logo_path, x, y, 
                                   width=img_width, height=img_height, 
                                   mask='auto',
                                   preserveAspectRatio=True)
                    
                    # Restaurar el estado original del canvas
                    canvas.restoreState()
                else:
                    app.logger.error(f'No se encontró el logo en: {logo_path}')
            except Exception as e:
                app.logger.error(f'Error al dibujar el logo: {str(e)}')
            
            # Agregar línea decorativa en la parte superior
            canvas.setStrokeColor(colors.darkgreen)
            canvas.setLineWidth(2)
            canvas.line(doc.leftMargin, doc.pagesize[1] - 50,
                      doc.pagesize[0] - doc.rightMargin, doc.pagesize[1] - 50)
            
            # Agregar pie de página con estilo mejorado
            canvas.setFont('Helvetica-Bold', 9)
            canvas.setFillColor(colors.darkgreen)
            
            # Línea superior del pie de página
            canvas.setStrokeColor(colors.darkgreen)
            canvas.setLineWidth(1)
            canvas.line(doc.leftMargin, doc.bottomMargin, 
                      doc.pagesize[0] - doc.rightMargin, doc.bottomMargin)
            
            # Texto del pie de página
            canvas.drawString(doc.leftMargin, doc.bottomMargin - 15, 
                            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Número de página
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            text_width = canvas.stringWidth(text, 'Helvetica-Bold', 9)
            canvas.drawString(doc.pagesize[0] - doc.rightMargin - text_width, 
                            doc.bottomMargin - 15, text)
        
        # Usar orientación horizontal (landscape)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=60,
            bottomMargin=40
        )
        
        # Preparar estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=colors.darkgreen
        )
        
        # Elementos del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph("SISTEMA GANADERO FINCA ABIGAIL", title_style))
        elements.append(Spacer(1, 20))
        
        # Subtítulo del reporte
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,
            textColor=colors.darkgreen
        )
        elements.append(Paragraph("Reporte de Gestaciones", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Encabezados de la tabla
        headers = [
            "N° Arete", 
            "Nombre", 
            "Estado",
            "Fecha Monta",
            "Fecha Probable Parto",
            "Días Restantes"
        ]
        data = [headers]
        
        # Datos de la tabla
        for g in gestaciones:
            # Calcular fecha probable de parto
            fecha_probable = g['fecha_inseminacion'] + timedelta(days=283)
            dias_restantes = (fecha_probable - date.today()).days if g['estado'] == 'En Gestación' else 0
            
            row = [
                str(g['numero_arete']),
                str(g['nombre']),
                str(g['estado']),
                g['fecha_inseminacion'].strftime('%d/%m/%Y'),
                fecha_probable.strftime('%d/%m/%Y'),
                str(max(0, dias_restantes)) if g['estado'] == 'En Gestación' else '-'
            ]
            data.append(row)
        
        # Crear y estilizar la tabla
        # Ajustar anchos de columna para formato horizontal
        col_widths = [
            doc.width * 0.12,  # N° Arete
            doc.width * 0.20,  # Nombre
            doc.width * 0.15,  # Estado
            doc.width * 0.18,  # Fecha Monta
            doc.width * 0.20,  # Fecha Probable Parto
            doc.width * 0.15   # Días Restantes
        ]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Estilo del contenido
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWHEIGHT', (0, 0), (-1, -1), 30),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Construir el PDF con el fondo personalizado
        app.logger.info('Generando el documento PDF...')
        doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
        
        # Preparar para descarga
        buffer.seek(0)
        response = send_file(
            buffer,
            download_name=f'reporte_gestaciones_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
        app.logger.info('PDF generado exitosamente')
        return response
        
    except Exception as e:
        app.logger.error(f'Error al generar reporte PDF: {str(e)}')
        app.logger.error('Traceback completo:', exc_info=True)
        flash(f'Error al generar el reporte PDF: {str(e)}', 'error')
        return redirect(url_for('gestacion'))

@app.route('/generar_reporte_desparasitacion')
@app.route('/generar_reporte_desparasitacion/<fecha_inicio>/<fecha_fin>')
@login_required
def generar_reporte_desparasitacion(fecha_inicio=None, fecha_fin=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Construir la consulta base
        query = """
            SELECT d.*, da.animal_id, a.numero_arete, a.nombre, a.condicion
            FROM desparasitacion d
            INNER JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id
            INNER JOIN animales a ON da.animal_id = a.id
            WHERE 1 = 1
        """
        params = []
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            query += " AND d.fecha_registro BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
            
        query += " ORDER BY d.fecha_registro DESC"
        
        cursor.execute(query, params)
        desparasitaciones = cursor.fetchall()
        
        if not desparasitaciones:
            flash('No hay registros de desparasitaciones para generar el reporte', 'warning')
            return redirect(url_for('desparasitacion'))
        
        # Configurar el documento PDF
        buffer = BytesIO()
        
        def draw_background(canvas, doc):
            try:
                # Dibujar el logo como marca de agua
                logo_path = os.path.join('static', 'images', 'logo.png')
                if os.path.exists(logo_path):
                    canvas.saveState()
                    canvas.setFillAlpha(0.15)
                    canvas.setStrokeAlpha(0.15)
                    img_width = 180
                    img_height = 180
                    x = (doc.pagesize[0] - img_width) / 2
                    y = doc.pagesize[1] - 140
                    canvas.drawImage(logo_path, x, y,
                                   width=img_width, height=img_height,
                                   mask='auto',
                                   preserveAspectRatio=True)
                    canvas.restoreState()
            except Exception as e:
                app.logger.error(f'Error al dibujar el logo: {str(e)}')
            
            # Línea decorativa superior
            canvas.setStrokeColor(colors.darkgreen)
            canvas.setLineWidth(2)
            canvas.line(doc.leftMargin, doc.pagesize[1] - 40,
                      doc.pagesize[0] - doc.rightMargin, doc.pagesize[1] - 40)
            
            # Pie de página
            canvas.setFont('Helvetica-Bold', 9)
            canvas.setFillColor(colors.darkgreen)
            canvas.line(doc.leftMargin, doc.bottomMargin,
                      doc.pagesize[0] - doc.rightMargin, doc.bottomMargin)
            
            # Fecha de generación
            canvas.drawString(doc.leftMargin, doc.bottomMargin - 15,
                            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Número de página
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            text_width = canvas.stringWidth(text, 'Helvetica-Bold', 9)
            canvas.drawString(doc.pagesize[0] - doc.rightMargin - text_width,
                            doc.bottomMargin - 15, text)
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=60,
            bottomMargin=40
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=15,
            alignment=1,
            textColor=colors.darkgreen
        )
        
        elements = []
        
        # Título principal
        elements.append(Paragraph("SISTEMA GANADERO FINCA ABIGAIL", title_style))
        elements.append(Spacer(1, 15))
        
        # Subtítulo con rango de fechas si aplica
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            alignment=1,
            textColor=colors.darkgreen
        )
        
        subtitle_text = "Reporte de Desparasitaciones"
        if fecha_inicio and fecha_fin:
            subtitle_text += f" ({fecha_inicio} - {fecha_fin})"
        elements.append(Paragraph(subtitle_text, subtitle_style))
        elements.append(Spacer(1, 15))
        
        # Encabezados de la tabla
        headers = [
            "Fecha",
            "N° Arete",
            "Nombre",
            "Tipo Animal",
            "Producto",
            "Dosis",
            "Próxima Dosis"
        ]
        data = [headers]
        
        # Datos de la tabla
        for d in desparasitaciones:
            row = [
                d['fecha_registro'].strftime('%d/%m/%Y'),
                str(d['numero_arete']),
                str(d['nombre']),
                str(d['condicion']),
                str(d['producto']),
                'N/A',  # La tabla no tiene campo de dosis
                d['proxima_aplicacion'].strftime('%d/%m/%Y') if d['proxima_aplicacion'] else '-'
            ]
            data.append(row)
        
        # Crear y estilizar la tabla
        col_widths = [
            doc.width * 0.12,  # Fecha
            doc.width * 0.12,  # N° Arete
            doc.width * 0.18,  # Nombre
            doc.width * 0.15,  # Tipo Animal
            doc.width * 0.18,  # Producto
            doc.width * 0.10,  # Dosis
            doc.width * 0.15   # Próxima Dosis
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Estilo del contenido
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWHEIGHT', (0, 0), (-1, -1), 30),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Generar PDF
        app.logger.info('Generando el documento PDF de desparasitaciones...')
        doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
        
        # Preparar descarga
        buffer.seek(0)
        response = send_file(
            buffer,
            download_name=f'reporte_desparasitaciones_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
        app.logger.info('PDF de desparasitaciones generado exitosamente')
        return response
        
    except Exception as e:
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
        cursor = conn.cursor(dictionary=True)
        
        # Construir la consulta base
        query = """
            SELECT v.*, va.animal_id, a.numero_arete, a.nombre, a.condicion
            FROM vitaminizacion v
            INNER JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id
            INNER JOIN animales a ON va.animal_id = a.id
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
            
            query += " AND DATE(v.fecha_registro) BETWEEN DATE(%s) AND DATE(%s)"
            params.extend([fecha_inicio, fecha_fin])
            
        query += " ORDER BY v.fecha_registro DESC"
        
        cursor.execute(query, params)
        vitaminizaciones = cursor.fetchall()
        
        if not vitaminizaciones:
            flash('No hay registros de vitaminización para generar el reporte', 'warning')
            return redirect(url_for('vitaminizacion'))
        
        # Configurar el documento PDF
        buffer = BytesIO()
        
        def draw_background(canvas, doc):
            try:
                # Dibujar el logo como marca de agua
                logo_path = os.path.join('static', 'images', 'logo.png')
                if os.path.exists(logo_path):
                    canvas.saveState()
                    canvas.setFillAlpha(0.15)
                    canvas.setStrokeAlpha(0.15)
                    img_width = 180
                    img_height = 180
                    x = (doc.pagesize[0] - img_width) / 2
                    y = doc.pagesize[1] - 140
                    canvas.drawImage(logo_path, x, y,
                                   width=img_width, height=img_height,
                                   mask='auto',
                                   preserveAspectRatio=True)
                    canvas.restoreState()
            except Exception as e:
                app.logger.error(f'Error al dibujar el logo: {str(e)}')
            
            # Línea decorativa superior
            canvas.setStrokeColor(colors.darkgreen)
            canvas.setLineWidth(2)
            canvas.line(doc.leftMargin, doc.pagesize[1] - 40,
                      doc.pagesize[0] - doc.rightMargin, doc.pagesize[1] - 40)
            
            # Pie de página
            canvas.setFont('Helvetica-Bold', 9)
            canvas.setFillColor(colors.darkgreen)
            canvas.line(doc.leftMargin, doc.bottomMargin,
                      doc.pagesize[0] - doc.rightMargin, doc.bottomMargin)
            
            # Fecha de generación
            canvas.drawString(doc.leftMargin, doc.bottomMargin - 15,
                            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Número de página
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            text_width = canvas.stringWidth(text, 'Helvetica-Bold', 9)
            canvas.drawString(doc.pagesize[0] - doc.rightMargin - text_width,
                            doc.bottomMargin - 15, text)
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=60,
            bottomMargin=40
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=15,
            alignment=1,
            textColor=colors.darkgreen
        )
        
        elements = []
        
        # Título principal
        elements.append(Paragraph("SISTEMA GANADERO FINCA ABIGAIL", title_style))
        elements.append(Spacer(1, 15))
        
        # Subtítulo con rango de fechas si aplica
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            alignment=1,
            textColor=colors.darkgreen
        )
        
        subtitle_text = "Reporte de Vitaminización"
        if fecha_inicio and fecha_fin:
            subtitle_text += f" ({fecha_inicio} - {fecha_fin})"
        elements.append(Paragraph(subtitle_text, subtitle_style))
        elements.append(Spacer(1, 15))
        
        # Encabezados de la tabla
        headers = [
            "Fecha",
            "N° Arete",
            "Nombre",
            "Tipo Animal",
            "Producto",
            "Aplicador",
            "Próxima Aplicación"
        ]
        data = [headers]
        
        # Datos de la tabla
        for v in vitaminizaciones:
            row = [
                v['fecha_registro'].strftime('%d/%m/%Y'),
                str(v['numero_arete']),
                str(v['nombre']),
                str(v['condicion']),
                str(v['producto']),
                str(v['aplicador']),
                v['proxima_aplicacion'].strftime('%d/%m/%Y') if v['proxima_aplicacion'] else '-'
            ]
            data.append(row)
        
        # Crear y estilizar la tabla
        col_widths = [
            doc.width * 0.12,  # Fecha
            doc.width * 0.12,  # N° Arete
            doc.width * 0.18,  # Nombre
            doc.width * 0.15,  # Tipo Animal
            doc.width * 0.18,  # Producto
            doc.width * 0.12,  # Aplicador
            doc.width * 0.13   # Próxima Aplicación
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Estilo del contenido
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWHEIGHT', (0, 0), (-1, -1), 30),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
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
        cursor = conn.cursor(dictionary=True)
        
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
        
        # Configurar el documento PDF
        buffer = BytesIO()
        
        # Función para agregar números de página y marca de agua
        # Utilizando la función global add_page_number
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,  # Formato vertical
            rightMargin=25,
            leftMargin=25,
            topMargin=70,  # Aumentar margen superior para el encabezado
            bottomMargin=40  # Aumentar margen inferior para número de página
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor('#006400'),
            leading=32
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
            textColor=colors.HexColor('#006400'),
            leading=24
        )
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading3'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#006400'),
            leading=16
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            leading=12
        )
        
        def draw_header(canvas, doc):
            canvas.saveState()
            # Color principal azul médico
            main_color = colors.HexColor('#005B96')
            canvas.setStrokeColor(main_color)
            canvas.setFillColor(main_color)
            
            # Solo borde exterior
            canvas.setLineWidth(1)
            canvas.rect(15, 15, doc.pagesize[0]-30, doc.pagesize[1]-30)
            
            # Título con fondo azul
            canvas.rect(20, doc.pagesize[1]-80, doc.pagesize[0]-40, 40, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica-Bold', 18)
            canvas.drawCentredString(doc.pagesize[0]/2, doc.pagesize[1]-55, 
                                   'CERTIFICADO DE VACUNACIÓN - FIEBRE AFTOSA')
            
            canvas.restoreState()
        
        elements = []
        
        # Espacio para el contenido después del encabezado
        elements.append(Spacer(1, 10))
        
        # Estilo para las secciones
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=10,
            textColor=colors.HexColor('#005B96'),
            spaceAfter=3,
            spaceBefore=6,
            borderWidth=0,  # Quitar borde
            borderPadding=2,
            alignment=0,
            leading=12
        )
        
        # Definir anchos de columnas para las tablas
        page_width = doc.width
        col1_width = page_width * 0.98  # Para tablas de una columna
        col2_width = page_width * 0.48  # Para tablas de dos columnas

        # Información del certificado en formato de ficha
        elements.append(Paragraph("INFORMACIÓN DEL CERTIFICADO", section_style))
        cert_data = [
            [Paragraph("<b>N° Certificado:</b>", normal_style), 
             Paragraph(f"{registro['numero_certificado']}", normal_style)],
            [Paragraph("<b>Fecha:</b>", normal_style), 
             Paragraph(f"{registro['fecha_registro'].strftime('%d/%m/%Y')}", normal_style)]
        ]
        cert_table = Table(cert_data, colWidths=[doc.width*0.3, doc.width*0.7])
        cert_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
        ]))
        
        # Crear un marco alrededor de la sección
        section_data = [[cert_table]]
        section_table = Table(section_data, colWidths=[doc.width])
        section_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(section_table)
        elements.append(Spacer(1, 20))
        
        # Información del propietario
        prop_info = [
            [Paragraph("<b>Nombre del Propietario:</b>", normal_style),
             Paragraph(f"{registro['nombre_propietario']}", normal_style)],
            [Paragraph("<b>Nombre del Predio:</b>", normal_style),
             Paragraph(f"{registro['nombre_predio']}", normal_style)],
            [Paragraph("<b>Ubicación:</b>", normal_style),
             Paragraph(f"{registro['provincia']}, {registro['canton']}, {registro['parroquia']}", normal_style)]
        ]
        prop_table = Table(prop_info, colWidths=[col1_width*0.4, col1_width*0.6])
        prop_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
        ]))
        
        # Crear un marco alrededor de la sección
        section_data = [[prop_table]]
        section_table = Table(section_data, colWidths=[doc.width])
        section_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(section_table)
        elements.append(Spacer(1, 20))
        
        # Información de la vacunación
        vac_info = [
            [Paragraph("<b>Responsable de Vacunación:</b>", normal_style),
             Paragraph(f"{registro['nombre_vacunador']}", normal_style)],
            [Paragraph("<b>Fecha de Aplicación:</b>", normal_style),
             Paragraph(f"{registro['fecha_registro'].strftime('%d de %B de %Y')}", normal_style)],
            [Paragraph("<b>Tipo de Explotación:</b>", normal_style),
             Paragraph(f"{registro['tipo_explotacion']}", normal_style)]
        ]
        vac_table = Table(vac_info, colWidths=[col1_width*0.4, col1_width*0.6])
        vac_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
        ]))
        
        # Crear un marco alrededor de la sección
        section_data = [[vac_table]]
        section_table = Table(section_data, colWidths=[doc.width])
        section_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(section_table)
        elements.append(Spacer(1, 20))
        
        # Tabla de animales vacunados
        headers = ["N° Arete", "Nombre", "Raza", "Sexo"]
        data = [headers]
        
        # Datos de la tabla
        for animal in animales:
            row = [
                str(animal['numero_arete']),
                str(animal['nombre']),
                str(animal['raza']),
                str(animal['sexo'])
            ]
            data.append(row)
        
        # Crear y estilizar la tabla
        animals_table = Table(data, colWidths=[col2_width/4.0]*4)
        # Estilo común para todas las tablas
        common_style = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('LINEBEFORE', (0, 0), (0, -1), 0.5, colors.gray),
            ('LINEAFTER', (-1, 0), (-1, -1), 0.5, colors.gray),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.gray),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.gray),
        ]
        
        # Aplicar estilos a las tablas
        cert_table.setStyle(TableStyle(common_style))
        elements.append(cert_table)
        elements.append(Spacer(1, 10))
        
        # Información del propietario
        elements.append(Paragraph("DATOS DEL PROPIETARIO", section_style))
        prop_data = [
            [Paragraph("<b>Nombre:</b>", normal_style),
             Paragraph(f"{registro['nombre_propietario']}", normal_style)],
            [Paragraph("<b>Predio:</b>", normal_style),
             Paragraph(f"{registro['nombre_predio']}", normal_style)],
            [Paragraph("<b>Ubicación:</b>", normal_style),
             Paragraph(f"{registro['provincia']}, {registro['canton']}, {registro['parroquia']}", normal_style)]
        ]
        prop_table = Table(prop_data, colWidths=[doc.width*0.3, doc.width*0.7])
        prop_table.setStyle(TableStyle(common_style))
        elements.append(prop_table)
        elements.append(Spacer(1, 10))
        
        # Información de la vacunación
        elements.append(Paragraph("DATOS DE LA VACUNACIÓN", section_style))
        vac_data = [
            [Paragraph("<b>Responsable:</b>", normal_style),
             Paragraph(f"{registro['nombre_vacunador']}", normal_style)],
            [Paragraph("<b>Fecha Aplicación:</b>", normal_style),
             Paragraph(f"{registro['fecha_registro'].strftime('%d/%m/%Y')}", normal_style)],
            [Paragraph("<b>Tipo Explotación:</b>", normal_style),
             Paragraph(f"{registro['tipo_explotacion']}", normal_style)]
        ]
        vac_table = Table(vac_data, colWidths=[doc.width*0.3, doc.width*0.7])
        vac_table.setStyle(TableStyle(common_style))
        elements.append(vac_table)
        elements.append(Spacer(1, 10))
        
        # Forzar nueva página para la lista de animales y firmas
        elements.append(PageBreak())
        elements.append(Spacer(1, 40))  # Agregar espacio después del salto de página
        
        # Tabla de animales
        elements.append(Paragraph("REGISTRO DE ANIMALES VACUNADOS", section_style))
        
        # Encabezados y datos
        headers = [[Paragraph("<b>N° Arete</b>", normal_style),
                   Paragraph("<b>Nombre</b>", normal_style),
                   Paragraph("<b>Raza</b>", normal_style),
                   Paragraph("<b>Sexo</b>", normal_style)]]
        
        animal_data = []
        for animal in animales:
            animal_data.append([
                Paragraph(str(animal['numero_arete']), normal_style),
                Paragraph(str(animal['nombre']), normal_style),
                Paragraph(str(animal['raza']), normal_style),
                Paragraph(str(animal['sexo']), normal_style)
            ])
        
        animals_table = Table(headers + animal_data, colWidths=[doc.width/4.0]*4)
        animals_table.setStyle(TableStyle(
            common_style + [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005B96')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]
        ))
        elements.append(animals_table)
        
        # Espacio para firmas
        elements.append(Spacer(1, 20))
        
        # Crear tabla para las firmas
        firma_data = [
            [Paragraph('_'*50, normal_style), Paragraph('_'*50, normal_style)],
            [Paragraph('<b>Firma y Sello del Propietario</b>', normal_style), 
             Paragraph('<b>Firma y Sello del Vacunador</b>', normal_style)],
            [Paragraph(registro['nombre_propietario'], normal_style),
             Paragraph(registro['nombre_vacunador'], normal_style)],
            [Paragraph('C.I.: ________________', normal_style),
             Paragraph('C.I.: ________________', normal_style)]
        ]
        
        firma_table = Table(firma_data, colWidths=[doc.width/2.0]*2)
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 1), (-1, 1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
        ]))
        
        elements.append(firma_table)
        
        # Nota al pie
        elements.append(Spacer(1, 20))
        note_style = ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            alignment=1
        )
        elements.append(Paragraph("Este certificado es un documento oficial. La falsificación o alteración de este documento está sujeta a sanciones legales.", note_style))
        
        # Generar PDF con el fondo decorativo
        doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header)
        
        # Preparar descarga
        buffer.seek(0)
        return send_file(
            buffer,
            download_name=f'certificado_aftosa_{registro["numero_certificado"]}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
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
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
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
        
        # Crear el PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#005B96'),
            spaceAfter=30,
            alignment=1
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#005B96'),
            spaceAfter=20,
            alignment=1
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#005B96'),
            spaceAfter=15
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=10
        )
        
        # Elementos del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph('CERTIFICADO DE VACUNACIÓN CONTRA CARBUNCO', title_style))
        elements.append(Spacer(1, 20))
        
        # Información del registro
        data = [
            ['Fecha de Aplicación:', registro['fecha_registro'].strftime('%d/%m/%Y')],
            ['Producto:', registro.get('nombre_producto', registro.get('producto', 'No especificado'))],
            ['Lote:', registro['lote']],
            ['Vacunador:', registro['vacunador']],
            ['Próxima Aplicación:', registro['proxima_aplicacion'].strftime('%d/%m/%Y')]
        ]
        
        # Crear tabla con la información
        info_table = Table(data, colWidths=[doc.width/3.0, doc.width/1.5])
        common_style = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]
        
        info_table.setStyle(TableStyle(common_style))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Lista de animales
        elements.append(Paragraph('REGISTRO DE ANIMALES VACUNADOS', section_style))
        
        # Encabezados y datos de animales
        headers = [[
            Paragraph('<b>N° Arete</b>', normal_style),
            Paragraph('<b>Nombre</b>', normal_style),
            Paragraph('<b>Raza</b>', normal_style),
            Paragraph('<b>Sexo</b>', normal_style)
        ]]
        
        animal_data = []
        for animal in animales:
            animal_data.append([
                Paragraph(str(animal['numero_arete']), normal_style),
                Paragraph(str(animal['nombre']), normal_style),
                Paragraph(str(animal['raza']), normal_style),
                Paragraph(str(animal['sexo']), normal_style)
            ])
        
        animals_table = Table(headers + animal_data, colWidths=[doc.width/4.0]*4)
        animals_table.setStyle(TableStyle(
            common_style + [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005B96')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]
        ))
        elements.append(animals_table)
        
        # Espacio para firmas
        elements.append(Spacer(1, 30))
        
        # Tabla de firmas
        firma_style = ParagraphStyle(
            'Firma',
            parent=normal_style,
            fontSize=10,
            alignment=1
        )
        firma_data = [
            [Paragraph('_'*20, firma_style), Paragraph('_'*20, firma_style)],
            [Paragraph('<b>Firma y Sello del Propietario</b>', firma_style),
             Paragraph('<b>Firma y Sello del Vacunador</b>', firma_style)],
            [Paragraph('_________________', firma_style),
             Paragraph(registro['vacunador'], firma_style)],
            [Paragraph('C.I.: ____________', firma_style),
             Paragraph('C.I.: ____________', firma_style)]
        ]
        
        firma_table = Table(firma_data, colWidths=[doc.width/2.0]*2)
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 1), (-1, 1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
        ]))
        elements.append(firma_table)
        
        # Nota al pie
        elements.append(Spacer(1, 20))
        note_style = ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            alignment=1
        )
        elements.append(Paragraph('Este certificado es un documento oficial. La falsificación o alteración de este documento está sujeta a sanciones legales.', note_style))
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar descarga
        buffer.seek(0)
        return send_file(
            buffer,
            download_name=f'certificado_carbunco_{registro_id}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        app.logger.error(f'Error al generar certificado PDF de carbunco: {str(e)}')
        app.logger.error('Traceback completo:', exc_info=True)
        flash(f'Error al generar el certificado PDF: {str(e)}', 'error')
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
        cursor = conn.cursor(dictionary=True)

        # Obtener registros de leche agrupados por fecha y animal
        cursor.execute('''
            SELECT 
                animal_id, 
                fecha,
                MAX(CASE WHEN turno = 'Mañana' THEN cantidad ELSE 0 END) as cantidad_manana,
                MAX(CASE WHEN turno = 'Tarde' THEN cantidad ELSE 0 END) as cantidad_tarde,
                MAX(calidad) as calidad,
                GROUP_CONCAT(DISTINCT observaciones SEPARATOR '; ') as observaciones
            FROM registro_leche
            GROUP BY animal_id, fecha
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
        cursor.execute('SELECT id, nombre, numero_arete FROM animales WHERE estado = "Activo"')
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
