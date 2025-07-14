def add_equipos_function():
    try:
        # Función equipos segura para añadir al final del archivo
        equipos_function = """
# Función equipos restaurada de manera segura
@app.route('/equipos')
@login_required
def equipos():
    # Versión segura que no accede a la base de datos
    flash('El módulo de equipos está temporalmente deshabilitado por mantenimiento.', 'warning')
    return render_template('mantenimiento.html', 
                          titulo="Módulo en Mantenimiento", 
                          mensaje="El módulo de gestión de equipos está temporalmente deshabilitado por mantenimiento.")
"""
        
        # Añadir la función al final del archivo, justo antes de if __name__ == '__main__'
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.readlines()
        
        # Buscar la línea if __name__ == '__main__'
        main_line_index = -1
        for i, line in enumerate(content):
            if "if __name__ == '__main__':" in line:
                main_line_index = i
                break
        
        if main_line_index > 0:
            # Insertar la función justo antes de if __name__ == '__main__'
            content.insert(main_line_index, equipos_function)
            
            # Escribir el contenido actualizado
            with open('app.py', 'w', encoding='utf-8') as file:
                file.writelines(content)
            
            print("Función equipos añadida exitosamente al archivo app.py")
        else:
            print("No se pudo encontrar 'if __name__ == '__main__'' en el archivo")
        
        # Crear la plantilla de mantenimiento
        with open('templates/mantenimiento.html', 'w', encoding='utf-8') as file:
            file.write("""{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <div class="card">
        <div class="card-header bg-warning text-white">
            <h2><i class="fas fa-tools"></i> {{ titulo }}</h2>
        </div>
        <div class="card-body text-center">
            <div class="mb-4">
                <i class="fas fa-cogs" style="font-size: 5rem; color: #ffc107;"></i>
            </div>
            <h3>{{ mensaje }}</h3>
            <p class="lead">Estamos trabajando para solucionar los problemas y mejorar la funcionalidad.</p>
            <p>Por favor, intente acceder más tarde o contacte al administrador del sistema si necesita asistencia inmediata.</p>
            <a href="{{ url_for('dashboard') }}" class="btn btn-primary mt-3">
                <i class="fas fa-home"></i> Volver al Inicio
            </a>
        </div>
    </div>
</div>
{% endblock %}""")
        print("Plantilla de mantenimiento creada exitosamente")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_equipos_function()
