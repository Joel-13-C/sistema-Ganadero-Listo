import mysql.connector
import os
import shutil

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'sistema_ganadero'
}

def copiar_imagenes_faltantes():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todas las rutas de imágenes
        cursor.execute("SELECT id, numero_arete, nombre, foto_path FROM animales")
        animales = cursor.fetchall()
        
        print(f"Total de animales en la base de datos: {len(animales)}")
        contador = 0
        
        # Asegurarse de que existe la carpeta uploads/animales
        if not os.path.exists('uploads/animales'):
            os.makedirs('uploads/animales', exist_ok=True)
            print("Carpeta 'uploads/animales' creada")
        
        for animal in animales:
            animal_id = animal['id']
            ruta_actual = animal['foto_path']
            
            if not ruta_actual or ruta_actual == 'static/images/upload-image-placeholder.svg':
                continue
                
            # Obtener el nombre del archivo de la ruta
            nombre_archivo = os.path.basename(ruta_actual)
            
            # Rutas de origen y destino
            ruta_origen_static = os.path.join('static/uploads/animales', nombre_archivo)
            ruta_destino_uploads = os.path.join('uploads/animales', nombre_archivo)
            
            # Verificar si el archivo existe en static/uploads/animales
            if os.path.exists(ruta_origen_static):
                # Copiar el archivo a uploads/animales si no existe
                if not os.path.exists(ruta_destino_uploads):
                    shutil.copy2(ruta_origen_static, ruta_destino_uploads)
                    print(f"Copiado: {nombre_archivo} a uploads/animales")
                    contador += 1
        
        print(f"\nSe copiaron {contador} imágenes a la carpeta uploads/animales")
        
        # Ahora vamos a crear un enlace simbólico para que Flask pueda servir archivos desde uploads
        print("\nCreando rutas de acceso para servir archivos desde 'uploads'...")
        
        # Modificar app.py para agregar una ruta para servir archivos desde uploads
        with open('app.py', 'r', encoding='utf-8') as file:
            contenido = file.read()
        
        # Verificar si ya existe la ruta para uploads
        if "@app.route('/uploads/<path:filename>')" not in contenido:
            # Buscar una posición adecuada para insertar el código
            posicion = contenido.find("@app.route('/')")
            if posicion != -1:
                nuevo_codigo = """
# Ruta para servir archivos desde la carpeta uploads
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

"""
                # Insertar el nuevo código antes de la primera ruta
                contenido_modificado = contenido[:posicion] + nuevo_codigo + contenido[posicion:]
                
                # Guardar los cambios
                with open('app.py', 'w', encoding='utf-8') as file:
                    file.write(contenido_modificado)
                
                print("Se agregó una ruta en app.py para servir archivos desde 'uploads'")
            else:
                print("No se pudo encontrar una posición adecuada para insertar el código en app.py")
        else:
            print("La ruta para servir archivos desde 'uploads' ya existe en app.py")
        
        # Modificar la plantilla animales.html para usar la ruta correcta
        with open('templates/animales.html', 'r', encoding='utf-8') as file:
            contenido_html = file.read()
        
        # Reemplazar la forma en que se muestran las imágenes
        if 'src="{{ animal.foto_path }}"' in contenido_html:
            contenido_html_modificado = contenido_html.replace(
                'src="{{ animal.foto_path }}"', 
                'src="{{ animal.foto_path if animal.foto_path.startswith(\'/static/\') or animal.foto_path.startswith(\'static/\') else \'/\' + animal.foto_path }}"'
            )
            
            # Guardar los cambios
            with open('templates/animales.html', 'w', encoding='utf-8') as file:
                file.write(contenido_html_modificado)
            
            print("Se modificó la plantilla animales.html para usar la ruta correcta de las imágenes")
        else:
            print("No se encontró la referencia a las imágenes en animales.html")
        
    except Exception as e:
        print(f"Error al copiar las imágenes faltantes: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    copiar_imagenes_faltantes()
