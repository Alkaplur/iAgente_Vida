"""
Cliente API para Woztell - Integración con WhatsApp
"""

import os
import requests
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class WoztellMessage:
    """Estructura para mensajes de Woztell"""
    from_number: str
    to_number: str
    message_type: str
    content: str
    timestamp: datetime
    message_id: Optional[str] = None

class WoztellClient:
    """Cliente para la API de Woztell"""
    
    def __init__(self, business_token: str = None):
        """
        Inicializa el cliente de Woztell
        
        Args:
            business_token: Token de negocio de Woztell
        """
        self.business_token = business_token or os.getenv("WOZTELL_BUSINESS_TOKEN")
        self.base_url = "https://api.woztell.com/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.business_token}"
        }
        
        if not self.business_token:
            raise ValueError("WOZTELL_BUSINESS_TOKEN no está configurado")
    
    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje de texto a través de Woztell
        
        Args:
            to_number: Número de teléfono destino (sin + ni espacios)
            message: Texto del mensaje
            
        Returns:
            Dict con la respuesta de la API
        """
        try:
            # Limpiar número de teléfono
            clean_number = self._clean_phone_number(to_number)
            
            payload = {
                "to": clean_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Mensaje enviado exitosamente a {clean_number}")
                return {
                    "success": True,
                    "data": result,
                    "message_id": result.get("id"),
                    "status": "sent"
                }
            else:
                logger.error(f"Error enviando mensaje: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Excepción enviando mensaje: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    def send_template_message(self, to_number: str, template_name: str, 
                            template_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Envía un mensaje de plantilla a través de Woztell
        
        Args:
            to_number: Número de teléfono destino
            template_name: Nombre de la plantilla
            template_params: Parámetros de la plantilla
            
        Returns:
            Dict con la respuesta de la API
        """
        try:
            clean_number = self._clean_phone_number(to_number)
            
            payload = {
                "to": clean_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "es"},
                    "components": []
                }
            }
            
            # Añadir parámetros si existen
            if template_params:
                payload["template"]["components"].append({
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(value)} 
                        for value in template_params.values()
                    ]
                })
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Plantilla enviada exitosamente a {clean_number}")
                return {
                    "success": True,
                    "data": result,
                    "message_id": result.get("id"),
                    "status": "sent"
                }
            else:
                logger.error(f"Error enviando plantilla: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Excepción enviando plantilla: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    def parse_incoming_message(self, webhook_data: Dict[str, Any]) -> Optional[WoztellMessage]:
        """
        Parsea un mensaje entrante desde el webhook de Woztell
        
        Args:
            webhook_data: Datos del webhook
            
        Returns:
            WoztellMessage o None si no se puede parsear
        """
        try:
            # Verificar estructura básica
            if "from" not in webhook_data or "message" not in webhook_data:
                logger.warning("Estructura de webhook inválida")
                return None
            
            from_number = webhook_data["from"]
            message_data = webhook_data["message"]
            
            # Obtener tipo y contenido del mensaje
            message_type = message_data.get("type", "unknown")
            content = ""
            
            if message_type == "text":
                content = message_data.get("text", "")
            elif message_type == "image":
                content = message_data.get("caption", "[Imagen]")
            elif message_type == "document":
                content = message_data.get("caption", "[Documento]")
            elif message_type == "audio":
                content = "[Audio]"
            elif message_type == "video":
                content = message_data.get("caption", "[Video]")
            else:
                content = f"[{message_type}]"
            
            return WoztellMessage(
                from_number=from_number,
                to_number=webhook_data.get("to", ""),
                message_type=message_type,
                content=content,
                timestamp=datetime.now(),
                message_id=webhook_data.get("id")
            )
            
        except Exception as e:
            logger.error(f"Error parseando mensaje entrante: {str(e)}")
            return None
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """
        Limpia un número de teléfono para el formato requerido por Woztell
        
        Args:
            phone_number: Número de teléfono raw
            
        Returns:
            Número limpio (solo dígitos)
        """
        # Remover todos los caracteres no numéricos
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Si no empieza con código de país, asumir España (+34)
        if len(clean_number) == 9 and clean_number.startswith(('6', '7', '8', '9')):
            clean_number = "34" + clean_number
        
        return clean_number
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un mensaje enviado
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            Dict con el estado del mensaje
        """
        try:
            response = requests.get(
                f"{self.base_url}/messages/{message_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estado del mensaje: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Valida la firma del webhook (opcional, según configuración de Woztell)
        
        Args:
            payload: Payload del webhook
            signature: Firma recibida
            secret: Secreto configurado
            
        Returns:
            True si la firma es válida
        """
        try:
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validando firma: {str(e)}")
            return False

# Funciones de conveniencia
def send_whatsapp_message(to_number: str, message: str) -> Dict[str, Any]:
    """
    Función de conveniencia para enviar un mensaje de WhatsApp
    
    Args:
        to_number: Número de teléfono destino
        message: Mensaje a enviar
        
    Returns:
        Dict con el resultado
    """
    client = WoztellClient()
    return client.send_text_message(to_number, message)

def parse_whatsapp_webhook(webhook_data: Dict[str, Any]) -> Optional[WoztellMessage]:
    """
    Función de conveniencia para parsear webhooks de WhatsApp
    
    Args:
        webhook_data: Datos del webhook
        
    Returns:
        WoztellMessage o None
    """
    client = WoztellClient()
    return client.parse_incoming_message(webhook_data)