from app import app
import os
from flask_session import Session

# Configuración específica para Vercel
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta_fija_aqui_123456789')
app.config['SESSION_COOKIE_SECURE'] = False  # Cambiar a True en producción con HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configurar sesiones para Vercel
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp'  # Directorio temporal para Vercel

# Inicializar Flask-Session
Session(app)

# Para Vercel, necesitamos exponer el objeto app
app.debug = False

# Configurar para producción
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)