# Script para implementar alertas de vitaminizaciones pendientes
import os
import re

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')

# Leer el contenido del archivo
with open(alarmas_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Buscar la posición donde añadir la nueva función (después de verificar_desparasitaciones_pendientes)
pattern = r'def verificar_desparasitaciones_pendientes\(self\):.*?return notificaciones_enviadas'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Función a añadir
    nueva_funcion = """
    def verificar_vitaminizaciones_pendientes(self):
        \"\"\"
        Verifica si hay vitaminizaciones pendientes y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        \"\"\"
        try:
            print("\\n==== INICIANDO VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES ====\\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar vitaminizaciones pendientes")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas de vitaminización activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'vitaminizacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = cursor.fetchall()
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de vitaminización activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de vitaminización activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar vitaminizaciones pendientes
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando vitaminizaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar vitaminizaciones pendientes
                query = \"\"\"
                    SELECT v.*, GROUP_CONCAT(a.id) as animal_ids, 
                           GROUP_CONCAT(a.nombre) as nombres_animales,
                           GROUP_CONCAT(a.numero_arete) as aretes_animales
                    FROM vitaminizacion v
                    JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id
                    JOIN animales a ON va.animal_id = a.id
                    WHERE v.proxima_aplicacion <= %s
                    AND v.proxima_aplicacion >= CURDATE()
                    GROUP BY v.id
                \"\"\"
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                vitaminizaciones = cursor.fetchall()
                print(f"Vitaminizaciones pendientes encontradas: {len(vitaminizaciones)}")
                
                if vitaminizaciones:
                    print("\\n==== DETALLES DE VITAMINIZACIONES PENDIENTES ====")
                    for v in vitaminizaciones:
                        dias_restantes = (v['proxima_aplicacion'] - datetime.now().date()).days
                        print(f"Vitaminización: ID={v['id']}, Producto={v['producto']}")
                        print(f"  Fecha próxima aplicación: {v['proxima_aplicacion']}")
                        print(f"  Días restantes: {dias_restantes}")
                        print(f"  Animales: {v['nombres_animales']}")
                        print("  ----------------------------------------")
                
                if vitaminizaciones:
                    # Enviar notificaciones para estas vitaminizaciones
                    for vitaminizacion in vitaminizaciones:
                        # Calcular días restantes
                        dias_restantes = (vitaminizacion['proxima_aplicacion'] - datetime.now().date()).days
                        
                        # Preparar lista de animales
                        nombres_animales = vitaminizacion['nombres_animales'].split(',') if vitaminizacion['nombres_animales'] else []
                        aretes_animales = vitaminizacion['aretes_animales'].split(',') if vitaminizacion['aretes_animales'] else []
                        
                        # Crear lista formateada de animales
                        lista_animales = ""
                        for i in range(min(len(nombres_animales), len(aretes_animales))):
                            lista_animales += f"- {nombres_animales[i]} (Arete: {aretes_animales[i]})\\n"
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Vitaminización pendiente - {vitaminizacion['producto']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f\"\"\"
                        ALERTA DE VITAMINIZACIÓN PENDIENTE
                        
                        Hay una vitaminización programada próximamente.
                        
                        Detalles:
                        - Producto: {vitaminizacion['producto']}
                        - Fecha de aplicación: {vitaminizacion['proxima_aplicacion'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Animales que requieren vitaminización:
                        {lista_animales}
                        
                        Por favor, prepare todo lo necesario para realizar la vitaminización.
                        \"\"\"
                        
                        # Enviar la notificación
                        print(f"Enviando notificación de vitaminización a {email}:")
                        print(f"Asunto: {asunto}")
                        print(f"Descripción: {mensaje}")
                        
                        enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                        
                        if enviado:
                            # Registrar la notificación en la base de datos
                            cursor.execute(\"\"\"
                                INSERT INTO alarmas_enviadas
                                (tipo, referencia_id, email, asunto, mensaje, fecha_envio)
                                VALUES (%s, %s, %s, %s, %s, NOW())
                            \"\"\", (
                                'vitaminizacion',
                                vitaminizacion['id'],
                                email,
                                asunto,
                                mensaje
                            ))
                            conn.commit()
                            notificaciones_enviadas += 1
                            print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
            
            cursor.close()
            conn.close()
            
            print("\\n==== VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar vitaminizaciones pendientes: {e}")
            print(f"Error: {e}")
            return 0
    """
    
    # Insertar la nueva función después de verificar_desparasitaciones_pendientes
    posicion_insercion = match.end()
    nuevo_contenido = content[:posicion_insercion] + nueva_funcion + content[posicion_insercion:]
    
    # Guardar el archivo actualizado
    with open(alarmas_path, 'w', encoding='utf-8') as file:
        file.write(nuevo_contenido)
    
    print("Se ha añadido la función verificar_vitaminizaciones_pendientes a la clase SistemaAlarmas")
else:
    print("No se pudo encontrar el punto de inserción después de verificar_desparasitaciones_pendientes")

# También modificar app.py para incluir la verificación de vitaminizaciones
app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r', encoding='utf-8') as file:
    app_content = file.read()

# Buscar la función de verificación programada de alarmas
pattern_verificacion = r'def verificar_alarmas_programadas\(\):[^}]*?# Verificar vacunaciones pendientes[^}]*?vacunaciones = alarmas\.verificar_vacunaciones_pendientes\(\)'
match_verificacion = re.search(pattern_verificacion, app_content, re.DOTALL)

if match_verificacion:
    # Contenido original
    original = match_verificacion.group(0)
    
    # Nuevo contenido con vitaminizaciones
    nuevo = original + """
        
        # Verificar vitaminizaciones pendientes
        vitaminizaciones = alarmas.verificar_vitaminizaciones_pendientes()
        
        app.logger.info(f'Verificación programada de alarmas: {partos} notificaciones de partos, {vacunaciones} de vacunaciones y {vitaminizaciones} de vitaminizaciones enviadas')"""
    
    # Reemplazar en el contenido
    nuevo_app_content = app_content.replace(original, nuevo)
    
    # Guardar el archivo actualizado
    with open(app_path, 'w', encoding='utf-8') as file:
        file.write(nuevo_app_content)
    
    print("Se ha actualizado la función verificar_alarmas_programadas en app.py para incluir vitaminizaciones")
else:
    print("No se pudo encontrar la función verificar_alarmas_programadas en app.py")
