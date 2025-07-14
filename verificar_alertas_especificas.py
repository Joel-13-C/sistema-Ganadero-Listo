# Script para verificar específicamente las alertas de partos y vacunaciones
import sys
import os
import datetime
from flask import Flask, session

# Añadir ruta actual al path de Python
sys.path.append(os.getcwd())

# Importar los componentes necesarios
from src.alarmas import SistemaAlarmas
from src.database import get_db_connection

def verificar_alertas_especificas():
    print("\n====== VERIFICACIÓN DE ALERTAS ESPECÍFICAS ======\n")
    
    # Crear una aplicación Flask para simular el entorno
    app = Flask(__name__)
    app.secret_key = "sistema_ganadero_secret_key"
    
    # Simular una sesión de usuario
    with app.test_request_context():
        # Establecer datos de sesión (simulando un usuario logueado)
        session['usuario_id'] = 1
        session['username'] = 'admin'
        
        # Inicializar el sistema de alarmas con la función de conexión
        print("Inicializando sistema de alarmas...")
        sistema_alarmas = SistemaAlarmas(get_db_connection)
        
        # 1. Verificar y actualizar datos de parto para asegurar que hay alertas pendientes
        print("\n------ Verificando datos de reproducción ------")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Actualizar fecha de parto próximo para asegurar que hay una alerta
            from datetime import datetime, timedelta
            fecha_parto = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                UPDATE reproduccion 
                SET fecha_parto_estimada = %s
                WHERE id = 1
            """, (fecha_parto,))
            conn.commit()
            
            # Consultar datos de partos próximos para verificación
            cursor.execute("""
                SELECT a.nombre, a.numero_arete, r.fecha_parto_estimada, 
                       DATEDIFF(r.fecha_parto_estimada, CURDATE()) as dias_restantes
                FROM reproduccion r
                JOIN animales a ON r.animal_id = a.id
                WHERE r.fecha_parto_estimada >= CURDATE()
                ORDER BY r.fecha_parto_estimada
            """)
            
            partos = cursor.fetchall()
            if partos:
                print(f"Partos próximos encontrados: {len(partos)}")
                for p in partos:
                    print(f"Animal: {p[0]} (Arete: {p[1]})")
                    print(f"Fecha de parto: {p[2]}")
                    print(f"Días restantes: {p[3]}")
            else:
                print("No se encontraron partos próximos en la base de datos")
            
            # 2. Verificar y actualizar datos de vacunación para asegurar que hay alertas pendientes
            print("\n------ Verificando datos de vacunación ------")
            
            # Actualizar fecha de vacunación próxima para asegurar que hay una alerta
            fecha_vacuna = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            
            # Primero verificamos si hay registros de vacunas
            cursor.execute("SELECT COUNT(*) FROM vacuna")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Crear una vacuna de ejemplo si no hay
                cursor.execute("""
                    INSERT INTO vacuna (nombre, fecha_aplicacion, proxima_aplicacion, dosis, observaciones)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    'Vacuna Aftosa', 
                    (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                    fecha_vacuna,
                    '5ml subcutáneo',
                    'Vacunación semestral obligatoria'
                ))
                vacuna_id = cursor.lastrowid
                
                # Asignar animales a la vacuna
                cursor.execute("SELECT id FROM animales LIMIT 5")
                animales = cursor.fetchall()
                for animal in animales:
                    cursor.execute("""
                        INSERT INTO vacuna_animal (vacuna_id, animal_id)
                        VALUES (%s, %s)
                    """, (vacuna_id, animal[0]))
                
                conn.commit()
                print(f"Creada vacuna de ejemplo con fecha próxima: {fecha_vacuna}")
            else:
                # Actualizar la fecha de la vacuna existente
                cursor.execute("""
                    UPDATE vacuna
                    SET proxima_aplicacion = %s
                    WHERE id = 1
                """, (fecha_vacuna,))
                conn.commit()
                print(f"Actualizada fecha de vacunación próxima: {fecha_vacuna}")
            
            # Consultar datos de vacunas próximas para verificación
            cursor.execute("""
                SELECT v.nombre, v.proxima_aplicacion, 
                       COUNT(va.animal_id) as cantidad_animales,
                       DATEDIFF(v.proxima_aplicacion, CURDATE()) as dias_restantes
                FROM vacuna v
                JOIN vacuna_animal va ON v.id = va.vacuna_id
                WHERE v.proxima_aplicacion >= CURDATE()
                GROUP BY v.id
                ORDER BY v.proxima_aplicacion
            """)
            
            vacunas = cursor.fetchall()
            if vacunas:
                print(f"Vacunas próximas encontradas: {len(vacunas)}")
                for v in vacunas:
                    print(f"Vacuna: {v[0]}")
                    print(f"Fecha próxima: {v[1]}")
                    print(f"Cantidad de animales: {v[2]}")
                    print(f"Días restantes: {v[3]}")
            else:
                print("No se encontraron vacunas próximas en la base de datos")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Error al actualizar datos de prueba: {e}")
        
        # 3. Verificar partos próximos
        print("\n------ VERIFICANDO ENVÍO DE ALERTAS DE PARTOS PRÓXIMOS ------")
        try:
            notificaciones_partos = sistema_alarmas.verificar_partos_proximos()
            print(f"Notificaciones de partos enviadas: {notificaciones_partos}")
        except Exception as e:
            print(f"Error al verificar partos próximos: {e}")
        
        # 4. Verificar vacunaciones pendientes
        print("\n------ VERIFICANDO ENVÍO DE ALERTAS DE VACUNACIONES PENDIENTES ------")
        try:
            notificaciones_vacunaciones = sistema_alarmas.verificar_vacunaciones_pendientes()
            print(f"Notificaciones de vacunaciones enviadas: {notificaciones_vacunaciones}")
        except Exception as e:
            print(f"Error al verificar vacunaciones pendientes: {e}")
    
    print("\n====== VERIFICACIÓN DE ALERTAS ESPECÍFICAS FINALIZADA ======\n")

if __name__ == "__main__":
    verificar_alertas_especificas()
