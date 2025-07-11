"""
Webhook Flask para recibir mensajes de Woztell (WhatsApp)
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports del proyecto
try:
    from integrations.woztell_client import WoztellClient, parse_whatsapp_webhook
    from graph import crear_grafo
    from models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion
    from utils.state_manager import StateManager
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    # Fallback para desarrollo
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from src.integrations.woztell_client import WoztellClient, parse_whatsapp_webhook
    from src.graph import crear_grafo
    from src.models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion
    from src.utils.state_manager import StateManager

# Configurar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configurar rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Inicializar clientes
woztell_client = WoztellClient()
state_manager = StateManager()

# Cache para evitar procesamiento duplicado
processed_messages = set()

@app.route('/webhook', methods=['POST'])
@limiter.limit("10 per minute")
def whatsapp_webhook():
    """
    Endpoint para recibir mensajes de WhatsApp vía Woztell
    """
    try:
        # Obtener datos del webhook
        webhook_data = request.get_json()
        
        if not webhook_data:
            logger.warning("Webhook recibido sin datos JSON")
            return jsonify({"error": "No JSON data provided"}), 400
        
        logger.info(f"Webhook recibido: {json.dumps(webhook_data, indent=2)}")
        
        # Validar firma del webhook (opcional)
        webhook_secret = os.getenv("WOZTELL_WEBHOOK_SECRET")
        if webhook_secret:
            signature = request.headers.get('X-Woztell-Signature')
            if not signature:
                logger.warning("Webhook sin firma de seguridad")
                return jsonify({"error": "Missing signature"}), 401
            
            payload = request.get_data(as_text=True)
            if not woztell_client.validate_webhook_signature(payload, signature, webhook_secret):
                logger.error("Firma de webhook inválida")
                return jsonify({"error": "Invalid signature"}), 401
        
        # Parsear mensaje entrante
        incoming_message = parse_whatsapp_webhook(webhook_data)
        
        if not incoming_message:
            logger.warning("No se pudo parsear el mensaje entrante")
            return jsonify({"error": "Invalid message format"}), 400
        
        # Verificar si ya procesamos este mensaje
        message_key = f"{incoming_message.from_number}_{incoming_message.message_id}_{incoming_message.timestamp}"
        if message_key in processed_messages:
            logger.info(f"Mensaje ya procesado: {message_key}")
            return jsonify({"status": "already_processed"}), 200
        
        # Marcar mensaje como procesado
        processed_messages.add(message_key)
        
        # Procesar mensaje con el sistema multiagente
        response = process_whatsapp_message(incoming_message)
        
        if response["success"]:
            logger.info(f"Mensaje procesado exitosamente para {incoming_message.from_number}")
            return jsonify({"status": "processed", "response_sent": True}), 200
        else:
            logger.error(f"Error procesando mensaje: {response['error']}")
            return jsonify({"status": "error", "error": response["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def process_whatsapp_message(incoming_message):
    """
    Procesa un mensaje de WhatsApp con el sistema multiagente
    
    Args:
        incoming_message: WoztellMessage entrante
        
    Returns:
        Dict con el resultado del procesamiento
    """
    try:
        # Obtener o crear estado del usuario
        user_id = incoming_message.from_number
        estado_bot = state_manager.get_user_state(user_id)
        
        if not estado_bot:
            # Crear nuevo estado para usuario
            cliente = Cliente(
                nombre="",  # Se completará durante la conversación
                edad=30,
                telefono=incoming_message.from_number,
                estado_civil="soltero",
                profesion="",
                ingresos_mensuales=0.0,
                gastos_fijos_mensuales=0.0,
                num_dependientes=0,
                salud_relevante="no especificado",
                tiene_seguro_vida=False
            )
            
            contexto = ContextoConversacional(
                plataforma="whatsapp",
                canal_origen="woztell",
                timestamp_inicio=datetime.now(),
                numero_telefono=incoming_message.from_number
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
        
        # Añadir mensaje del usuario al historial
        estado_bot.mensaje_usuario = incoming_message.content
        estado_bot.mensajes.append({
            "role": "user",
            "content": incoming_message.content,
            "timestamp": incoming_message.timestamp.isoformat(),
            "platform": "whatsapp"
        })
        
        # Procesar con el sistema multiagente
        logger.info(f"Procesando mensaje: '{incoming_message.content}' del usuario {user_id}")
        
        grafo = crear_grafo()
        resultado = grafo.invoke(estado_bot)
        
        # Guardar estado actualizado
        state_manager.save_user_state(user_id, resultado)
        
        # Obtener última respuesta del sistema
        respuesta_sistema = ""
        if hasattr(resultado, 'mensajes') and resultado.mensajes:
            ultimo_mensaje = resultado.mensajes[-1]
            if ultimo_mensaje.get("role") == "assistant":
                respuesta_sistema = ultimo_mensaje.get("content", "")
        
        # Si no hay respuesta específica, usar respuesta por defecto
        if not respuesta_sistema:
            respuesta_sistema = "Gracias por contactar con iAgente_Vida. ¿En qué puedo ayudarte con tu seguro de vida?"
        
        # Enviar respuesta por WhatsApp
        send_result = woztell_client.send_text_message(
            incoming_message.from_number,
            respuesta_sistema
        )
        
        if send_result["success"]:
            logger.info(f"Respuesta enviada exitosamente a {incoming_message.from_number}")
            return {
                "success": True,
                "message_sent": True,
                "response": respuesta_sistema
            }
        else:
            logger.error(f"Error enviando respuesta: {send_result['error']}")
            return {
                "success": False,
                "error": f"Error enviando respuesta: {send_result['error']}"
            }
            
    except Exception as e:
        logger.error(f"Error procesando mensaje de WhatsApp: {str(e)}")
        
        # Enviar mensaje de error al usuario
        try:
            error_msg = "Disculpa, hubo un problema técnico. Por favor, intenta de nuevo en unos minutos."
            woztell_client.send_text_message(incoming_message.from_number, error_msg)
        except:
            pass
        
        return {
            "success": False,
            "error": str(e)
        }

@app.route('/webhook', methods=['GET'])
def webhook_verification():
    """
    Endpoint para verificación del webhook (si es requerido por Woztell)
    """
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    expected_token = os.getenv('WOZTELL_VERIFY_TOKEN')
    
    if verify_token == expected_token:
        logger.info("Webhook verificado exitosamente")
        return challenge
    else:
        logger.warning("Token de verificación inválido")
        return "Invalid verify token", 403

@app.route('/send_message', methods=['POST'])
@limiter.limit("5 per minute")
def send_message():
    """
    Endpoint para enviar mensajes manualmente (para testing)
    """
    try:
        data = request.get_json()
        
        if not data or 'to' not in data or 'message' not in data:
            return jsonify({"error": "Missing 'to' or 'message' fields"}), 400
        
        result = woztell_client.send_text_message(
            data['to'],
            data['message']
        )
        
        return jsonify(result), 200 if result["success"] else 500
        
    except Exception as e:
        logger.error(f"Error enviando mensaje manual: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de health check
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "iAgente_Vida WhatsApp Webhook"
    }), 200

@app.route('/stats', methods=['GET'])
def stats():
    """
    Endpoint para estadísticas básicas
    """
    return jsonify({
        "processed_messages": len(processed_messages),
        "active_users": state_manager.get_active_users_count(),
        "uptime": "Running",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Manejador para rate limiting
    """
    return jsonify({"error": "Rate limit exceeded", "retry_after": e.retry_after}), 429

@app.errorhandler(500)
def internal_error(e):
    """
    Manejador de errores internos
    """
    logger.error(f"Error interno: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Configuración para desarrollo
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    host = os.getenv('WEBHOOK_HOST', '0.0.0.0')
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    
    logger.info(f"Iniciando webhook de WhatsApp en {host}:{port}")
    logger.info(f"Debug mode: {debug_mode}")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )