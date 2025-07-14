# Sistema de Gestión Ganadera

Sistema integral para la gestión de ganado que permite el registro, seguimiento y control de animales, vacunaciones, tratamientos, producción de leche y más.

## Requisitos Previos
- Python 3.8+
- MySQL 5.7+
- pip (Gestor de paquetes de Python)

## Características Principales

### Gestión de Animales
- Registro completo de animales con datos detallados
- Seguimiento de historial médico y productivo
- Generación de códigos QR para identificación
- Carga y gestión de imágenes

### Módulos de Vacunación
- Registro de vacunaciones (Carbunco, Vitaminización, Desparasitación, Fiebre Aftosa)
- Programación de próximas aplicaciones
- Sistema de alertas para vacunaciones próximas

### Gestión Reproductiva
- Registro y seguimiento de gestaciones
- Control de partos
- Alertas de fechas próximas

### Producción de Leche
- Registro diario de producción (mañana/tarde)
- Estadísticas de producción
- Gráficos de rendimiento

### Dashboard
- Resumen estadístico del hato ganadero
- Alertas de próximas vacunaciones y eventos
- Acceso rápido a funciones principales

### Seguridad
- Sistema de autenticación de usuarios
- Protección de rutas
- Auditoría de acciones

## Configuración de Base de Datos
1. Instalar MySQL
2. Crear una base de datos llamada `sistema_ganadero`
3. Configurar las credenciales en `src/database.py`
4. La estructura de la base de datos se creará automáticamente al iniciar la aplicación

## Instalación

1. Clonar el repositorio
   ```bash
   git clone https://github.com/usuario/SistemaGanadero.git
   cd SistemaGanadero
   ```

2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar credenciales de base de datos en `src/database.py`

5. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

## Tecnologías Utilizadas
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Base de Datos**: MySQL
- **Reportes**: ReportLab
- **Gráficos**: Chart.js
- **Programación de tareas**: APScheduler

## Estructura del Proyecto
- `app.py`: Punto de entrada principal
- `src/`: Módulos y componentes del sistema
- `templates/`: Plantillas HTML
- `static/`: Archivos estáticos (CSS, JS, imágenes)
- `uploads/`: Directorio para almacenar imágenes subidas

## Contribución
Si deseas contribuir al proyecto, por favor:
1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un nuevo Pull Request

## Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.
- Flask
- MySQL
- HTML5
- CSS3
- JavaScript
