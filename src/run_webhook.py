#!/usr/bin/env python3
"""
Script para ejecutar el webhook de WhatsApp
Incluye configuración de desarrollo y producción
"""
import sys
import os
import logging
from datetime import datetime

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.webhooks.whatsapp_webhook import app
    from src.config import settings
except ImportError:
    from webhooks.whatsapp_webhook import app
    from config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Función principal para ejecutar el webhook"""
    
    print("🚀 Iniciando webhook de WhatsApp Business para iAgente_Vida")
    print(f"⏰ Tiempo de inicio: {datetime.now().isoformat()}")
    
    # Verificar configuración
    required_settings = [
        'whatsapp_phone_number_id',
        'whatsapp_token',
        'whatsapp_verify_token'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing_settings.append(setting)
    
    if missing_settings:
        print(f"❌ Configuración faltante: {', '.join(missing_settings)}")
        print("💡 Asegúrate de configurar las variables en .env:")
        for setting in missing_settings:
            print(f"   {setting.upper()}=tu_valor_aquí")
        sys.exit(1)
    
    # Configuración del servidor
    host = getattr(settings, 'webhook_host', '0.0.0.0')
    port = getattr(settings, 'webhook_port', 5000)
    debug = getattr(settings, 'debug', False)
    
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"📱 Webhook URL: http://{host}:{port}/webhook/whatsapp")
    print(f"🔧 Debug mode: {debug}")
    print(f"📞 WhatsApp Phone ID: {settings.whatsapp_phone_number_id}")
    
    # Mensajes informativos
    print("\n📋 Endpoints disponibles:")
    print(f"   GET  /webhook/whatsapp    - Verificación del webhook")
    print(f"   POST /webhook/whatsapp    - Recibir mensajes")
    print(f"   GET  /webhook/status      - Estado del webhook")
    print(f"   GET  /webhook/conversations - Lista de conversaciones")
    print(f"   DEL  /webhook/conversation/<phone> - Reiniciar conversación")
    
    print("\n🔐 Para configurar en Meta:")
    print(f"   1. URL del webhook: http://tu-servidor:{port}/webhook/whatsapp")
    print(f"   2. Token de verificación: {settings.whatsapp_verify_token}")
    print(f"   3. Eventos: messages, message_deliveries")
    
    print("\n🎯 Integración Chatwoot:")
    chatwoot_configured = all([
        hasattr(settings, 'chatwoot_base_url'),
        hasattr(settings, 'chatwoot_account_id'), 
        hasattr(settings, 'chatwoot_user_token')
    ])
    print(f"   Estado: {'✅ Configurado' if chatwoot_configured else '⚠️ Pendiente'}")
    
    print("\n" + "="*60)
    print("🚀 WEBHOOK LISTO - Esperando mensajes de WhatsApp...")
    print("="*60)
    
    try:
        # Ejecutar servidor Flask
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False  # Evitar recargas automáticas en producción
        )
    except KeyboardInterrupt:
        print("\n👋 Webhook detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando webhook: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()