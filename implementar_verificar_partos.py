# Script para implementar el método verificar_partos_proximos en la clase SistemaAlarmas
import os

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')

# Código del método a añadir
codigo_metodo = """
    def verificar_partos_proximos(self):
        \"\"\"
        Verifica si hay partos próximos y envía notificaciones
        
        Returns:
            int: Número de notificaciones enviadas
        \"\"\"
        try:
            print("\\n==== INICIANDO VERIFICACIÓN DE PARTOS PRÓXIMOS ====\\n")
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para verificar partos próximos")
                print("Error: No se pudo conectar a la base de datos")
                return 0
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas de parto activas
            query_config = "SELECT * FROM config_alarmas WHERE tipo = 'parto' AND activo = TRUE"
            print(f"Ejecutando consulta: {query_config}")
            
            cursor.execute(query_config)
            
            configuraciones = cursor.fetchall()
            print(f"Configuraciones de alarmas activas encontradas: {len(configuraciones)}")
            
            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado
            if not configuraciones:
                logger.info("No hay configuraciones de alarmas de parto activas, usando configuración predeterminada")
                print("No hay configuraciones de alarmas de parto activas. Usando configuración predeterminada.")
                
                # Crear una configuración predeterminada
                configuraciones = [{
                    'usuario_id': 1,  # Usuario administrador por defecto
                    'dias_anticipacion': 7,  # 7 días de anticipación
                    'email': self.email_config['username']  # Usar el correo configurado
                }]
            
            notificaciones_enviadas = 0
            
            # Para cada configuración, buscar partos próximos
            for config in configuraciones:
                usuario_id = config['usuario_id']
                dias_anticipacion = config['dias_anticipacion']
                email = config['email']
                
                # Calcular la fecha límite
                from datetime import datetime, timedelta
                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)
                
                # Imprimir información de depuración
                print(f"Buscando partos para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}")
                
                # Buscar animales con partos próximos
                query = \"\"\"
                    SELECT a.*, r.fecha_parto_estimada, DATEDIFF(r.fecha_parto_estimada, CURDATE()) as dias_restantes
                    FROM animales a
                    JOIN reproduccion r ON a.id = r.animal_id
                    WHERE a.sexo = 'Hembra' 
                    AND r.fecha_parto_estimada IS NOT NULL
                    AND r.fecha_parto_estimada <= %s
                    AND r.fecha_parto_estimada >= CURDATE()
                \"\"\"
                
                print(f"Ejecutando consulta: {query}")
                print(f"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}")
                
                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))
                
                animales = cursor.fetchall()
                print(f"Animales con partos próximos encontrados: {len(animales)}")
                
                if animales:
                    print("\\n==== DETALLES DE PARTOS PRÓXIMOS ====")
                    for a in animales:
                        print(f"Animal: {a['nombre']} (ID={a['id']}, Arete={a['numero_arete']})")
                        print(f"  Fecha estimada de parto: {a['fecha_parto_estimada']}")
                        print(f"  Días restantes: {a['dias_restantes']}")
                        print("  ----------------------------------------")
                
                if animales:
                    # Enviar notificaciones para estos animales
                    for animal in animales:
                        # Calcular días restantes
                        dias_restantes = animal['dias_restantes']
                        
                        # Preparar el asunto del correo
                        asunto = f"ALERTA: Parto próximo - {animal['nombre']} en {dias_restantes} días"
                        
                        # Preparar el mensaje del correo
                        mensaje = f\"\"\"
                        ALERTA DE PARTO PRÓXIMO
                        
                        Hay un parto programado próximamente.
                        
                        Detalles:
                        - Animal: {animal['nombre']}
                        - Número de arete: {animal['numero_arete']}
                        - Fecha estimada de parto: {animal['fecha_parto_estimada'].strftime('%d/%m/%Y')}
                        - Días restantes: {dias_restantes}
                        
                        Por favor, prepare todo lo necesario para atender el parto.
                        \"\"\"
                        
                        # Enviar la notificación
                        print(f"Enviando notificación de parto a {email}:")
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
                                    'parto',
                                    animal['id'],
                                    email,
                                    mensaje
                                ))
                                conn.commit()
                                notificaciones_enviadas += 1
                                print(f"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}")
                            except Exception as e:
                                print(f"Error al registrar notificación: {e}")
            
            print(f"\\n==== VERIFICACIÓN DE PARTOS PRÓXIMOS FINALIZADA ====")
            print(f"Total de notificaciones enviadas: {notificaciones_enviadas}")
            
            return notificaciones_enviadas
            
        except Exception as e:
            logger.error(f"Error al verificar partos próximos: {e}")
            print(f"Error: {e}")
            return 0
"""

# Leer el contenido actual del archivo
with open(alarmas_path, 'r', encoding='utf-8') as file:
    contenido = file.read()

# Encontrar la posición adecuada para añadir el nuevo método
# Buscar el fin del método verificar_desparasitaciones_pendientes (que sabemos que ya existe)
posicion_final_metodo = contenido.find("def verificar_desparasitaciones_pendientes")
posicion_final_metodo = contenido.find("    def", posicion_final_metodo + 10)

if posicion_final_metodo != -1:
    # Añadir el nuevo método después del método verificar_desparasitaciones_pendientes
    nuevo_contenido = contenido[:posicion_final_metodo] + codigo_metodo + contenido[posicion_final_metodo:]
    
    # Guardar el archivo actualizado
    with open(alarmas_path, 'w', encoding='utf-8') as file:
        file.write(nuevo_contenido)
    
    print("Método verificar_partos_proximos añadido correctamente a la clase SistemaAlarmas")
else:
    print("No se pudo encontrar la posición adecuada para añadir el método")
