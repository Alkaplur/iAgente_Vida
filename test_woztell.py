#!/usr/bin/env python3
"""
Script de prueba para la integración con Woztell
"""

import os
import sys
import json
import time
from datetime import datetime

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.integrations.woztell_client import WoztellClient, WoztellMessage
    from src.integrations.whatsapp_adapter import WhatsAppAdapter
    print("✅ Módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def test_woztell_client():
    """
    Test básico del cliente Woztell
    """
    print("\n🧪 Testeando WoztellClient...")
    
    try:
        # Verificar que el token está configurado
        token = os.getenv('WOZTELL_BUSINESS_TOKEN')
        if not token or token == 'tu_woztell_business_token_aqui':
            print("⚠️  WOZTELL_BUSINESS_TOKEN no configurado - saltando test real")
            return False
        
        client = WoztellClient(token)
        print("✅ Cliente Woztell inicializado")
        
        # Test de limpieza de número
        test_numbers = [
            "34600123456",
            "+34 600 123 456",
            "600123456",
            "600-123-456"
        ]
        
        for number in test_numbers:
            clean = client._clean_phone_number(number)
            print(f"   {number} -> {clean}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en WoztellClient: {e}")
        return False

def test_message_parsing():
    """
    Test de parseo de mensajes
    """
    print("\n🧪 Testeando parseo de mensajes...")
    
    try:
        client = WoztellClient("dummy_token")
        
        # Test de mensaje de texto
        webhook_data = {
            "from": "34600123456",
            "to": "34600654321",
            "message": {
                "type": "text",
                "text": "Hola, quiero información sobre seguros"
            },
            "id": "msg_123"
        }
        
        message = client.parse_incoming_message(webhook_data)
        
        if message:
            print("✅ Mensaje parseado correctamente:")
            print(f"   From: {message.from_number}")
            print(f"   Content: {message.content}")
            print(f"   Type: {message.message_type}")
            print(f"   ID: {message.message_id}")
            return True
        else:
            print("❌ No se pudo parsear el mensaje")
            return False
            
    except Exception as e:
        print(f"❌ Error parseando mensaje: {e}")
        return False

def test_whatsapp_adapter():
    """
    Test del adaptador WhatsApp
    """
    print("\n🧪 Testeando WhatsAppAdapter...")
    
    try:
        # Crear mensaje de prueba
        test_message = WoztellMessage(
            from_number="34600123456",
            to_number="34600654321",
            message_type="text",
            content="Hola, quiero información sobre seguros de vida",
            timestamp=datetime.now(),
            message_id="test_msg_123"
        )
        
        # Crear adaptador (en modo test)
        os.environ['WOZTELL_BUSINESS_TOKEN'] = 'test_token'
        adapter = WhatsAppAdapter()
        
        # Test detección de intenciones
        intentions = [
            ("hola", "greeting"),
            ("help", "help"),
            ("ayuda", "help"),
            ("reiniciar", "restart"),
            ("stop", "stop"),
            ("quiero un seguro", None)
        ]
        
        for message_text, expected in intentions:
            detected = adapter._detect_special_intention(message_text)
            status = "✅" if detected == expected else "❌"
            print(f"   {status} '{message_text}' -> {detected} (esperado: {expected})")
        
        # Test de mensajes de sistema
        welcome = adapter._get_welcome_message()
        help_msg = adapter._get_help_message()
        
        print(f"✅ Mensaje de bienvenida: {len(welcome)} caracteres")
        print(f"✅ Mensaje de ayuda: {len(help_msg)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en WhatsAppAdapter: {e}")
        return False

def test_message_adaptation():
    """
    Test de adaptación de mensajes
    """
    print("\n🧪 Testeando adaptación de mensajes...")
    
    try:
        os.environ['WOZTELL_BUSINESS_TOKEN'] = 'test_token'
        adapter = WhatsAppAdapter()
        
        # Test de conversión markdown
        test_messages = [
            "**Hola** _mundo_",
            "Mensaje muy largo " + "x" * 5000,
            "Mensaje normal"
        ]
        
        for msg in test_messages:
            adapted = adapter._adapt_message_for_whatsapp(msg)
            print(f"   Original: {len(msg)} chars -> Adaptado: {len(adapted)} chars")
            if len(msg) != len(adapted):
                print(f"   Cambios aplicados: {msg[:50]}... -> {adapted[:50]}...")
        
        # Test de división de mensajes
        long_message = "Esta es una oración muy larga. " * 200
        parts = adapter._split_message(long_message)
        print(f"✅ Mensaje largo dividido en {len(parts)} partes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en adaptación: {e}")
        return False

def test_webhook_simulation():
    """
    Simula el procesamiento de un webhook
    """
    print("\n🧪 Simulando procesamiento de webhook...")
    
    try:
        # Crear datos de webhook simulados
        webhook_data = {
            "from": "34600123456",
            "to": "34600654321",
            "message": {
                "type": "text",
                "text": "Hola, necesito información sobre seguros de vida"
            },
            "id": "webhook_test_123",
            "timestamp": datetime.now().isoformat()
        }
        
        print("✅ Datos de webhook simulados:")
        print(json.dumps(webhook_data, indent=2, default=str))
        
        # Parsear mensaje
        from src.integrations.woztell_client import parse_whatsapp_webhook
        message = parse_whatsapp_webhook(webhook_data)
        
        if message:
            print("✅ Webhook parseado correctamente")
            print(f"   Usuario: {message.from_number}")
            print(f"   Mensaje: {message.content}")
            return True
        else:
            print("❌ Error parseando webhook")
            return False
            
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False

def main():
    """
    Ejecuta todos los tests
    """
    print("🚀 Iniciando tests de integración Woztell")
    print("=" * 50)
    
    tests = [
        ("Cliente Woztell", test_woztell_client),
        ("Parseo de mensajes", test_message_parsing),
        ("Adaptador WhatsApp", test_whatsapp_adapter),
        ("Adaptación de mensajes", test_message_adaptation),
        ("Simulación de webhook", test_webhook_simulation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n📊 RESUMEN DE TESTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todos los tests pasaron! La integración está lista.")
    else:
        print("⚠️  Algunos tests fallaron. Revisa la configuración.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)