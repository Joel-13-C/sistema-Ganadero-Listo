# Script para verificar las desparasitaciones pendientes registradas y comprobar el sistema de alarmas
from src.database import get_db_connection
from src.alarmas import SistemaAlarmas
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Función para obtener conexión a la base de datos
def get_db():
    return get_db_connection()

# Verificar desparasitaciones en la base de datos
def verificar_desparasitaciones_bd():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Verificar estructura de la tabla
        print("\n=== ESTRUCTURA DE TABLA DE DESPARASITACIONES ===")
        cursor.execute("DESCRIBE desparasitacion")
        estructura = cursor.fetchall()
        for campo in estructura:
            print(f"{campo['Field']} - {campo['Type']} - {campo['Null']}")
        
        # 2. Contar registros
        cursor.execute("SELECT COUNT(*) as total FROM desparasitacion")
        total = cursor.fetchone()['total']
        print(f"\n=== TOTAL DE DESPARASITACIONES: {total} ===")
        
        # 3. Mostrar próximas desparasitaciones
        print("\n=== PRÓXIMAS DESPARASITACIONES (30 días) ===")
        limite = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        hoy = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT d.*, GROUP_CONCAT(a.nombre) as nombres_animales
            FROM desparasitacion d
            LEFT JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id
            LEFT JOIN animales a ON da.animal_id = a.id
            WHERE d.proxima_aplicacion BETWEEN %s AND %s
            GROUP BY d.id
            ORDER BY d.proxima_aplicacion
        """
        
        cursor.execute(query, (hoy, limite))
        proximas = cursor.fetchall()
        
        if proximas:
            for d in proximas:
                dias_restantes = (d['proxima_aplicacion'] - datetime.now().date()).days
                animales = d['nombres_animales'] or "Sin animales asignados"
                print(f"ID: {d['id']}, Producto: {d['producto']}, Fecha: {d['proxima_aplicacion']}, Días restantes: {dias_restantes}")
                print(f"  Animales: {animales}")
                print("  ----------------------------------------")
        else:
            print("  No hay desparasitaciones programadas para los próximos 30 días.")
        
        return True
    except Exception as e:
        logger.error(f"Error al verificar desparasitaciones: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Probar el sistema de alarmas
def probar_sistema_alarmas():
    print("\n=== PRUEBA DEL SISTEMA DE ALARMAS PARA DESPARASITACIONES ===")
    try:
        # Inicializar el sistema de alarmas con la conexión a la BD
        alarmas = SistemaAlarmas(get_db)
        
        # Verificar configuración de alarmas
        print("\n1. Verificando configuración de alarmas de desparasitación")
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM config_alarmas WHERE tipo = 'desparasitacion' AND activo = TRUE")
        config = cursor.fetchall()
        
        if config:
            print(f"  Configuraciones activas encontradas: {len(config)}")
            for c in config:
                print(f"  Usuario ID: {c['usuario_id']}, Email: {c['email']}, Días anticipación: {c['dias_anticipacion']}")
        else:
            print("  No hay configuraciones activas para alarmas de desparasitación.")
            print("  El sistema usará la configuración predeterminada.")
        
        # Ejecutar la función de verificación de desparasitaciones pendientes
        print("\n2. Ejecutando verificación de desparasitaciones pendientes")
        notificaciones = alarmas.verificar_desparasitaciones_pendientes()
        
        print(f"\n3. Resultado: Se enviaron {notificaciones} notificaciones")
        
        # Verificar registro de alarmas enviadas
        print("\n4. Verificando registro de alarmas enviadas")
        cursor.execute("""
            SELECT * FROM alarmas_enviadas 
            WHERE tipo = 'desparasitacion'
            ORDER BY fecha_envio DESC
            LIMIT 5
        """)
        
        alarmas_enviadas = cursor.fetchall()
        if alarmas_enviadas:
            print(f"  Últimas {len(alarmas_enviadas)} alarmas enviadas:")
            for a in alarmas_enviadas:
                print(f"  ID: {a['id']}, Fecha: {a['fecha_envio']}, Email: {a['email']}")
                print(f"  Asunto: {a['asunto']}")
                print("  ------------------------------------")
        else:
            print("  No se encontraron registros de alarmas enviadas para desparasitaciones.")
        
        return notificaciones
    except Exception as e:
        logger.error(f"Error al probar el sistema de alarmas: {e}")
        return -1
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== VERIFICACIÓN DEL SISTEMA DE ALARMAS DE DESPARASITACIONES ===")
    print("Fecha actual:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Verificar datos en la BD
    verificar_desparasitaciones_bd()
    
    # Probar sistema de alarmas
    probar_sistema_alarmas()
