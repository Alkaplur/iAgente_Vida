"""
Adaptador para integrar el sistema multiagente con WhatsApp via Woztell
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from integrations.woztell_client import WoztellClient, WoztellMessage
from utils.state_manager import StateManager
from graph import crear_grafo
from models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion

logger = logging.getLogger(__name__)

class WhatsAppAdapter:
    """
    Adaptador que conecta el sistema multiagente con WhatsApp
    """
    
    def __init__(self):
        """
        Inicializa el adaptador
        """
        self.woztell_client = WoztellClient()
        self.state_manager = StateManager()
        self.grafo = crear_grafo()
        
        # Configuraciones
        self.max_message_length = 4096  # Límite de WhatsApp
        self.session_timeout_hours = 24
        
        logger.info("WhatsAppAdapter inicializado")
    
    def process_incoming_message(self, incoming_message: WoztellMessage) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante de WhatsApp
        
        Args:
            incoming_message: Mensaje de WhatsApp
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            user_id = incoming_message.from_number
            logger.info(f"Procesando mensaje de {user_id}: '{incoming_message.content}'")
            
            # Obtener o crear estado del usuario
            estado_bot = self._get_or_create_user_state(user_id, incoming_message)
            
            # Actualizar mensaje del usuario
            estado_bot.mensaje_usuario = incoming_message.content
            
            # Añadir mensaje al historial
            self._add_message_to_history(estado_bot, "user", incoming_message.content)
            
            # Detectar intención especial
            intention = self._detect_special_intention(incoming_message.content)
            
            if intention:
                response = self._handle_special_intention(intention, estado_bot)
            else:
                # Procesar con sistema multiagente
                response = self._process_with_multiagent_system(estado_bot)
            
            # Enviar respuesta
            if response["success"]:
                send_result = self._send_response(user_id, response["message"])
                
                if send_result["success"]:
                    # Guardar estado actualizado
                    self.state_manager.save_user_state(user_id, response["state"])
                    
                    return {
                        "success": True,
                        "message_sent": True,
                        "response": response["message"]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error enviando respuesta: {send_result['error']}"
                    }
            else:
                # Enviar mensaje de error
                error_msg = "Disculpa, hubo un problema procesando tu mensaje. ¿Puedes intentar de nuevo?"
                self._send_response(user_id, error_msg)
                
                return {
                    "success": False,
                    "error": response["error"]
                }
                
        except Exception as e:
            logger.error(f"Error procesando mensaje entrante: {str(e)}")
            
            # Enviar mensaje de error al usuario
            try:
                error_msg = "Disculpa, hubo un problema técnico. Por favor, intenta de nuevo en unos minutos."
                self._send_response(incoming_message.from_number, error_msg)
            except:
                pass
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_or_create_user_state(self, user_id: str, incoming_message: WoztellMessage) -> EstadoBot:
        """
        Obtiene o crea el estado de un usuario
        
        Args:
            user_id: ID del usuario
            incoming_message: Mensaje entrante
            
        Returns:
            EstadoBot del usuario
        """
        estado_bot = self.state_manager.get_user_state(user_id)
        
        if not estado_bot:
            # Crear nuevo estado
            cliente = Cliente(
                nombre="",  # Se completará durante la conversación
                edad=30,
                telefono=user_id,
                estado_civil="soltero",
                profesion="",
                ingresos_mensuales=0.0,
                gastos_fijos_mensuales=0.0,
                num_dependientes=0,
                salud_relevante="no especificado",
                tiene_seguro_vida=False,
                email=""
            )
            
            contexto = ContextoConversacional(
                plataforma="whatsapp",
                canal_origen="woztell",
                timestamp_inicio=datetime.now(),
                numero_telefono=user_id,
                idioma="es"
            )
            
            estado_bot = EstadoBot(
                cliente=cliente,
                etapa=EstadoConversacion.INICIO,
                contexto=contexto,
                mensajes=[],
                cotizaciones=[],
                mensaje_usuario="",
                next_agent="needs_based_selling",
                agente_activo="orquestador"
            )
            
            # Añadir mensaje de bienvenida
            welcome_msg = self._get_welcome_message()
            self._add_message_to_history(estado_bot, "assistant", welcome_msg)
            
            logger.info(f"Nuevo usuario creado: {user_id}")
        
        return estado_bot
    
    def _add_message_to_history(self, estado_bot: EstadoBot, role: str, content: str):
        """
        Añade un mensaje al historial de forma segura
        
        Args:
            estado_bot: Estado del bot
            role: Rol del mensaje ('user' o 'assistant')
            content: Contenido del mensaje
        """
        try:
            estado_bot.mensajes.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "platform": "whatsapp"
            })
        except Exception as e:
            logger.error(f"Error añadiendo mensaje al historial: {str(e)}")
    
    def _detect_special_intention(self, message: str) -> Optional[str]:
        """
        Detecta intenciones especiales en el mensaje
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Intención detectada o None
        """
        message_lower = message.lower().strip()
        
        # Intenciones de control
        if any(word in message_lower for word in ["help", "ayuda", "menu", "menú"]):
            return "help"
        elif any(word in message_lower for word in ["reiniciar", "restart", "empezar de nuevo"]):
            return "restart"
        elif any(word in message_lower for word in ["stop", "parar", "cancelar", "salir"]):
            return "stop"
        elif any(word in message_lower for word in ["hola", "hi", "hello", "buenas", "buenos días"]):
            return "greeting"
        
        return None
    
    def _handle_special_intention(self, intention: str, estado_bot: EstadoBot) -> Dict[str, Any]:
        """
        Maneja intenciones especiales
        
        Args:
            intention: Intención detectada
            estado_bot: Estado del bot
            
        Returns:
            Dict con respuesta
        """
        try:
            if intention == "help":
                message = self._get_help_message()
            elif intention == "restart":
                # Reiniciar estado del usuario
                estado_bot.etapa = EstadoConversacion.INICIO
                estado_bot.mensajes = []
                estado_bot.cotizaciones = []
                estado_bot.next_agent = "needs_based_selling"
                estado_bot.agente_activo = "orquestador"
                message = "¡Perfecto! Empezamos de nuevo. " + self._get_welcome_message()
            elif intention == "stop":
                message = "Gracias por contactar con iAgente_Vida. Si necesitas ayuda con seguros de vida, no dudes en escribirnos. ¡Hasta pronto!"
            elif intention == "greeting":
                message = self._get_welcome_message()
            else:
                message = "¿En qué puedo ayudarte?"
            
            self._add_message_to_history(estado_bot, "assistant", message)
            
            return {
                "success": True,
                "message": message,
                "state": estado_bot
            }
            
        except Exception as e:
            logger.error(f"Error manejando intención especial: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_with_multiagent_system(self, estado_bot: EstadoBot) -> Dict[str, Any]:
        """
        Procesa el mensaje con el sistema multiagente
        
        Args:
            estado_bot: Estado del bot
            
        Returns:
            Dict con resultado
        """
        try:
            # Procesar con el grafo
            resultado = self.grafo.invoke(estado_bot)
            
            # Obtener respuesta del sistema
            response_message = ""
            if hasattr(resultado, 'mensajes') and resultado.mensajes:
                ultimo_mensaje = resultado.mensajes[-1]
                if ultimo_mensaje.get("role") == "assistant":
                    response_message = ultimo_mensaje.get("content", "")
            
            # Si no hay respuesta específica, usar genérica
            if not response_message:
                response_message = "Gracias por tu mensaje. ¿En qué más puedo ayudarte con tu seguro de vida?"
            
            # Adaptar mensaje para WhatsApp
            response_message = self._adapt_message_for_whatsapp(response_message)
            
            return {
                "success": True,
                "message": response_message,
                "state": resultado
            }
            
        except Exception as e:
            logger.error(f"Error procesando con sistema multiagente: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _send_response(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía respuesta al usuario
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
            
        Returns:
            Dict con resultado
        """
        try:
            # Dividir mensaje si es muy largo
            if len(message) > self.max_message_length:
                messages = self._split_message(message)
                
                # Enviar cada parte
                for i, part in enumerate(messages):
                    result = self.woztell_client.send_text_message(user_id, part)
                    if not result["success"]:
                        return result
                    
                    # Pequeña pausa entre mensajes
                    if i < len(messages) - 1:
                        import time
                        time.sleep(1)
                
                return {"success": True, "parts_sent": len(messages)}
            else:
                return self.woztell_client.send_text_message(user_id, message)
                
        except Exception as e:
            logger.error(f"Error enviando respuesta: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _adapt_message_for_whatsapp(self, message: str) -> str:
        """
        Adapta un mensaje para WhatsApp
        
        Args:
            message: Mensaje original
            
        Returns:
            Mensaje adaptado
        """
        # Convertir markdown básico a WhatsApp
        message = message.replace("**", "*")  # Bold
        message = message.replace("__", "_")  # Italic
        
        # Límite de caracteres
        if len(message) > self.max_message_length:
            message = message[:self.max_message_length-3] + "..."
        
        return message
    
    def _split_message(self, message: str) -> list:
        """
        Divide un mensaje largo en partes más pequeñas
        
        Args:
            message: Mensaje largo
            
        Returns:
            Lista de partes del mensaje
        """
        parts = []
        current_part = ""
        
        for sentence in message.split(". "):
            if len(current_part + sentence + ". ") <= self.max_message_length:
                current_part += sentence + ". "
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = sentence + ". "
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts
    
    def _get_welcome_message(self) -> str:
        """
        Obtiene mensaje de bienvenida
        
        Returns:
            Mensaje de bienvenida
        """
        return """¡Hola! Soy *iAgente_Vida* 🤖

Tu asistente especializado en seguros de vida.

Puedo ayudarte con:
• Analizar tus necesidades de protección
• Calcular la cobertura ideal para tu familia
• Generar cotizaciones personalizadas
• Comparar diferentes productos

¿En qué puedo ayudarte hoy?"""
    
    def _get_help_message(self) -> str:
        """
        Obtiene mensaje de ayuda
        
        Returns:
            Mensaje de ayuda
        """
        return """*Comandos disponibles:*

• Escribe tu consulta normalmente
• *help* - Mostrar esta ayuda
• *reiniciar* - Empezar de nuevo
• *stop* - Finalizar conversación

*Ejemplos de consultas:*
• "Quiero un seguro de vida"
• "¿Cuánto debería asegurarme?"
• "Necesito cotizaciones"
• "Tengo 2 hijos, ¿qué me recomiendas?"

¿En qué puedo ayudarte?"""

# Instancia global del adaptador
whatsapp_adapter = WhatsAppAdapter()