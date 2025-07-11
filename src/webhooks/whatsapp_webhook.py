"""
Webhook para recibir mensajes de WhatsApp Business API
Procesa mensajes entrantes y los dirige al sistema iAgente_Vida
"""
from flask import Flask, request, jsonify
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from ..integrations.whatsapp_client import whatsapp_client, WhatsAppMessage
    from ..integrations.chatwoot_client import sync_whatsapp_to_chatwoot, send_agent_response_to_chatwoot
    from ..graph import process_message
    from ..models import EstadoBot, EstadoConversacion, Cliente, ContextoConversacional
    from ..config import settings
except ImportError:
    from integrations.whatsapp_client import whatsapp_client, WhatsAppMessage
    from integrations.chatwoot_client import sync_whatsapp_to_chatwoot, send_agent_response_to_chatwoot
    from graph import process_message
    from models import EstadoBot, EstadoConversacion, Cliente, ContextoConversacional
    from config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store para mantener estado de conversaciones por número de teléfono
conversation_store: Dict[str, EstadoBot] = {}


@app.route("/webhook/whatsapp", methods=["GET", "POST"])
def whatsapp_webhook():
    """Endpoint principal del webhook de WhatsApp"""
    
    if request.method == "GET":
        return verify_webhook()
    elif request.method == "POST":
        return handle_incoming_message()


def verify_webhook():
    """Verifica el webhook de WhatsApp (desafío inicial de Meta)"""
    try:
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        logger.info(f"🔐 Verificación webhook: mode={mode}, token={token}")
        
        # Verificar con el cliente WhatsApp
        verified_challenge = whatsapp_client.verify_webhook(mode, token, challenge)
        
        if verified_challenge:
            logger.info("✅ Webhook verificado exitosamente")
            return verified_challenge, 200
        else:
            logger.error("❌ Verificación de webhook fallida")
            return "Forbidden", 403
            
    except Exception as e:
        logger.error(f"❌ Error en verificación webhook: {e}")
        return "Internal Server Error", 500


def handle_incoming_message():
    """Procesa mensajes entrantes de WhatsApp"""
    try:
        # Obtener datos del webhook
        webhook_data = request.get_json()
        logger.info(f"📨 Webhook recibido: {json.dumps(webhook_data, indent=2)}")
        
        # Parsear mensaje de WhatsApp
        whatsapp_message = whatsapp_client.parse_webhook_message(webhook_data)
        
        if not whatsapp_message:
            logger.warning("⚠️ No se pudo parsear mensaje de WhatsApp")
            return jsonify({"status": "no_message"}), 200
        
        logger.info(f"📱 Mensaje procesado: {whatsapp_message.from_number} -> {whatsapp_message.content}")
        
        # Marcar mensaje como leído
        whatsapp_client.mark_as_read(whatsapp_message.message_id)
        
        # Sincronizar con Chatwoot para seguimiento
        chatwoot_conversation = sync_whatsapp_to_chatwoot(whatsapp_message)
        
        # Procesar mensaje con iAgente_Vida
        agent_response = process_whatsapp_message(whatsapp_message)
        
        if agent_response:
            # Enviar respuesta por WhatsApp
            send_result = whatsapp_client.send_text_message(
                to_number=whatsapp_message.from_number,
                message=agent_response
            )
            
            # Sincronizar respuesta con Chatwoot
            if chatwoot_conversation:
                send_agent_response_to_chatwoot(
                    conversation_id=chatwoot_conversation.id,
                    response=agent_response,
                    client_data=get_client_data_from_store(whatsapp_message.from_number)
                )
            
            logger.info(f"✅ Respuesta enviada: {send_result.get('messages', [{}])[0].get('id', 'unknown')}")
        
        return jsonify({"status": "processed"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}")
        return jsonify({"error": str(e)}), 500


def process_whatsapp_message(whatsapp_msg: WhatsAppMessage) -> Optional[str]:
    """
    Procesa mensaje de WhatsApp con el sistema iAgente_Vida
    Mantiene estado persistente por número de teléfono
    """
    try:
        phone_number = whatsapp_msg.from_number
        
        # Obtener o crear estado de conversación
        estado = get_or_create_conversation_state(phone_number, whatsapp_msg)
        
        # Actualizar mensaje del usuario
        estado.mensaje_usuario = whatsapp_msg.content
        
        # Agregar al historial
        estado.mensajes.append({
            "role": "user",
            "content": whatsapp_msg.content,
            "timestamp": whatsapp_msg.timestamp.isoformat(),
            "platform": "whatsapp"
        })
        
        logger.info(f"🤖 Procesando con iAgente_Vida: {phone_number}")
        
        # Procesar con el grafo de agentes
        result = process_message(estado)
        
        # Actualizar estado en store
        conversation_store[phone_number] = result
        
        # Extraer respuesta del agente
        if result.mensajes and len(result.mensajes) > 0:
            last_message = result.mensajes[-1]
            if last_message.get("role") == "assistant":
                return format_response_for_whatsapp(last_message.get("content", ""))
        
        return "Lo siento, hubo un problema procesando tu mensaje. ¿Puedes intentar de nuevo?"
        
    except Exception as e:
        logger.error(f"❌ Error en process_whatsapp_message: {e}")
        return "Disculpa, hay un problema técnico. Inténtalo más tarde."


def get_or_create_conversation_state(phone_number: str, whatsapp_msg: WhatsAppMessage) -> EstadoBot:
    """
    Obtiene estado existente o crea uno nuevo para el número de teléfono
    """
    if phone_number in conversation_store:
        logger.info(f"📋 Estado existente recuperado para {phone_number}")
        return conversation_store[phone_number]
    
    # Crear nuevo estado
    logger.info(f"🆕 Creando nuevo estado para {phone_number}")
    
    cliente = Cliente(
        nombre=whatsapp_msg.contact_name or f"Cliente {phone_number[-4:]}",
        telefono=phone_number
    )
    
    contexto = ContextoConversacional(
        plataforma="whatsapp",
        canal_origen="whatsapp_business",
        timestamp_inicio=datetime.now(),
        preferencias_contacto={"whatsapp": True},
        historial_interacciones=[]
    )
    
    estado = EstadoBot(
        cliente=cliente,
        etapa=EstadoConversacion.INICIO,
        contexto=contexto,
        mensaje_usuario="",
        mensajes=[],
        cotizaciones=[],
        recomendacion_producto=None,
        next_agent="needs_based_selling",
        agente_activo="orquestador"
    )
    
    conversation_store[phone_number] = estado
    return estado


def format_response_for_whatsapp(response: str) -> str:
    """
    Formatea la respuesta del agente para WhatsApp
    Aplica límites de caracteres y formato apropiado
    """
    # Usar el formateador del cliente WhatsApp
    from integrations.whatsapp_client import format_message_for_whatsapp
    return format_message_for_whatsapp(response)


def get_client_data_from_store(phone_number: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene datos del cliente desde el store para Chatwoot
    """
    if phone_number in conversation_store:
        cliente = conversation_store[phone_number].cliente
        return {
            "nombre": cliente.nombre,
            "edad": cliente.edad,
            "num_dependientes": cliente.num_dependientes,
            "ingresos_mensuales": cliente.ingresos_mensuales,
            "profesion": cliente.profesion,
            "telefono": cliente.telefono
        }
    return None


@app.route("/webhook/status", methods=["GET"])
def webhook_status():
    """Endpoint para verificar estado del webhook"""
    return jsonify({
        "status": "active",
        "active_conversations": len(conversation_store),
        "webhook_url": request.url_root + "webhook/whatsapp",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/webhook/conversations", methods=["GET"])
def list_conversations():
    """Lista conversaciones activas (para debugging)"""
    conversations = {}
    for phone, estado in conversation_store.items():
        conversations[phone] = {
            "cliente_nombre": estado.cliente.nombre,
            "etapa": estado.etapa.value if estado.etapa else "unknown",
            "mensajes_count": len(estado.mensajes),
            "ultimo_agente": estado.agente_activo,
            "tiene_cotizaciones": len(estado.cotizaciones) > 0,
            "tiene_recomendacion": estado.recomendacion_producto is not None
        }
    
    return jsonify({
        "total_conversations": len(conversations),
        "conversations": conversations
    })


@app.route("/webhook/conversation/<phone_number>", methods=["DELETE"])
def reset_conversation(phone_number: str):
    """Reinicia conversación específica (para testing)"""
    if phone_number in conversation_store:
        del conversation_store[phone_number]
        return jsonify({"status": "conversation_reset", "phone": phone_number})
    else:
        return jsonify({"error": "conversation_not_found"}), 404


# Manejador de errores global
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"❌ Error no manejado: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Configuración para desarrollo
    app.run(
        host="0.0.0.0",
        port=getattr(settings, 'webhook_port', 5000),
        debug=getattr(settings, 'debug', False)
    )