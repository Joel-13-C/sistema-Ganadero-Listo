import jwt
import datetime
from functools import wraps
from flask import request, jsonify, session
import os

# Clave secreta para JWT (en producción debería ser una variable de entorno)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tu_clave_jwt_secreta_aqui_123456789')

def create_token(user_id, username):
    """Crear un token JWT para el usuario"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verificar un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def jwt_login_required(f):
    """Decorador para proteger rutas con JWT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primero intentar con sesión (para compatibilidad)
        if 'username' in session:
            return f(*args, **kwargs)
        
        # Si no hay sesión, intentar con JWT
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
                payload = verify_token(token)
                if payload:
                    # Establecer datos en sesión para compatibilidad
                    session['username'] = payload['username']
                    session['usuario_id'] = payload['user_id']
                    return f(*args, **kwargs)
            except (IndexError, KeyError):
                pass
        
        # Si no hay token válido, redirigir al login
        return redirect('/login')
    
    return decorated_function

def get_current_user():
    """Obtener el usuario actual desde sesión o JWT"""
    if 'username' in session:
        return {
            'username': session['username'],
            'user_id': session.get('usuario_id')
        }
    
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                return {
                    'username': payload['username'],
                    'user_id': payload['user_id']
                }
        except (IndexError, KeyError):
            pass
    
    return None 