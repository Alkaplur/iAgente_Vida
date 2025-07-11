"""
Cliente WhatsApp Business API para iAgente_Vida
Maneja envío/recepción de mensajes y webhooks
"""
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

try:
    from ..config import settings
    from ..models import Cliente, EstadoBot
except ImportError:
    from config import settings
    from models import Cliente, EstadoBot


@dataclass
class WhatsAppMessage:
    """Estructura de mensaje WhatsApp"""
    message_id: str
    from_number: str
    to_number: str
    message_type: str  # text, image, audio, document
    content: str
    timestamp: datetime
    contact_name: Optional[str] = None
    media_url: Optional[str] = None
    media_mime_type: Optional[str] = None


@dataclass
class WhatsAppContact:
    """Información de contacto WhatsApp"""
    phone_number: str
    name: Optional[str] = None
    profile_name: Optional[str] = None
    
    
class WhatsAppClient:
    """Cliente para WhatsApp Business API"""
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v19.0"
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_token
        self.verify_token = settings.whatsapp_verify_token
        
        if not all([self.phone_number_id, self.access_token, self.verify_token]):
            logging.warning("⚠️ WhatsApp credentials not fully configured")
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica webhook de WhatsApp
        """
        if mode == "subscribe" and token == self.verify_token:
            logging.info("✅ WhatsApp webhook verified")
            return challenge
        else:
            logging.warning("❌ WhatsApp webhook verification failed")
            return None
    
    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Envía mensaje de texto
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"✅ Message sent to {to_number}: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error sending message to {to_number}: {e}")
            return {"error": str(e)}
    
    def send_template_message(self, to_number: str, template_name: str, 
                            language_code: str = "es", 
                            parameters: List[str] = None) -> Dict[str, Any]:
        """
        Envía mensaje con plantilla aprobada
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Construir componentes de la plantilla
        components = []
        if parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": components
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"✅ Template sent to {to_number}: {template_name}")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error sending template to {to_number}: {e}")
            return {"error": str(e)}
    
    def send_interactive_message(self, to_number: str, header_text: str, 
                               body_text: str, footer_text: str,
                               buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Envía mensaje interactivo con botones
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Construir botones (máximo 3)
        interactive_buttons = []
        for i, button in enumerate(buttons[:3]):
            interactive_buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i+1}",
                    "title": button.get("title", f"Opción {i+1}")
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": header_text
                },
                "body": {
                    "text": body_text
                },
                "footer": {
                    "text": footer_text
                },
                "action": {
                    "buttons": interactive_buttons
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"✅ Interactive message sent to {to_number}")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error sending interactive message to {to_number}: {e}")
            return {"error": str(e)}
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Parsea mensaje recibido del webhook
        """
        try:
            # Estructura típica del webhook de WhatsApp
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Extraer mensajes
            messages = value.get("messages", [])
            if not messages:
                return None
                
            message = messages[0]
            contacts = value.get("contacts", [{}])
            contact = contacts[0] if contacts else {}
            
            # Extraer información del mensaje
            message_id = message.get("id")
            from_number = message.get("from")
            message_type = message.get("type")
            timestamp = datetime.fromtimestamp(int(message.get("timestamp")))
            
            # Extraer contenido según tipo
            content = ""
            media_url = None
            media_mime_type = None
            
            if message_type == "text":
                content = message.get("text", {}).get("body", "")
            elif message_type == "image":
                image_data = message.get("image", {})
                content = image_data.get("caption", "[Imagen]")
                media_url = image_data.get("id")  # Se usa para descargar
                media_mime_type = image_data.get("mime_type")
            elif message_type == "audio":
                audio_data = message.get("audio", {})
                content = "[Audio]"
                media_url = audio_data.get("id")
                media_mime_type = audio_data.get("mime_type")
            elif message_type == "document":
                doc_data = message.get("document", {})
                content = f"[Documento: {doc_data.get('filename', 'Sin nombre')}]"
                media_url = doc_data.get("id")
                media_mime_type = doc_data.get("mime_type")
            
            # Información del contacto
            contact_name = contact.get("profile", {}).get("name")
            
            return WhatsAppMessage(
                message_id=message_id,
                from_number=from_number,
                to_number=self.phone_number_id,
                message_type=message_type,
                content=content,
                timestamp=timestamp,
                contact_name=contact_name,
                media_url=media_url,
                media_mime_type=media_mime_type
            )
            
        except Exception as e:
            logging.error(f"❌ Error parsing webhook message: {e}")
            return None
    
    def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Descarga archivo multimedia
        """
        try:
            # Primero obtener URL del archivo
            url = f"{self.base_url}/{media_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            media_info = response.json()
            download_url = media_info.get("url")
            
            if not download_url:
                return None
            
            # Descargar el archivo
            download_response = requests.get(download_url, headers=headers)
            download_response.raise_for_status()
            
            return download_response.content
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error downloading media {media_id}: {e}")
            return None
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Marca mensaje como leído
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error marking message as read: {e}")
            return False


# Singleton instance
whatsapp_client = WhatsAppClient()


def format_message_for_whatsapp(message: str) -> str:
    """
    Formatea mensaje para WhatsApp (límites, emojis, etc.)
    """
    # WhatsApp tiene límite de 4096 caracteres para mensajes de texto
    if len(message) > 4000:
        message = message[:3997] + "..."
    
    # Asegurar que hay saltos de línea apropiados
    message = message.replace("\\n", "\n")
    
    return message


def extract_phone_number(text: str) -> Optional[str]:
    """
    Extrae número de teléfono de texto
    """
    import re
    
    # Patrones comunes para números de teléfono
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # Internacional
        r'\+?\d{10,15}',  # Número simple
        r'\(\d{3}\)\s?\d{3}-?\d{4}'  # Formato (123) 456-7890
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Limpiar el número
            phone = re.sub(r'[^\d+]', '', match.group())
            if len(phone) >= 10:
                return phone
    
    return None