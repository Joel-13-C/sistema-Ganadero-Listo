#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificar desparasitaciones pendientes en el sistema.
"""

from src.database import get_db_connection
import sys
from datetime import datetime, timedelta

def main():
    """
    Función principal que verifica las desparasitaciones pendientes
    """
    print("\n===== VERIFICANDO DESPARASITACIONES PENDIENTES =====\n")
    
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Calcular la fecha límite (próximos 7 días)
        fecha_limite = datetime.now() + timedelta(days=7)
        
        # Buscar desparasitaciones pendientes
        query = """
            SELECT d.*, GROUP_CONCAT(a.id) as animal_ids, 
                   GROUP_CONCAT(a.nombre) as nombres_animales,
                   GROUP_CONCAT(a.numero_arete) as aretes_animales
            FROM desparasitacion d
            JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id
            JOIN animales a ON da.animal_id = a.id
            WHERE d.proxima_aplicacion <= %s
            AND d.proxima_aplicacion >= CURDATE()
            GROUP BY d.id
        """
        
        print(f"Ejecutando consulta: {query}")
        print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
        
        cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
        
        desparasitaciones = cursor.fetchall()
        print(f"Desparasitaciones pendientes encontradas: {len(desparasitaciones)}")
        
        if desparasitaciones:
            print("\n==== DETALLES DE DESPARASITACIONES PENDIENTES ====")
            for d in desparasitaciones:
                dias_restantes = (d['proxima_aplicacion'] - datetime.now().date()).days
                print(f"Desparasitación: ID={d['id']}, Producto={d['producto']}")
                print(f"  Fecha próxima aplicación: {d['proxima_aplicacion']}")
                print(f"  Días restantes: {dias_restantes}")
                print(f"  Animales: {d['nombres_animales']}")
                print("  ----------------------------------------")
        else:
            print("No se encontraron desparasitaciones pendientes en los próximos 7 días")
        
        return 0  # Éxito
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1  # Error
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
