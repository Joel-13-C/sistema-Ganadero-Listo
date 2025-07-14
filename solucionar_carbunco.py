# Script para solucionar definitivamente el problema de registro de carbunco
import sys
import os
sys.path.append(os.getcwd())

from src.database import get_db_connection

def solucionar_problema_carbunco():
    print("\n====== SOLUCIONANDO PROBLEMA DE REGISTRO DE CARBUNCO ======\n")
    
    try:
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar si existe y arreglar la tabla carbunco
        print("Verificando tabla carbunco...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sistema_ganadero' 
            AND table_name = 'carbunco'
        """)
        existe_tabla_carbunco = cursor.fetchone()[0] > 0
        
        if not existe_tabla_carbunco:
            print("La tabla carbunco no existe. Creándola...")
            cursor.execute("""
                CREATE TABLE carbunco (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fecha_registro DATE NOT NULL,
                    producto VARCHAR(100) NOT NULL,
                    lote VARCHAR(50),
                    vacunador VARCHAR(100),
                    aplicacion_general BOOLEAN DEFAULT TRUE,
                    proxima_aplicacion DATE,
                    usuario_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Tabla carbunco creada correctamente")
        else:
            # Verificar estructura de la tabla carbunco
            print("La tabla carbunco ya existe. Verificando estructura...")
            cursor.execute("DESCRIBE carbunco")
            columnas = [col[0] for col in cursor.fetchall()]
            print(f"Columnas actuales: {columnas}")
            
            # Verificar si tiene la columna usuario_id
            if 'usuario_id' not in columnas:
                print("La columna usuario_id no existe en carbunco. Añadiéndola...")
                cursor.execute("""
                    ALTER TABLE carbunco
                    ADD COLUMN usuario_id INT DEFAULT 1
                """)
                conn.commit()
                print("Columna usuario_id añadida a tabla carbunco")
        
        # 2. Verificar si existe y arreglar la tabla carbunco_animal
        print("\nVerificando tabla carbunco_animal...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sistema_ganadero' 
            AND table_name = 'carbunco_animal'
        """)
        existe_tabla_rel = cursor.fetchone()[0] > 0
        
        if not existe_tabla_rel:
            print("La tabla carbunco_animal no existe. Creándola...")
            cursor.execute("""
                CREATE TABLE carbunco_animal (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    carbunco_id INT NOT NULL,
                    animal_id INT NOT NULL,
                    FOREIGN KEY (carbunco_id) REFERENCES carbunco(id),
                    FOREIGN KEY (animal_id) REFERENCES animales(id)
                )
            """)
            conn.commit()
            print("Tabla carbunco_animal creada correctamente")
        else:
            print("La tabla carbunco_animal ya existe")
        
        # 3. Examinar la función registrar_carbunco en el archivo app.py
        app_path = os.path.join(os.getcwd(), 'app.py')
        
        with open(app_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Buscar la función registrar_carbunco
        registrar_carbunco_start = content.find("def registrar_carbunco()")
        if registrar_carbunco_start != -1:
            registrar_carbunco_end = content.find("def ", registrar_carbunco_start + 10)
            if registrar_carbunco_end == -1:  # Si es la última función del archivo
                registrar_carbunco_end = content.find("if __name__ ==", registrar_carbunco_start)
            
            registro_function = content[registrar_carbunco_start:registrar_carbunco_end]
            print("\nAnalizando función registrar_carbunco...")
            
            # Buscar la línea INSERT INTO carbunco
            if "INSERT INTO carbunco" in registro_function:
                print("Se encontró INSERT INTO carbunco en la función")
                if "usuario_id" in registro_function:
                    print("La función está intentando insertar usuario_id")
            
            # Buscar posibles referencias a otras tablas
            if "INSERT INTO vacuna" in registro_function:
                print("¡ATENCIÓN! La función está intentando insertar en la tabla vacuna")
        
        # 4. Crear una función corregida para registrar carbunco
        fix_script_path = os.path.join(os.getcwd(), 'fix_registrar_carbunco.py')
        with open(fix_script_path, 'w', encoding='utf-8') as file:
            file.write("""# Script para corregir la función registrar_carbunco
import os
import re

def corregir_funcion_registrar_carbunco():
    app_path = os.path.join(os.getcwd(), 'app.py')
    
    with open(app_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar la función registrar_carbunco
    start_idx = content.find("def registrar_carbunco()")
    if start_idx == -1:
        print("No se encontró la función registrar_carbunco")
        return
    
    # Encontrar el final de la función
    end_idx = content.find("def ", start_idx + 10)
    if end_idx == -1:  # Si es la última función
        end_idx = content.find("if __name__ ==", start_idx)
    
    # Extraer la función completa
    original_function = content[start_idx:end_idx]
    
    # Crear la versión corregida de la función
    corrected_function = '''@app.route('/registrar_carbunco', methods=['POST'])
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
        
        cursor.execute("""
            INSERT INTO carbunco 
            (fecha_registro, producto, lote, vacunador, aplicacion_general, proxima_aplicacion, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fecha_registro, producto, lote, vacunador, tipo_aplicacion == 'general', proxima_aplicacion, session.get('usuario_id', 1)))
        
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
'''
    
    # Reemplazar la función original con la corregida
    new_content = content.replace(original_function, corrected_function)
    
    # Guardar el archivo modificado
    with open(app_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("Función registrar_carbunco corregida con éxito")

if __name__ == "__main__":
    corregir_funcion_registrar_carbunco()
""")
        print("\nScript de corrección creado: fix_registrar_carbunco.py")
        
        print("\n====== SOLUCIÓN DE PROBLEMA DE CARBUNCO FINALIZADA ======\n")
        print("Para completar la solución, ejecuta el siguiente comando:")
        print("python fix_registrar_carbunco.py")
        print("Y luego reinicia el servidor web para aplicar los cambios")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    solucionar_problema_carbunco()
