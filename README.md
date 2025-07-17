# Sistema de Gestión Ganadera

Sistema integral para la gestión de ganado que permite el registro, seguimiento y control de animales, vacunaciones, tratamientos, producción de leche y más.

## Requisitos Previos
- Python 3.8+
- MySQL 5.7+
- pip (Gestor de paquetes de Python)

## Configuración

### Base de Datos
1. Instalar MySQL
2. Crear una base de datos llamada `sistema_ganadero2`
3. Configurar MySQL con las siguientes credenciales:
   - Usuario: root
   - Contraseña: Cappa100..$$
   - Host: localhost
   - Base de datos: sistema_ganadero2
4. Ejecutar el script `bd.sql` para crear las tablas necesarias

### Configuración de Correo (Para notificaciones)
El sistema está configurado para usar Gmail con las siguientes credenciales:
```python
email_config = {
    'smtp_server': 'smtp.gmail.com',
    'port': 587,
    'username': 'p2pacademy.oficial@gmail.com',
    'password': 'dtnf whvj oycf nhbb',
    'from_email': 'p2pacademy.oficial@gmail.com'
}
```

### Instalación

1. Clonar el repositorio:
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

4. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

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

## Estructura del Proyecto
- `app.py`: Punto de entrada principal
- `src/`: Módulos y componentes del sistema
  - `database.py`: Conexión y operaciones de base de datos
  - `alarmas.py`: Sistema de alertas y notificaciones
  - `auditoria.py`: Registro de actividades
  - `routes/`: Rutas y controladores
- `templates/`: Plantillas HTML
- `static/`: Archivos estáticos (CSS, JS, imágenes)
  - `uploads/`: Directorio para almacenar imágenes subidas
    - `animales/`: Fotos de animales
    - `perfiles/`: Fotos de perfil
  - `comprobantes/`: Comprobantes y documentos

## Tecnologías Utilizadas
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Base de Datos**: MySQL
- **Reportes**: ReportLab
- **Gráficos**: Chart.js
- **Programación de tareas**: APScheduler
- **Almacenamiento de imágenes**: Cloudinary

## Contribución
Si deseas contribuir al proyecto, por favor:
1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un nuevo Pull Request

## Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.
