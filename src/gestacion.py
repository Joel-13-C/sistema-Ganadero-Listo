import pg8000
from datetime import datetime, timedelta
from src.database import get_db_connection
from flask import flash

def dictfetchall(cursor):
    """Convierte los resultados del cursor a una lista de diccionarios."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def registrar_gestacion(animal_id, fecha_monta, observaciones):
    try:
        # Validar que el animal existe y es hembra
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, sexo, condicion, usuario_id
            FROM animales 
            WHERE id = %s
        """, (animal_id,))
        animal = cursor.fetchone()
        
        if not animal:
            return False, "Animal no encontrado"
        
        # animal es una tupla: (id, sexo, condicion, usuario_id)
        if animal[1] != 'Hembra':  # sexo está en la posición 1
            return False, "Solo se puede registrar gestación para animales hembra"
            
        if animal[2] not in ['Vaca', 'Vacona']:  # condicion está en la posición 2
            return False, "Solo se puede registrar gestación para vacas o vaconas"
        
        # Calcular fecha probable de parto (283 días después de la monta)
        fecha_monta_obj = datetime.strptime(fecha_monta, '%Y-%m-%d')
        fecha_probable_parto = fecha_monta_obj + timedelta(days=283)
        
        # Verificar si ya existe una gestación activa
        cursor.execute("""
            SELECT id FROM gestaciones 
            WHERE animal_id = %s AND estado = 'En Gestación'
        """, (animal_id,))
        
        if cursor.fetchone():
            return False, "Este animal ya tiene una gestación activa registrada"
        
        # Insertar el registro de gestación
        cursor.execute("""
            INSERT INTO gestaciones (animal_id, fecha_monta, fecha_probable_parto, 
                                estado, observaciones, usuario_id)
            VALUES (%s, %s, %s, 'En Gestación', %s, %s)
        """, (animal_id, fecha_monta, fecha_probable_parto.strftime('%Y-%m-%d'), 
              observaciones, animal[3]))  # usuario_id está en la posición 3
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Gestación registrada exitosamente"
        
    except Exception as e:
        return False, f"Error al registrar la gestación: {str(e)}"

def obtener_gestaciones(usuario_id=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if usuario_id:
            cursor.execute("""
                SELECT g.*, a.numero_arete, a.nombre, a.condicion
                FROM gestaciones g
                JOIN animales a ON g.animal_id = a.id
                WHERE a.usuario_id = %s
                ORDER BY g.fecha_registro DESC
            """, (usuario_id,))
        else:
            cursor.execute("""
                SELECT g.*, a.numero_arete, a.nombre, a.condicion
                FROM gestaciones g
                JOIN animales a ON g.animal_id = a.id
                ORDER BY g.fecha_registro DESC
            """)
        
        gestaciones = dictfetchall(cursor)
        
        # Calcular días restantes para cada gestación y actualizar estado si es necesario
        for g in gestaciones:
            if g['estado'] == 'En Gestación':
                # Usar la fecha probable de parto almacenada en la base de datos
                fecha_probable_parto = g['fecha_probable_parto']
                dias_restantes = (fecha_probable_parto - datetime.now().date()).days
                g['dias_restantes'] = max(0, dias_restantes)
                # Agregar la fecha probable de parto al diccionario para usarla en la plantilla
                g['fecha_probable_parto'] = fecha_probable_parto
                
                # Si los días restantes son 0 y el estado aún es 'En Gestación', actualizarlo
                if g['dias_restantes'] == 0:
                    observacion = f"\n[{datetime.now().strftime('%Y-%m-%d')}] Parto detectado automáticamente por el sistema."
                    cursor.execute("""
                        UPDATE gestaciones 
                        SET estado = 'Finalizado',
                            observaciones = COALESCE(observaciones, '') || %s
                        WHERE id = %s AND estado = 'En Gestación'
                    """, (observacion, g['id']))
                    conn.commit()
                    g['estado'] = 'Finalizado'
                    g['observaciones'] = (g['observaciones'] or '') + observacion
            else:
                g['dias_restantes'] = 0
        
        cursor.close()
        conn.close()
        
        return gestaciones
        
    except Exception as e:
        print(f"Error al obtener gestaciones: {str(e)}")
        return []

def obtener_gestaciones_proximas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener gestaciones que están a 7 días o menos del parto y aún están activas
        cursor.execute("""
            SELECT g.*, a.numero_arete, a.nombre, a.condicion,
                   (g.fecha_probable_parto - CURRENT_DATE) as dias_restantes
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.estado = 'En Gestación'
            AND (g.fecha_probable_parto - CURRENT_DATE) BETWEEN 0 AND 7
            ORDER BY g.fecha_probable_parto ASC
        """)
        
        gestaciones_proximas = dictfetchall(cursor)
        cursor.close()
        conn.close()
        
        return gestaciones_proximas
        
    except Exception as e:
        print(f"Error al obtener gestaciones próximas: {str(e)}")
        return []

def actualizar_estado_gestacion(gestacion_id, nuevo_estado, observaciones=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_query = """
            UPDATE gestaciones 
            SET estado = %s, observaciones = COALESCE(observaciones, '') || '\n' || %s
            WHERE id = %s
        """
        
        observacion_estado = f"\n[{datetime.now().strftime('%Y-%m-%d')}] Cambio de estado a: {nuevo_estado}"
        if observaciones:
            observacion_estado += f" - {observaciones}"
            
        cursor.execute(update_query, (nuevo_estado, observacion_estado, gestacion_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Estado de gestación actualizado correctamente"
        
    except Exception as e:
        return False, f"Error al actualizar el estado: {str(e)}"

def eliminar_gestacion(gestacion_id):
    """
    Elimina un registro de gestación por su ID
    
    Args:
        gestacion_id (int): ID del registro de gestación a eliminar
        
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que la gestación existe
        cursor.execute("SELECT id FROM gestaciones WHERE id = %s", (gestacion_id,))
        gestacion = cursor.fetchone()
        
        if not gestacion:
            return False, "El registro de gestación no existe"
        
        # Eliminar la gestación
        cursor.execute("DELETE FROM gestaciones WHERE id = %s", (gestacion_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True, "Registro de gestación eliminado correctamente"
        
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error al eliminar el registro de gestación: {str(e)}"
