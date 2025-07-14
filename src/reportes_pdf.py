from flask import render_template, make_response
from xhtml2pdf import pisa
from io import BytesIO
import datetime
from datetime import datetime, timedelta
from src.database import get_db_connection

# Función auxiliar para convertir HTML a PDF
def html_to_pdf(html_content):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

# Función para generar reporte de animales
def generar_reporte_animales(categoria_animal, estado_animal):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Fecha de generación del reporte
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Construir la consulta SQL con filtros
        query = """
            SELECT a.*, ca.nombre as categoria 
            FROM animales a
            JOIN categorias_animales ca ON a.categoria_id = ca.id
            WHERE 1=1
        """
        params = []
        
        if categoria_animal and categoria_animal != 'todas':
            query += " AND a.categoria_id = %s"
            params.append(categoria_animal)
            
        if estado_animal and estado_animal != 'todos':
            query += " AND a.estado = %s"
            params.append(estado_animal)
            
        query += " ORDER BY a.nombre_arete"
        
        # Ejecutar la consulta
        cursor.execute(query, params)
        animales = cursor.fetchall()
        
        # Calcular estadísticas
        total_machos = sum(1 for animal in animales if animal['sexo'] == 'Macho')
        total_hembras = sum(1 for animal in animales if animal['sexo'] == 'Hembra')
        valor_total = sum(float(animal['valor_estimado']) for animal in animales if animal['valor_estimado'])
        
        # Renderizar la plantilla HTML
        html = render_template('reportes_pdf/reporte_animales.html',
                              titulo="Reporte de Animales",
                              fecha_generacion=fecha_generacion,
                              animales=animales,
                              total_machos=total_machos,
                              total_hembras=total_hembras,
                              valor_total=valor_total)
        
        # Generar el PDF
        pdf = html_to_pdf(html)
        
        # Crear la respuesta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_animales.pdf'
        
        cursor.close()
        db.close()
        
        return response
    
    except Exception as e:
        print(f"Error al generar el reporte de animales: {str(e)}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()
        raise e

# Función para generar reporte financiero
def generar_reporte_financiero(periodo_financiero, fecha_inicio=None, fecha_fin=None):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Fecha de generación del reporte
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Determinar el rango de fechas según el período seleccionado
        hoy = datetime.now()
        if periodo_financiero == 'mes_actual':
            inicio_mes = datetime(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                fin_mes = datetime(hoy.year + 1, 1, 1) - timedelta(days=1)
            else:
                fin_mes = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            fecha_inicio = inicio_mes
            fecha_fin = fin_mes
            periodo = f"{hoy.strftime('%B %Y')}"
        elif periodo_financiero == 'mes_anterior':
            if hoy.month == 1:
                inicio_mes = datetime(hoy.year - 1, 12, 1)
                fin_mes = datetime(hoy.year, 1, 1) - timedelta(days=1)
            else:
                inicio_mes = datetime(hoy.year, hoy.month - 1, 1)
                fin_mes = datetime(hoy.year, hoy.month, 1) - timedelta(days=1)
            fecha_inicio = inicio_mes
            fecha_fin = fin_mes
            periodo = f"{inicio_mes.strftime('%B %Y')}"
        elif periodo_financiero == 'anio_actual':
            fecha_inicio = datetime(hoy.year, 1, 1)
            fecha_fin = datetime(hoy.year, 12, 31)
            periodo = f"Año {hoy.year}"
        else:  # personalizado
            periodo = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
        
        # Obtener ingresos en el período
        cursor.execute("""
            SELECT i.*, ci.nombre as categoria 
            FROM ingresos i
            JOIN categorias_ingresos ci ON i.categoria_id = ci.id
            WHERE i.fecha BETWEEN %s AND %s
            ORDER BY i.fecha
        """, (fecha_inicio, fecha_fin))
        ingresos = cursor.fetchall()
        
        # Obtener gastos en el período
        cursor.execute("""
            SELECT g.*, cg.nombre as categoria 
            FROM gastos g
            JOIN categorias_gastos cg ON g.categoria_id = cg.id
            WHERE g.fecha BETWEEN %s AND %s
            ORDER BY g.fecha
        """, (fecha_inicio, fecha_fin))
        gastos = cursor.fetchall()
        
        # Calcular totales
        total_ingresos = sum(float(ingreso['monto']) for ingreso in ingresos)
        total_gastos = sum(float(gasto['monto']) for gasto in gastos)
        balance = total_ingresos - total_gastos
        
        # Calcular ingresos por categoría
        ingresos_por_categoria = []
        cursor.execute("""
            SELECT ci.nombre, SUM(i.monto) as monto
            FROM ingresos i
            JOIN categorias_ingresos ci ON i.categoria_id = ci.id
            WHERE i.fecha BETWEEN %s AND %s
            GROUP BY ci.nombre
            ORDER BY monto DESC
        """, (fecha_inicio, fecha_fin))
        for categoria in cursor.fetchall():
            porcentaje = (float(categoria['monto']) / total_ingresos * 100) if total_ingresos > 0 else 0
            ingresos_por_categoria.append({
                'nombre': categoria['nombre'],
                'monto': float(categoria['monto']),
                'porcentaje': porcentaje
            })
        
        # Calcular gastos por categoría
        gastos_por_categoria = []
        cursor.execute("""
            SELECT cg.nombre, SUM(g.monto) as monto
            FROM gastos g
            JOIN categorias_gastos cg ON g.categoria_id = cg.id
            WHERE g.fecha BETWEEN %s AND %s
            GROUP BY cg.nombre
            ORDER BY monto DESC
        """, (fecha_inicio, fecha_fin))
        for categoria in cursor.fetchall():
            porcentaje = (float(categoria['monto']) / total_gastos * 100) if total_gastos > 0 else 0
            gastos_por_categoria.append({
                'nombre': categoria['nombre'],
                'monto': float(categoria['monto']),
                'porcentaje': porcentaje
            })
        
        # Renderizar la plantilla HTML
        html = render_template('reportes_pdf/reporte_financiero.html',
                              titulo="Reporte Financiero",
                              fecha_generacion=fecha_generacion,
                              periodo=periodo,
                              ingresos=ingresos,
                              gastos=gastos,
                              total_ingresos=total_ingresos,
                              total_gastos=total_gastos,
                              balance=balance,
                              ingresos_por_categoria=ingresos_por_categoria,
                              gastos_por_categoria=gastos_por_categoria)
        
        # Generar el PDF
        pdf = html_to_pdf(html)
        
        # Crear la respuesta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_financiero.pdf'
        
        cursor.close()
        db.close()
        
        return response
    
    except Exception as e:
        print(f"Error al generar el reporte financiero: {str(e)}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()
        raise e

# Función para generar reporte de salud
def generar_reporte_salud(periodo_salud, tipo_evento, fecha_inicio=None, fecha_fin=None):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Fecha de generación del reporte
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Determinar el rango de fechas según el período seleccionado
        hoy = datetime.now()
        if periodo_salud == 'mes_actual':
            inicio_mes = datetime(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                fin_mes = datetime(hoy.year + 1, 1, 1) - timedelta(days=1)
            else:
                fin_mes = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            fecha_inicio = inicio_mes
            fecha_fin = fin_mes
            periodo = f"{hoy.strftime('%B %Y')}"
        elif periodo_salud == 'mes_anterior':
            if hoy.month == 1:
                inicio_mes = datetime(hoy.year - 1, 12, 1)
                fin_mes = datetime(hoy.year, 1, 1) - timedelta(days=1)
            else:
                inicio_mes = datetime(hoy.year, hoy.month - 1, 1)
                fin_mes = datetime(hoy.year, hoy.month, 1) - timedelta(days=1)
            fecha_inicio = inicio_mes
            fecha_fin = fin_mes
            periodo = f"{inicio_mes.strftime('%B %Y')}"
        elif periodo_salud == 'anio_actual':
            fecha_inicio = datetime(hoy.year, 1, 1)
            fecha_fin = datetime(hoy.year, 12, 31)
            periodo = f"Año {hoy.year}"
        else:  # personalizado
            periodo = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
        
        # Construir la consulta SQL con filtros
        query = """
            SELECT es.*, a.nombre_arete as animal 
            FROM eventos_salud es
            JOIN animales a ON es.animal_id = a.id
            WHERE es.fecha BETWEEN %s AND %s
        """
        params = [fecha_inicio, fecha_fin]
        
        if tipo_evento and tipo_evento != 'todos':
            query += " AND es.tipo = %s"
            params.append(tipo_evento)
            
        query += " ORDER BY es.fecha DESC"
        
        # Ejecutar la consulta
        cursor.execute(query, params)
        eventos = cursor.fetchall()
        
        # Calcular estadísticas
        total_vacunaciones = sum(1 for evento in eventos if evento['tipo'] == 'Vacunación')
        total_tratamientos = sum(1 for evento in eventos if evento['tipo'] == 'Tratamiento')
        total_enfermedades = sum(1 for evento in eventos if evento['tipo'] == 'Enfermedad')
        
        # Obtener próximas vacunaciones
        cursor.execute("""
            SELECT es.*, a.nombre_arete as animal, 
                   DATE_ADD(es.fecha, INTERVAL es.recordatorio_dias DAY) as fecha_programada,
                   DATEDIFF(DATE_ADD(es.fecha, INTERVAL es.recordatorio_dias DAY), CURDATE()) as dias_restantes
            FROM eventos_salud es
            JOIN animales a ON es.animal_id = a.id
            WHERE es.tipo = 'Vacunación'
            AND es.recordatorio_dias > 0
            AND DATE_ADD(es.fecha, INTERVAL es.recordatorio_dias DAY) >= CURDATE()
            ORDER BY fecha_programada
            LIMIT 10
        """)
        proximas_vacunas = cursor.fetchall()
        
        # Renderizar la plantilla HTML
        html = render_template('reportes_pdf/reporte_salud.html',
                              titulo="Reporte de Salud Animal",
                              fecha_generacion=fecha_generacion,
                              periodo=periodo,
                              eventos=eventos,
                              total_vacunaciones=total_vacunaciones,
                              total_tratamientos=total_tratamientos,
                              total_enfermedades=total_enfermedades,
                              proximas_vacunas=proximas_vacunas)
        
        # Generar el PDF
        pdf = html_to_pdf(html)
        
        # Crear la respuesta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_salud.pdf'
        
        cursor.close()
        db.close()
        
        return response
    
    except Exception as e:
        print(f"Error al generar el reporte de salud: {str(e)}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()
        raise e

# Función para generar reporte de producción
def generar_reporte_produccion(periodo_produccion, fecha_inicio=None, fecha_fin=None):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Fecha de generación del reporte
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Determinar el rango de fechas según el período seleccionado
        hoy = datetime.now()
        if periodo_produccion == 'mes_actual':
            inicio_mes = datetime(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                fin_mes = datetime(hoy.year + 1, 1, 1) - timedelta(days=1)
            else:
                fin_mes = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            fecha_inicio = inicio_mes
            fecha_fin = fin_mes
            periodo = f"{hoy.strftime('%B %Y')}"
        elif periodo_produccion == 'mes_anterior':
            if hoy.month == 1:
                inicio_mes = datetime(hoy.year - 1, 12, 1)
                fin_mes = datetime(hoy.year, 1, 1) - timedelta(days=1)
            else:
                inicio_mes = datetime(hoy.year, hoy.month - 1, 1)
                fin_mes = datetime(hoy.year, hoy.month, 1) - timedelta(days=1)
            fecha_inicio = inicio_mes
            fecha_fin = fin_mes
            periodo = f"{inicio_mes.strftime('%B %Y')}"
        elif periodo_produccion == 'anio_actual':
            fecha_inicio = datetime(hoy.year, 1, 1)
            fecha_fin = datetime(hoy.year, 12, 31)
            periodo = f"Año {hoy.year}"
        else:  # personalizado
            periodo = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
        
        # Obtener registros de leche en el período
        cursor.execute("""
            SELECT rl.*, a.nombre_arete as animal_nombre
            FROM registro_leche rl
            JOIN animales a ON rl.animal_id = a.id
            WHERE rl.fecha BETWEEN %s AND %s
            ORDER BY rl.fecha
        """, (fecha_inicio, fecha_fin))
        registros_leche = cursor.fetchall()
        
        # Calcular totales
        total_leche = sum(float(registro['cantidad']) for registro in registros_leche)
        dias_periodo = (fecha_fin - fecha_inicio).days + 1
        promedio_diario = total_leche / dias_periodo if dias_periodo > 0 else 0
        
        # Calcular valor estimado (usando precio promedio de venta)
        cursor.execute("""
            SELECT AVG(precio_litro) as precio_promedio
            FROM ventas_leche
            WHERE fecha BETWEEN %s AND %s
        """, (fecha_inicio, fecha_fin))
        resultado = cursor.fetchone()
        precio_promedio = float(resultado['precio_promedio']) if resultado['precio_promedio'] else 0
        valor_total = total_leche * precio_promedio
        
        # Calcular producción por animal
        produccion_por_animal = []
        cursor.execute("""
            SELECT a.nombre_arete as nombre, 
                   SUM(rl.cantidad) as total,
                   COUNT(DISTINCT rl.fecha) as dias
            FROM registro_leche rl
            JOIN animales a ON rl.animal_id = a.id
            WHERE rl.fecha BETWEEN %s AND %s
            GROUP BY a.id
            ORDER BY total DESC
        """, (fecha_inicio, fecha_fin))
        for animal in cursor.fetchall():
            promedio = float(animal['total']) / animal['dias'] if animal['dias'] > 0 else 0
            produccion_por_animal.append({
                'nombre': animal['nombre'],
                'total': float(animal['total']),
                'promedio': round(promedio, 2),
                'dias': animal['dias']
            })
        
        # Añadir valor estimado a cada registro
        for registro in registros_leche:
            registro['valor'] = float(registro['cantidad']) * precio_promedio
        
        # Renderizar la plantilla HTML
        html = render_template('reportes_pdf/reporte_produccion.html',
                              titulo="Reporte de Producción de Leche",
                              fecha_generacion=fecha_generacion,
                              periodo=periodo,
                              registros_leche=registros_leche,
                              total_leche=total_leche,
                              promedio_diario=round(promedio_diario, 2),
                              valor_total=valor_total,
                              produccion_por_animal=produccion_por_animal)
        
        # Generar el PDF
        pdf = html_to_pdf(html)
        
        # Crear la respuesta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_produccion.pdf'
        
        cursor.close()
        db.close()
        
        return response
    
    except Exception as e:
        print(f"Error al generar el reporte de producción: {str(e)}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()
        raise e
