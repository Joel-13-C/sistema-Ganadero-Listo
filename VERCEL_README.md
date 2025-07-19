# Configuración para Vercel

Este proyecto ha sido configurado para funcionar correctamente en Vercel con las siguientes mejoras:

## Cambios Realizados

### 1. Configuración de Sesiones
- **Problema**: Vercel es un entorno serverless donde las sesiones no se mantienen entre requests
- **Solución**: Implementado sistema híbrido de autenticación (sesiones + JWT)

### 2. Archivos Modificados

#### `vercel_app.py`
- Configuración específica para Vercel
- Manejo de sesiones con Flask-Session
- Configuración de cookies seguras

#### `app.py`
- Clave secreta fija (en lugar de `os.urandom()`)
- Sistema de autenticación JWT
- Decorador `login_required` híbrido

#### `src/jwt_auth.py` (NUEVO)
- Sistema de autenticación JWT
- Tokens con expiración de 24 horas
- Compatibilidad con sesiones existentes

#### `vercel.json`
- Variables de entorno configuradas
- Headers para evitar cache
- Configuración de funciones serverless

#### `requirements.txt`
- Flask-Session para manejo de sesiones
- PyJWT para tokens de autenticación

## Variables de Entorno

Las siguientes variables están configuradas en `vercel.json`:

```json
{
  "SECRET_KEY": "tu_clave_secreta_fija_aqui_123456789",
  "JWT_SECRET_KEY": "tu_clave_jwt_secreta_aqui_123456789",
  "SESSION_TYPE": "filesystem",
  "SESSION_FILE_DIR": "/tmp"
}
```

## Cómo Funciona

### Autenticación Híbrida
1. **Login**: Se genera tanto una sesión como un token JWT
2. **Protección de rutas**: El decorador `@login_required` verifica:
   - Primero: Sesión existente
   - Segundo: Token JWT en headers
   - Si no hay ninguno: Redirige al login

### Compatibilidad
- Mantiene compatibilidad con el código existente
- Funciona tanto en desarrollo local como en Vercel
- No requiere cambios en los templates

## Despliegue

1. **Instalar Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Desplegar**:
   ```bash
   vercel --prod
   ```

3. **Verificar configuración**:
   ```bash
   python test_vercel.py
   ```

## Solución de Problemas

### Si las sesiones no se mantienen:
1. Verificar que las variables de entorno estén configuradas
2. Asegurar que `SECRET_KEY` sea la misma en todos los entornos
3. Verificar que `SESSION_FILE_DIR` apunte a `/tmp` en Vercel

### Si el login no funciona:
1. Verificar la conexión a la base de datos
2. Revisar los logs en Vercel Dashboard
3. Probar con el script de prueba: `python test_vercel.py`

## Notas Importantes

- **Seguridad**: En producción, cambiar las claves secretas por variables de entorno reales
- **HTTPS**: Cambiar `SESSION_COOKIE_SECURE` a `True` cuando se use HTTPS
- **Base de datos**: Asegurar que la base de datos PostgreSQL esté accesible desde Vercel

## Próximos Pasos

1. Desplegar en Vercel
2. Probar el login y navegación
3. Verificar que las sesiones se mantengan
4. Configurar variables de entorno reales en Vercel Dashboard 