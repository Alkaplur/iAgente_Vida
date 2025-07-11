"""
Aplicación principal del webhook para WhatsApp
Archivo de entrada para producción
"""

import os
import sys
import logging
from datetime import datetime

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

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.whatsapp_webhook import app
    logger.info("Aplicación de webhook importada exitosamente")
except ImportError as e:
    logger.error(f"Error importando aplicación: {e}")
    sys.exit(1)

if __name__ == '__main__':
    # Configuración de producción
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8080))  # Railway usa PORT variable
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Iniciando iAgente_Vida WhatsApp Webhook")
    logger.info(f"Host: {host}, Puerto: {port}, Debug: {debug}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Evitar doble inicio en producción
        )
    except Exception as e:
        logger.error(f"Error iniciando aplicación: {e}")
        sys.exit(1)