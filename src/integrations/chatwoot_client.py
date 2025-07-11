"""
Cliente Chatwoot para seguimiento de conversaciones
Integra con WhatsApp para trazabilidad completa
"""
import requests
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

try:
    from ..config import settings
    from .whatsapp_client import WhatsAppMessage
except ImportError:
    from config import settings
    from integrations.whatsapp_client import WhatsAppMessage


@dataclass
class ChatwootContact:
    """Contacto en Chatwoot"""
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None
    custom_attributes: Dict[str, Any] = None


@dataclass
class ChatwootConversation:
    """Conversación en Chatwoot"""
    id: int
    contact_id: int
    inbox_id: int
    status: str  # open, resolved, pending
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None
    labels: List[str] = None
    custom_attributes: Dict[str, Any] = None


@dataclass
class ChatwootMessage:
    """Mensaje en Chatwoot"""
    id: int
    conversation_id: int
    message_type: str  # incoming, outgoing
    content: str
    created_at: datetime
    sender_type: str  # contact, user, agent_bot
    attachments: List[Dict[str, Any]] = None


class ChatwootClient:
    """Cliente para Chatwoot API"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'chatwoot_base_url', 'https://app.chatwoot.com')
        self.account_id = getattr(settings, 'chatwoot_account_id', None)
        self.user_token = getattr(settings, 'chatwoot_user_token', None)
        self.platform_token = getattr(settings, 'chatwoot_platform_token', None)
        self.inbox_id = getattr(settings, 'chatwoot_whatsapp_inbox_id', None)
        
        if not all([self.base_url, self.account_id, self.user_token]):
            logging.warning("⚠️ Chatwoot credentials not fully configured")
    
    def _get_headers(self, use_platform_token: bool = False) -> Dict[str, str]:
        """Obtiene headers para API"""
        token = self.platform_token if use_platform_token else self.user_token
        return {
            "api_access_token": token,
            "Content-Type": "application/json"
        }
    
    def create_contact(self, phone_number: str, name: str, 
                      custom_attributes: Dict[str, Any] = None) -> Optional[ChatwootContact]:
        """
        Crea o actualiza contacto en Chatwoot
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts"
        
        payload = {
            "name": name,
            "phone_number": phone_number,
            "custom_attributes": custom_attributes or {}
        }
        
        try:
            # Primero intentar buscar contacto existente
            existing_contact = self.get_contact_by_phone(phone_number)
            if existing_contact:
                # Actualizar contacto existente
                return self.update_contact(existing_contact.id, name, custom_attributes)
            
            # Crear nuevo contacto
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            contact_data = response.json()
            logging.info(f"✅ Contact created: {name} ({phone_number})")
            
            return ChatwootContact(
                id=contact_data["id"],
                name=contact_data["name"],
                phone_number=contact_data["phone_number"],
                email=contact_data.get("email"),
                custom_attributes=contact_data.get("custom_attributes", {})
            )
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error creating contact: {e}")
            return None
    
    def get_contact_by_phone(self, phone_number: str) -> Optional[ChatwootContact]:
        """
        Busca contacto por número de teléfono
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/search"
        
        params = {"q": phone_number}
        
        try:
            response = requests.get(
                url, 
                headers=self._get_headers(), 
                params=params
            )
            response.raise_for_status()
            
            contacts = response.json()
            for contact in contacts:
                if contact.get("phone_number") == phone_number:
                    return ChatwootContact(
                        id=contact["id"],
                        name=contact["name"],
                        phone_number=contact["phone_number"],
                        email=contact.get("email"),
                        custom_attributes=contact.get("custom_attributes", {})
                    )
            
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error searching contact: {e}")
            return None
    
    def update_contact(self, contact_id: int, name: str = None,
                      custom_attributes: Dict[str, Any] = None) -> Optional[ChatwootContact]:
        """
        Actualiza contacto existente
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/{contact_id}"
        
        payload = {}
        if name:
            payload["name"] = name
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes
        
        try:
            response = requests.patch(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            contact_data = response.json()
            logging.info(f"✅ Contact updated: {contact_id}")
            
            return ChatwootContact(
                id=contact_data["id"],
                name=contact_data["name"],
                phone_number=contact_data["phone_number"],
                email=contact_data.get("email"),
                custom_attributes=contact_data.get("custom_attributes", {})
            )
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error updating contact: {e}")
            return None
    
    def create_conversation(self, contact_id: int, 
                          initial_message: str = None) -> Optional[ChatwootConversation]:
        """
        Crea nueva conversación
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"
        
        payload = {
            "contact_id": contact_id,
            "inbox_id": self.inbox_id,
        }
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            conv_data = response.json()
            conversation = ChatwootConversation(
                id=conv_data["id"],
                contact_id=conv_data["meta"]["contact"]["id"],
                inbox_id=conv_data["inbox_id"],
                status=conv_data["status"],
                assignee_id=conv_data.get("assignee", {}).get("id"),
                team_id=conv_data.get("team", {}).get("id"),
                labels=conv_data.get("labels", []),
                custom_attributes=conv_data.get("custom_attributes", {})
            )
            
            logging.info(f"✅ Conversation created: {conversation.id}")
            
            # Enviar mensaje inicial si se proporciona
            if initial_message:
                self.send_message(conversation.id, initial_message, "incoming")
            
            return conversation
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error creating conversation: {e}")
            return None
    
    def get_conversations_by_contact(self, contact_id: int) -> List[ChatwootConversation]:
        """
        Obtiene conversaciones de un contacto
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"
        
        params = {"contact_id": contact_id}
        
        try:
            response = requests.get(
                url, 
                headers=self._get_headers(), 
                params=params
            )
            response.raise_for_status()
            
            conversations_data = response.json()
            conversations = []
            
            for conv_data in conversations_data["data"]:
                conversations.append(ChatwootConversation(
                    id=conv_data["id"],
                    contact_id=conv_data["meta"]["contact"]["id"],
                    inbox_id=conv_data["inbox_id"],
                    status=conv_data["status"],
                    assignee_id=conv_data.get("assignee", {}).get("id"),
                    team_id=conv_data.get("team", {}).get("id"),
                    labels=conv_data.get("labels", []),
                    custom_attributes=conv_data.get("custom_attributes", {})
                ))
            
            return conversations
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error getting conversations: {e}")
            return []
    
    def send_message(self, conversation_id: int, content: str, 
                    message_type: str = "outgoing") -> Optional[ChatwootMessage]:
        """
        Envía mensaje a conversación
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        
        payload = {
            "content": content,
            "message_type": message_type,
            "private": False
        }
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            msg_data = response.json()
            message = ChatwootMessage(
                id=msg_data["id"],
                conversation_id=msg_data["conversation_id"],
                message_type=msg_data["message_type"],
                content=msg_data["content"],
                created_at=datetime.fromisoformat(msg_data["created_at"].replace('Z', '+00:00')),
                sender_type=msg_data.get("sender_type", "agent_bot"),
                attachments=msg_data.get("attachments", [])
            )
            
            logging.info(f"✅ Message sent to conversation {conversation_id}")
            return message
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error sending message: {e}")
            return None
    
    def add_labels(self, conversation_id: int, labels: List[str]) -> bool:
        """
        Añade etiquetas a conversación
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/labels"
        
        payload = {"labels": labels}
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            logging.info(f"✅ Labels added to conversation {conversation_id}: {labels}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error adding labels: {e}")
            return False
    
    def update_conversation_status(self, conversation_id: int, status: str) -> bool:
        """
        Actualiza estado de conversación (open, resolved, pending)
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/toggle_status"
        
        payload = {"status": status}
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            logging.info(f"✅ Conversation {conversation_id} status updated to {status}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error updating conversation status: {e}")
            return False
    
    def assign_conversation(self, conversation_id: int, assignee_id: int) -> bool:
        """
        Asigna conversación a agente
        """
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/assignments"
        
        payload = {"assignee_id": assignee_id}
        
        try:
            response = requests.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            )
            response.raise_for_status()
            
            logging.info(f"✅ Conversation {conversation_id} assigned to {assignee_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error assigning conversation: {e}")
            return False


# Singleton instance
chatwoot_client = ChatwootClient()


def sync_whatsapp_to_chatwoot(whatsapp_msg: WhatsAppMessage) -> Optional[ChatwootConversation]:
    """
    Sincroniza mensaje de WhatsApp con Chatwoot
    """
    try:
        # 1. Crear o buscar contacto
        contact = chatwoot_client.create_contact(
            phone_number=whatsapp_msg.from_number,
            name=whatsapp_msg.contact_name or f"Cliente {whatsapp_msg.from_number[-4:]}",
            custom_attributes={
                "whatsapp_number": whatsapp_msg.from_number,
                "last_message_type": whatsapp_msg.message_type,
                "source": "whatsapp_iagente_vida"
            }
        )
        
        if not contact:
            logging.error("❌ Failed to create/find contact")
            return None
        
        # 2. Buscar conversación abierta o crear nueva
        conversations = chatwoot_client.get_conversations_by_contact(contact.id)
        active_conversation = None
        
        for conv in conversations:
            if conv.status in ["open", "pending"]:
                active_conversation = conv
                break
        
        if not active_conversation:
            active_conversation = chatwoot_client.create_conversation(
                contact_id=contact.id,
                initial_message=whatsapp_msg.content
            )
        else:
            # Enviar mensaje a conversación existente
            chatwoot_client.send_message(
                conversation_id=active_conversation.id,
                content=whatsapp_msg.content,
                message_type="incoming"
            )
        
        # 3. Añadir etiquetas según tipo de mensaje
        labels = ["whatsapp", "iagente_vida"]
        if whatsapp_msg.message_type != "text":
            labels.append(f"media_{whatsapp_msg.message_type}")
        
        chatwoot_client.add_labels(active_conversation.id, labels)
        
        logging.info(f"✅ WhatsApp message synced to Chatwoot conversation {active_conversation.id}")
        return active_conversation
        
    except Exception as e:
        logging.error(f"❌ Error syncing WhatsApp to Chatwoot: {e}")
        return None


def send_agent_response_to_chatwoot(conversation_id: int, response: str, 
                                  client_data: Dict[str, Any] = None) -> bool:
    """
    Envía respuesta del agente iAgente_Vida a Chatwoot
    """
    try:
        # Formatear respuesta con contexto del cliente
        formatted_response = f"🤖 **iAgente_Vida**\n\n{response}"
        
        if client_data:
            client_info = f"\n\n📊 **Datos del cliente:**"
            if client_data.get("nombre"):
                client_info += f"\n• Nombre: {client_data['nombre']}"
            if client_data.get("edad"):
                client_info += f"\n• Edad: {client_data['edad']} años"
            if client_data.get("num_dependientes"):
                client_info += f"\n• Dependientes: {client_data['num_dependientes']}"
            if client_data.get("ingresos_mensuales"):
                client_info += f"\n• Ingresos: €{client_data['ingresos_mensuales']}/mes"
            
            formatted_response += client_info
        
        # Enviar mensaje
        result = chatwoot_client.send_message(
            conversation_id=conversation_id,
            content=formatted_response,
            message_type="outgoing"
        )
        
        return result is not None
        
    except Exception as e:
        logging.error(f"❌ Error sending agent response to Chatwoot: {e}")
        return False


def create_lead_in_chatwoot(phone_number: str, name: str, 
                          lead_data: Dict[str, Any]) -> Optional[ChatwootContact]:
    """
    Crea lead en Chatwoot con datos del cliente potencial
    """
    custom_attributes = {
        "lead_source": "whatsapp_iagente_vida",
        "lead_status": "new",
        "created_via": "ai_agent",
        **lead_data
    }
    
    contact = chatwoot_client.create_contact(
        phone_number=phone_number,
        name=name,
        custom_attributes=custom_attributes
    )
    
    if contact:
        # Crear conversación inicial con información del lead
        conv = chatwoot_client.create_conversation(
            contact_id=contact.id,
            initial_message=f"💡 **Nuevo lead generado por iAgente_Vida**\n\nDatos recopilados:\n{format_lead_data(lead_data)}"
        )
        
        if conv:
            # Añadir etiquetas de lead
            chatwoot_client.add_labels(conv.id, ["lead", "new_prospect", "iagente_vida"])
        
    return contact


def format_lead_data(data: Dict[str, Any]) -> str:
    """
    Formatea datos del lead para mostrar en Chatwoot
    """
    formatted = ""
    if data.get("edad"):
        formatted += f"• Edad: {data['edad']} años\n"
    if data.get("num_dependientes"):
        formatted += f"• Dependientes: {data['num_dependientes']}\n"
    if data.get("ingresos_mensuales"):
        formatted += f"• Ingresos: €{data['ingresos_mensuales']}/mes\n"
    if data.get("profesion"):
        formatted += f"• Profesión: {data['profesion']}\n"
    if data.get("interes_producto"):
        formatted += f"• Interés: {data['interes_producto']}\n"
    
    return formatted