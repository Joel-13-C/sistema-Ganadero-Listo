import os
import logging
import random

class GanaderiaChatbot:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        
        # Preguntas frecuentes y respuestas
        self.respuestas = {
            "saludo": ["¡Hola! Escribe 'ayuda' para ver las preguntas frecuentes."],
            "ayuda": ["Preguntas frecuentes:\n1. ¿Cuántos animales tengo?\n2. ¿Qué razas hay en mi ganado?\n3. ¿Cuándo es la próxima vacunación?\n4. ¿Hay partos programados?\n5. ¿Hay alertas pendientes?"],
            "default": ["No entendí tu pregunta. Escribe 'ayuda' para ver las preguntas frecuentes."]
        }
    
    def generar_respuesta(self, mensaje, usuario_id):
        try:
            # Obtener información relevante del usuario y sus animales
            animales = self.db_connection.obtener_animales_por_usuario(usuario_id)
            total_animales = len(animales)
            razas = set(animal['raza'] for animal in animales)
            
            # Convertir mensaje a minúsculas para comparación
            mensaje_lower = mensaje.lower()
            
            # Lógica de respuestas
            if any(palabra in mensaje_lower for palabra in ['hola', 'hi', 'hey']):
                return random.choice(self.respuestas['saludo'])
            
            if any(palabra in mensaje_lower for palabra in ['ayuda', 'help', 'asistencia']):
                return random.choice(self.respuestas['ayuda'])
            
            if any(palabra in mensaje_lower for palabra in ['animal', 'animales', 'rebaño', 'ganado']):
                return f"""Información de tu rebaño:
- Total de Animales: {total_animales}
- Razas: {', '.join(razas)}

¿Quieres saber más detalles sobre tus animales?"""
            
            # Respuesta por defecto
            return random.choice(self.respuestas['default'])
        
        except Exception as e:
            logging.error(f"Error en chatbot: {e}")
            return "Lo siento, hubo un problema procesando tu mensaje."
