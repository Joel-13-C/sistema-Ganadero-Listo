from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from datetime import datetime
import psycopg2
import psycopg2.extras
import os

# Crear el blueprint para registro_leche
registro_leche_bp = Blueprint('registro_leche', __name__)

# Función para obtener conexión a la base de datos
def get_db_connection():
    try:
        db_url = "postgresql://ganadero_anwt_user:rOsqRSS6jlrJ6UiEQzj7HM2G5CAb0eBb@dpg-d1tg58idbo4c73dieh30-a.oregon-postgres.render.com/ganadero_anwt"
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Decorador para requerir inicio de sesión
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta para mostrar la página principal de registro de leche
@registro_leche_bp.route('/')
@login_required
def vista_registro_leche():
    try:
        conn = get_db_connection()
        if not conn:
            flash('Error al conectar con la base de datos', 'danger')
            return render_template('registro_leche.html', registros=[], animales=[])
            
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        animal_id = request.args.get('animal')
        
        # Construir consulta base
        query = """
            SELECT rl.*, a.nombre as nombre_animal, u.username as nombre_usuario
            FROM registro_leche rl
            JOIN animales a ON rl.animal_id = a.id
            JOIN usuarios u ON rl.usuario_id = u.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(rl.fecha) = %s"
            params.append(fecha)
        if animal_id:
            query += " AND rl.animal_id = %s"
            params.append(animal_id)
            
        query += " ORDER BY rl.fecha DESC"
        
        cursor.execute(query, params)
        registros = cursor.fetchall()
        
        # Obtener lista de animales para el selector
        cursor.execute("""
            SELECT id, nombre, numero_arete 
            FROM animales 
            WHERE sexo = 'Hembra'
            AND condicion IN ('Vaca', 'Vacona')
            ORDER BY nombre
        """)
        animales = cursor.fetchall()
        
        return render_template('registro_leche.html', registros=registros, animales=animales)
    
    except Exception as e:
        print(f"Error en vista_registro_leche: {str(e)}")
        flash(f'Error al cargar los registros: {str(e)}', 'danger')
        return render_template('registro_leche.html', registros=[], animales=[])
    
    finally:
        if conn:
            cursor.close()
            conn.close()

# Ruta para agregar un nuevo registro de leche
@registro_leche_bp.route('/agregar', methods=['POST'])
@login_required
def nuevo_registro_leche():
    conn = None
    cursor = None
    try:
        # Obtener datos del formulario
        animal_id = request.form['animal_id']
        fecha = request.form['fecha']
        cantidad_manana = request.form.get('cantidad_manana', 0)
        cantidad_tarde = request.form.get('cantidad_tarde', 0)
        calidad = request.form.get('calidad', 'A')
        observaciones = request.form.get('observaciones', '')
        
        # Validar datos
        if not animal_id or not fecha:
            flash('Todos los campos obligatorios deben ser completados', 'danger')
            return redirect(url_for('registro_leche.vista_registro_leche'))
        
        # Convertir cantidades a decimal
        try:
            cantidad_manana = float(cantidad_manana)
            cantidad_tarde = float(cantidad_tarde)
            cantidad_total = cantidad_manana + cantidad_tarde
        except ValueError:
            flash('Las cantidades deben ser números válidos', 'danger')
            return redirect(url_for('registro_leche.vista_registro_leche'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe un registro para este animal y fecha
        cursor.execute("""
            SELECT id FROM registro_leche 
            WHERE animal_id = %s AND fecha = %s
        """, (animal_id, fecha))
        
        existing = cursor.fetchone()
        
        if existing:
            flash(f'Ya existe un registro para este animal en la fecha {fecha}', 'warning')
            return redirect(url_for('registro_leche.vista_registro_leche'))
        
        # Insertar nuevo registro
        cursor.execute("""
            INSERT INTO registro_leche 
            (animal_id, usuario_id, fecha, cantidad_manana, cantidad_tarde, total_dia, observaciones) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (animal_id, session['usuario_id'], fecha, cantidad_manana, cantidad_tarde, cantidad_total, observaciones))
        
        conn.commit()
        flash('Registro de producción de leche agregado exitosamente', 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error al agregar el registro: {str(e)}', 'danger')
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return redirect(url_for('registro_leche.vista_registro_leche'))

# Ruta para editar un registro existente
@registro_leche_bp.route('/editar/<int:registro_id>', methods=['POST'])
@login_required
def actualizar_registro_leche(registro_id):
    conn = None
    cursor = None
    try:
        # Obtener datos del formulario
        animal_id = request.form['animal_id']
        fecha = request.form['fecha']
        cantidad_manana = request.form.get('cantidad_manana', 0)
        cantidad_tarde = request.form.get('cantidad_tarde', 0)
        calidad = request.form.get('calidad', 'A')
        observaciones = request.form.get('observaciones', '')
        
        # Convertir cantidades a decimal
        try:
            cantidad_manana = float(cantidad_manana)
            cantidad_tarde = float(cantidad_tarde)
            cantidad_total = cantidad_manana + cantidad_tarde
        except ValueError:
            flash('Las cantidades deben ser números válidos', 'danger')
            return redirect(url_for('registro_leche.vista_registro_leche'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Actualizar registro
        cursor.execute("""
            UPDATE registro_leche 
            SET animal_id = %s, fecha = %s, cantidad_manana = %s, cantidad_tarde = %s, 
                total_dia = %s, observaciones = %s
            WHERE id = %s
        """, (animal_id, fecha, cantidad_manana, cantidad_tarde, cantidad_total, observaciones, registro_id))
        
        conn.commit()
        flash('Registro actualizado exitosamente', 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error al actualizar el registro: {str(e)}', 'danger')
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return redirect(url_for('registro_leche.vista_registro_leche'))

# Ruta para eliminar un registro
@registro_leche_bp.route('/eliminar/<int:registro_id>', methods=['DELETE'])
@login_required
def borrar_registro_leche(registro_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM registro_leche WHERE id = %s", (registro_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Registro eliminado correctamente'})
    
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para obtener un registro específico (para edición)
@registro_leche_bp.route('/obtener/<int:registro_id>')
@login_required
def obtener_registro_leche(registro_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT rl.*, a.nombre as nombre_animal 
            FROM registro_leche rl
            JOIN animales a ON rl.animal_id = a.id
            WHERE rl.id = %s
        """, (registro_id,))
        
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404
        
        # Formatear la fecha para el formulario HTML
        if 'fecha' in registro and registro['fecha']:
            registro['fecha'] = registro['fecha'].strftime('%Y-%m-%d')
        
        # Asegurar que todos los campos necesarios estén presentes
        if 'total_dia' not in registro or registro['total_dia'] is None:
            registro['total_dia'] = 0.0
        
        if 'calidad' not in registro or not registro['calidad']:
            registro['calidad'] = 'A'
            
        if 'turno' not in registro or not registro['turno']:
            registro['turno'] = 'Ambos'
            
        if 'observaciones' not in registro:
            registro['observaciones'] = ''
        
        return jsonify({'success': True, 'registro': registro})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
