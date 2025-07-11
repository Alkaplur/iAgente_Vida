#!/usr/bin/env python3
"""
Ejemplo de uso de la integración Woztell
"""

import os
import sys
import json
from datetime import datetime

# Configurar variables de entorno de ejemplo
os.environ['WOZTELL_BUSINESS_TOKEN'] = 'tu_token_real_aqui'
os.environ['OPENAI_API_KEY'] = 'tu_openai_key_aqui'

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def ejemplo_envio_mensaje():
    """
    Ejemplo de envío de mensaje directo
    """
    print("📤 Ejemplo: Envío de mensaje directo")
    print("-" * 40)
    
    try:
        from src.integrations.woztell_client import send_whatsapp_message
        
        # Enviar mensaje de prueba
        resultado = send_whatsapp_message(
            to_number="34600123456",  # Reemplaza con un número real
            message="¡Hola! Soy iAgente_Vida, tu asistente de seguros de vida. ¿En qué puedo ayudarte?"
        )
        
        print(f"Resultado: {json.dumps(resultado, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Nota: Asegúrate de configurar WOZTELL_BUSINESS_TOKEN")

def ejemplo_webhook_simulado():
    """
    Ejemplo de procesamiento de webhook simulado
    """
    print("\n🔄 Ejemplo: Procesamiento de webhook simulado")
    print("-" * 40)
    
    try:
        from src.integrations.whatsapp_adapter import whatsapp_adapter
        from src.integrations.woztell_client import WoztellMessage
        
        # Crear mensaje simulado
        mensaje_entrante = WoztellMessage(
            from_number="34600123456",
            to_number="34600654321",
            message_type="text",
            content="Hola, tengo 35 años y 2 hijos. ¿Qué seguro me recomiendas?",
            timestamp=datetime.now(),
            message_id="ejemplo_001"
        )
        
        # Procesar mensaje
        resultado = whatsapp_adapter.process_incoming_message(mensaje_entrante)
        
        print(f"Resultado del procesamiento:")
        print(f"  Success: {resultado.get('success')}")
        print(f"  Respuesta: {resultado.get('response', 'N/A')}")
        
        if not resultado.get('success'):
            print(f"  Error: {resultado.get('error')}")
        
    except Exception as e:
        print(f"Error: {e}")

def ejemplo_conversacion_completa():
    """
    Ejemplo de conversación completa
    """
    print("\n💬 Ejemplo: Conversación completa")
    print("-" * 40)
    
    try:
        from src.integrations.whatsapp_adapter import whatsapp_adapter
        from src.integrations.woztell_client import WoztellMessage
        
        # Simular conversación
        conversacion = [
            "Hola",
            "Quiero información sobre seguros de vida",
            "Tengo 30 años y estoy casado",
            "Mis ingresos son de 3000 euros al mes",
            "Tengo 2 hijos pequeños",
            "¿Cuánto me costaría un seguro?"
        ]
        
        user_id = "34600123456"
        
        for i, mensaje in enumerate(conversacion):
            print(f"\n--- Mensaje {i+1}: {mensaje} ---")
            
            mensaje_entrante = WoztellMessage(
                from_number=user_id,
                to_number="34600654321",
                message_type="text",
                content=mensaje,
                timestamp=datetime.now(),
                message_id=f"conv_{i+1}"
            )
            
            resultado = whatsapp_adapter.process_incoming_message(mensaje_entrante)
            
            if resultado.get('success'):
                respuesta = resultado.get('response', 'Sin respuesta')
                print(f"Bot: {respuesta[:100]}...")
            else:
                print(f"Error: {resultado.get('error')}")
                break
        
    except Exception as e:
        print(f"Error: {e}")

def ejemplo_intenciones_especiales():
    """
    Ejemplo de manejo de intenciones especiales
    """
    print("\n🎯 Ejemplo: Intenciones especiales")
    print("-" * 40)
    
    try:
        from src.integrations.whatsapp_adapter import whatsapp_adapter
        from src.integrations.woztell_client import WoztellMessage
        
        # Comandos especiales
        comandos = [
            "help",
            "ayuda",
            "reiniciar",
            "stop",
            "hola"
        ]
        
        user_id = "34600123456"
        
        for comando in comandos:
            print(f"\n--- Comando: {comando} ---")
            
            mensaje_entrante = WoztellMessage(
                from_number=user_id,
                to_number="34600654321",
                message_type="text",
                content=comando,
                timestamp=datetime.now(),
                message_id=f"cmd_{comando}"
            )
            
            resultado = whatsapp_adapter.process_incoming_message(mensaje_entrante)
            
            if resultado.get('success'):
                respuesta = resultado.get('response', 'Sin respuesta')
                print(f"Respuesta: {respuesta[:100]}...")
            else:
                print(f"Error: {resultado.get('error')}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """
    Ejecuta todos los ejemplos
    """
    print("🚀 EJEMPLOS DE USO - INTEGRACIÓN WOZTELL")
    print("=" * 60)
    
    # Verificar configuración
    if not os.getenv('WOZTELL_BUSINESS_TOKEN') or os.getenv('WOZTELL_BUSINESS_TOKEN') == 'tu_token_real_aqui':
        print("⚠️  ADVERTENCIA: WOZTELL_BUSINESS_TOKEN no configurado")
        print("   Los ejemplos de envío real no funcionarán")
        print("   Configura tu token real en las variables de entorno")
        print()
    
    # Ejecutar ejemplos
    ejemplo_envio_mensaje()
    ejemplo_webhook_simulado()
    ejemplo_conversacion_completa()
    ejemplo_intenciones_especiales()
    
    print("\n✅ Ejemplos completados")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Configura tu WOZTELL_BUSINESS_TOKEN real")
    print("2. Ejecuta: python webhook_app.py")
    print("3. Configura la URL del webhook en Woztell")
    print("4. ¡Prueba enviando mensajes desde WhatsApp!")

if __name__ == "__main__":
    main()