#!/usr/bin/env python3
"""
Test de carga de API key
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings

def test_api_key_loading():
    """Verifica que la API key se carga correctamente"""
    
    print("🔑 TEST: Carga de API Key")
    print("=" * 40)
    
    # Verificar que la API key se carga
    print(f"Provider configurado: {settings.llm_provider}")
    print(f"Modelo configurado: {settings.llm_model}")
    
    # Verificar API key (mostrar solo el final)
    if settings.openai_api_key:
        key_end = settings.openai_api_key[-20:]  # Últimos 20 caracteres
        print(f"OpenAI API key terminación: ...{key_end}")
        
        # Verificar que termina con la cadena correcta
        if settings.openai_api_key.endswith("OvA2Mwr7JeuF1knwA"):
            print("✅ API key termina correctamente")
        else:
            print("❌ API key NO termina correctamente")
    else:
        print("❌ No se pudo cargar OpenAI API key")
    
    # Test directo con OpenAI
    print("\n🧪 TEST: Conexión directa con OpenAI")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Test simple
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Responde solo: 'API funciona'"}],
            max_tokens=10
        )
        
        print(f"✅ Respuesta OpenAI: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error OpenAI: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key_loading()
    if success:
        print("\n🎉 API KEY FUNCIONANDO CORRECTAMENTE")
    else:
        print("\n❌ PROBLEMA CON API KEY")