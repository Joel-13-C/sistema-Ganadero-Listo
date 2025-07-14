# Script para implementar el método verificar_vacunaciones_pendientes en la clase SistemaAlarmas
import os

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')

# Código del método a añadir
codigo_metodo = """
    def verificar_vacunaciones_pendientes(self):
        \"\"\"
        Verifica si hay vacunaciones pendientes y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        \"\"\"
        try:
            print("\\n==== INICIANDO VERIFICACIÓN DE VACUNACIONES PENDIENTES ====\\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar vacunaciones pendientes")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas de vacunación activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'vacunacion' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = cursor.fetchall()
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de vacunación activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de vacunación activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar vacunaciones pendientes
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                from datetime import datetime, timedelta
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando vacunaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar vacunaciones pendientes
                query = \"\"\"
                    SELECT v.*, GROUP_CONCAT(a.id) as animal_ids, 
                           GROUP_CONCAT(a.nombre) as nombres_animales,
                           GROUP_CONCAT(a.numero_arete) as aretes_animales
                    FROM vacuna v
                    JOIN vacuna_animal va ON v.id = va.vacuna_id
                    JOIN animales a ON va.animal_id = a.id
                    WHERE v.proxima_aplicacion <= %s
                    AND v.proxima_aplicacion >= CURDATE()
                    GROUP BY v.id
                \"\"\"
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                vacunaciones = cursor.fetchall()
                print(f"Vacunaciones pendientes encontradas: {len(vacunaciones)}")
                
                if vacunaciones:
                    print("\\n==== DETALLES DE VACUNACIONES PENDIENTES ====")
                    for v in vacunaciones:
                        dias_restantes = (v['proxima_aplicacion'] - datetime.now().date()).days
                        print(f"Vacunación: ID={v['id']}, Vacuna={v['nombre']}")
                        print(f"  Fecha próxima aplicación: {v['proxima_aplicacion']}")
                        print(f"  Días restantes: {dias_restantes}")
                        print(f"  Animales: {v['nombres_animales']}")
                        print("  ----------------------------------------")
                
                if vacunaciones:
                    # Enviar notificaciones para estas vacunaciones
                    for vacunacion in vacunaciones:
                        # Calcular días restantes
                        dias_restantes = (vacunacion['proxima_aplicacion'] - datetime.now().date()).days
                        
                        # Preparar lista de animales
                        nombres_animales = vacunacion['nombres_animales'].split(',') if vacunacion['nombres_animales'] else []
                        aretes_animales = vacunacion['aretes_animales'].split(',') if vacunacion['aretes_animales'] else []
                        
                        # Crear lista formateada de animales
                        lista_animales = ""
                        for i in range(min(len(nombres_animales), len(aretes_animales))):
                            lista_animales += f"- {nombres_animales[i]} (Arete: {aretes_animales[i]})\\n"
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Vacunación pendiente - {vacunacion['nombre']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f\"\"\"
                        ALERTA DE VACUNACIÓN PENDIENTE
                        
                        Hay una vacunación programada próximamente.
                        
                        Detalles:
                        - Vacuna: {vacunacion['nombre']}
                        - Fecha de aplicación: {vacunacion['proxima_aplicacion'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Animales que requieren vacunación:
                        {lista_animales}
                        
                        Por favor, prepare todo lo necesario para realizar la vacunación.
                        \"\"\"
                        
                        # Enviar la notificación
                        print(f"Enviando notificación de vacunación a {email}:")
                        print(f"Asunto: {asunto}")
                        print(f"Descripción: {mensaje}")
                        
                        enviado = self._enviar_notificacion_email(email, asunto, mensaje)
                        
                        if enviado:
                            # Registrar la notificación en la base de datos
                            try:
                                cursor.execute(\"\"\"
                                    INSERT INTO alarmas_enviadas
                                    (tipo, referencia_id, email, mensaje, fecha_envio)
                                    VALUES (%s, %s, %s, %s, NOW())
                                \"\"\", (
                                    'vacunacion',
                                    vacunacion['id'],
                                    email,
                                    mensaje
                                ))
                                conn.commit()
                                notificaciones_enviadas += 1
                                print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
                            except Exception as e:
                                print(f"Error al registrar notificación: {e}")
            
            print(f"\\n==== VERIFICACIÓN DE VACUNACIONES PENDIENTES FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar vacunaciones pendientes: {e}")
            print(f"Error: {e}")
            return 0
"""

# Leer el contenido actual del archivo
with open(alarmas_path, 'r', encoding='utf-8') as file:
    contenido = file.read()

# Encontrar la posición adecuada para añadir el nuevo método
# Buscar el método que acabamos de añadir verificar_partos_proximos
posicion_final_metodo = contenido.find("def verificar_partos_proximos")
posicion_final_metodo = contenido.find("    def", posicion_final_metodo + 10)

if posicion_final_metodo != -1:
    # Añadir el nuevo método después del método verificar_partos_proximos
    nuevo_contenido = contenido[:posicion_final_metodo] + codigo_metodo + contenido[posicion_final_metodo:]
    
    # Guardar el archivo actualizado
    with open(alarmas_path, 'w', encoding='utf-8') as file:
        file.write(nuevo_contenido)
    
    print("Método verificar_vacunaciones_pendientes añadido correctamente a la clase SistemaAlarmas")
else:
    print("No se pudo encontrar la posición adecuada para añadir el método")
