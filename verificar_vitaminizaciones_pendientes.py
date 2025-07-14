# Script para verificar las vitaminizaciones pendientes registradas y comprobar el sistema de alarmas
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

# Verificar vitaminizaciones en la base de datos
def verificar_vitaminizaciones_bd():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Verificar estructura de la tabla
        print("\n=== ESTRUCTURA DE TABLA DE VITAMINIZACIONES ===")
        cursor.execute("DESCRIBE vitaminizacion")
        estructura = cursor.fetchall()
        for campo in estructura:
            print(f"{campo['Field']} - {campo['Type']} - {campo['Null']}")
        
        # 2. Contar registros
        cursor.execute("SELECT COUNT(*) as total FROM vitaminizacion")
        total = cursor.fetchone()['total']
        print(f"\n=== TOTAL DE VITAMINIZACIONES: {total} ===")
        
        # 3. Mostrar próximas vitaminizaciones
        print("\n=== PRÓXIMAS VITAMINIZACIONES (30 días) ===")
        limite = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        hoy = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT v.*, GROUP_CONCAT(a.nombre) as nombres_animales
            FROM vitaminizacion v
            LEFT JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id
            LEFT JOIN animales a ON va.animal_id = a.id
            WHERE v.proxima_aplicacion BETWEEN %s AND %s
            GROUP BY v.id
            ORDER BY v.proxima_aplicacion
        """
        
        cursor.execute(query, (hoy, limite))
        proximas = cursor.fetchall()
        
        if proximas:
            for v in proximas:
                dias_restantes = (v['proxima_aplicacion'] - datetime.now().date()).days
                animales = v['nombres_animales'] or "Sin animales asignados"
                print(f"ID: {v['id']}, Producto: {v['producto']}, Fecha: {v['proxima_aplicacion']}, Días restantes: {dias_restantes}")
                print(f"  Animales: {animales}")
                print("  ----------------------------------------")
        else:
            print("  No hay vitaminizaciones programadas para los próximos 30 días.")
        
        return True
    except Exception as e:
        logger.error(f"Error al verificar vitaminizaciones: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Revisando el código en SistemaAlarmas para vitaminizaciones
def verificar_sistema_alarmas_vitaminizaciones():
    print("\n=== VERIFICANDO CÓDIGO DEL SISTEMA DE ALARMAS PARA VITAMINIZACIONES ===")
    try:
        # Buscar método específico en SistemaAlarmas
        alarmas = SistemaAlarmas(get_db)
        
        # Comprobar si existe el método para verificar vitaminizaciones
        if hasattr(alarmas, 'verificar_vitaminizaciones_pendientes'):
            print("  ✓ El método 'verificar_vitaminizaciones_pendientes' existe en el sistema de alarmas")
            
            # Intentar verificar vitaminizaciones
            print("\n=== EJECUTANDO VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES ===")
            notificaciones = alarmas.verificar_vitaminizaciones_pendientes()
            print(f"\n  Resultado: Se enviaron {notificaciones} notificaciones")
            
            return True
        else:
            print("  ✗ El método 'verificar_vitaminizaciones_pendientes' NO existe en el sistema de alarmas")
            
            # Verificar si hay otros métodos que puedan estar manejando las vitaminizaciones
            metodos = [m for m in dir(alarmas) if callable(getattr(alarmas, m)) and not m.startswith('_')]
            print("\n  Métodos disponibles en SistemaAlarmas que podrían manejar vitaminizaciones:")
            vitaminizacion_metodos = [m for m in metodos if 'vitaminizacion' in m.lower() or 'vitamina' in m.lower()]
            
            if vitaminizacion_metodos:
                for m in vitaminizacion_metodos:
                    print(f"    - {m}")
            else:
                print("    - No se encontraron métodos relacionados con vitaminizaciones")
            
            return False
    except Exception as e:
        logger.error(f"Error al verificar sistema de alarmas para vitaminizaciones: {e}")
        return False

# Verificar la tabla de configuración de alarmas para vitaminizaciones
def verificar_config_alarmas_vitaminizaciones():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        print("\n=== VERIFICANDO CONFIGURACIÓN DE ALARMAS PARA VITAMINIZACIONES ===")
        
        # Verificar si hay configuraciones específicas para vitaminizaciones
        cursor.execute("SELECT * FROM config_alarmas WHERE tipo = 'vitaminizacion' AND activo = TRUE")
        config = cursor.fetchall()
        
        if config:
            print(f"  Configuraciones activas encontradas: {len(config)}")
            for c in config:
                print(f"  Usuario ID: {c['usuario_id']}, Email: {c['email']}, Días anticipación: {c['dias_anticipacion']}")
        else:
            print("  No hay configuraciones activas para alarmas de vitaminizaciones.")
            print("  El sistema usaría la configuración predeterminada si estuviera implementado.")
        
        # Verificar si hay alarmas enviadas de tipo vitaminizacion
        cursor.execute("""
            SELECT * FROM alarmas_enviadas 
            WHERE tipo = 'vitaminizacion'
            ORDER BY fecha_envio DESC
            LIMIT 5
        """)
        
        alarmas_enviadas = cursor.fetchall()
        if alarmas_enviadas:
            print(f"\n  Últimas {len(alarmas_enviadas)} alarmas enviadas para vitaminizaciones:")
            for a in alarmas_enviadas:
                print(f"  ID: {a['id']}, Fecha: {a['fecha_envio']}, Email: {a['email']}")
                print(f"  Asunto: {a['asunto']}")
                print("  ------------------------------------")
        else:
            print("\n  No se encontraron registros de alarmas enviadas para vitaminizaciones.")
        
        return True
    except Exception as e:
        logger.error(f"Error al verificar configuración de alarmas para vitaminizaciones: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Función principal
if __name__ == "__main__":
    print("=== VERIFICACIÓN DEL SISTEMA DE ALARMAS DE VITAMINIZACIONES ===")
    print("Fecha actual:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Verificar datos en la BD
    verificar_vitaminizaciones_bd()
    
    # Verificar configuración de alarmas
    verificar_config_alarmas_vitaminizaciones()
    
    # Verificar código del sistema de alarmas
    verificar_sistema_alarmas_vitaminizaciones()
