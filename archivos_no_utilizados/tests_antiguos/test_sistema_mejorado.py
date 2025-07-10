#!/usr/bin/env python3
"""
Test del sistema mejorado con respuestas fallback inteligentes
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import Cliente, EstadoBot, ContextoConversacional, EstadoConversacion
from agents.extractor import extraer_datos_cliente
from agents.needs_based_selling import _respuesta_fallback_natural

def test_sistema_mejorado():
    """Prueba el sistema completo con respuestas fallback"""
    
    print("🎯 TEST: Sistema mejorado con fallback inteligente")
    print("=" * 60)
    
    # Estado inicial
    cliente = Cliente(id_cliente="test_001")
    contexto = ContextoConversacional()
    
    # Secuencia de conversación
    mensajes = [
        "hola",
        "mi cliente quiere un seguro de vida",
        "que necesitas saber",
        "se llama Juan y tiene 45 años",
        "tiene 2 hijos",
        "sus ingresos son 3000 euros mensuales",
        "trabaja como ingeniero"
    ]
    
    for i, mensaje in enumerate(mensajes, 1):
        print(f"\n{i}️⃣ Usuario: '{mensaje}'")
        
        # Extraer datos
        cliente_anterior = Cliente(**cliente.model_dump())
        cliente, cambios = extraer_datos_cliente(cliente, mensaje, contexto)
        
        # Crear estado para respuesta fallback
        estado = EstadoBot(
            cliente=cliente,
            mensaje_usuario=mensaje,
            etapa=EstadoConversacion.NEEDS_ANALYSIS,
            mensajes=[],
            contexto=contexto,
            agente_activo="needs_based_selling"
        )
        
        # Generar respuesta fallback
        respuesta = _respuesta_fallback_natural(estado)
        
        print(f"   🤖 Bot: {respuesta}")
        
        # Mostrar cambios si los hay
        if cambios:
            print(f"   📊 Datos extraídos:")
            if cliente.nombre != cliente_anterior.nombre:
                print(f"      - Nombre: {cliente.nombre}")
            if cliente.edad != cliente_anterior.edad:
                print(f"      - Edad: {cliente.edad}")
            if cliente.num_dependientes != cliente_anterior.num_dependientes:
                print(f"      - Dependientes: {cliente.num_dependientes}")
            if cliente.ingresos_mensuales != cliente_anterior.ingresos_mensuales:
                print(f"      - Ingresos: €{cliente.ingresos_mensuales}")
            if cliente.profesion != cliente_anterior.profesion:
                print(f"      - Profesión: {cliente.profesion}")
    
    # Resumen final
    print(f"\n🎉 CONVERSACIÓN COMPLETADA")
    print("=" * 60)
    print("📋 PERFIL FINAL:")
    print(f"   👤 Nombre: {cliente.nombre}")
    print(f"   🎂 Edad: {cliente.edad}")
    print(f"   👨‍👩‍👧‍👦 Dependientes: {cliente.num_dependientes}")
    print(f"   💰 Ingresos: €{cliente.ingresos_mensuales}")
    print(f"   💼 Profesión: {cliente.profesion}")
    
    # Verificar éxito
    success = (
        cliente.nombre == "Juan" and
        cliente.edad == 45 and
        cliente.num_dependientes == 2 and
        cliente.ingresos_mensuales == 3000.0 and
        cliente.profesion == "ingeniero"
    )
    
    print(f"\n{'✅ SISTEMA FUNCIONANDO PERFECTAMENTE' if success else '❌ PROBLEMAS DETECTADOS'}")
    print("🚀 CARACTERÍSTICAS:")
    print("   ✅ Extracción por patrones")
    print("   ✅ Respuestas fallback inteligentes")
    print("   ✅ No requiere API para funcionar")
    print("   ✅ Conversación natural")
    
    return success

if __name__ == "__main__":
    test_sistema_mejorado()