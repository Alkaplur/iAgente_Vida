#!/usr/bin/env python3
"""
Test del sistema con LLM como principal
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import Cliente, ContextoConversacional
from agents.extractor import extraer_datos_cliente

def test_llm_principal():
    """Prueba el sistema con LLM como extractor principal"""
    
    print("🧠 TEST: Sistema con LLM como extractor principal")
    print("=" * 60)
    
    # Cliente inicial vacío
    cliente = Cliente(id_cliente="test_llm_001")
    contexto = ContextoConversacional()
    
    # Secuencia de mensajes de prueba
    mensajes = [
        "hola",
        "mi cliente quiere un seguro de vida",
        "se llama Juan García y tiene 45 años",
        "tiene 2 hijos pequeños",
        "trabaja como ingeniero en una empresa de tecnología",
        "sus ingresos son de 3500 euros mensuales",
        "está casado y puede ahorrar 250 euros al mes",
        "no tiene seguro de vida pero cree que es importante"
    ]
    
    for i, mensaje in enumerate(mensajes, 1):
        print(f"\n{i}️⃣ Usuario: '{mensaje}'")
        
        # Usar extractor con LLM como principal
        cliente_anterior = Cliente(**cliente.model_dump())
        cliente, cambios = extraer_datos_cliente(cliente, mensaje, contexto)
        
        # Mostrar resultados
        if cambios:
            print(f"   ✅ Cambios detectados:")
            if cliente.nombre != cliente_anterior.nombre:
                print(f"      👤 Nombre: {cliente.nombre}")
            if cliente.edad != cliente_anterior.edad:
                print(f"      🎂 Edad: {cliente.edad}")
            if cliente.num_dependientes != cliente_anterior.num_dependientes:
                print(f"      👨‍👩‍👧‍👦 Dependientes: {cliente.num_dependientes}")
            if cliente.profesion != cliente_anterior.profesion:
                print(f"      💼 Profesión: {cliente.profesion}")
            if cliente.ingresos_mensuales != cliente_anterior.ingresos_mensuales:
                print(f"      💰 Ingresos: €{cliente.ingresos_mensuales}")
            if cliente.estado_civil != cliente_anterior.estado_civil:
                print(f"      💑 Estado civil: {cliente.estado_civil}")
            if cliente.nivel_ahorro != cliente_anterior.nivel_ahorro:
                print(f"      💵 Ahorro: €{cliente.nivel_ahorro}")
            if cliente.tiene_seguro_vida != cliente_anterior.tiene_seguro_vida:
                print(f"      🛡️ Tiene seguro: {cliente.tiene_seguro_vida}")
            if cliente.percepcion_seguro != cliente_anterior.percepcion_seguro:
                print(f"      🤔 Percepción: {cliente.percepcion_seguro}")
        else:
            print(f"   ℹ️ No se detectaron cambios")
    
    # Resumen final
    print(f"\n🎉 PERFIL FINAL EXTRAÍDO POR LLM:")
    print("=" * 60)
    print(f"👤 Nombre: {cliente.nombre}")
    print(f"🎂 Edad: {cliente.edad}")
    print(f"👨‍👩‍👧‍👦 Dependientes: {cliente.num_dependientes}")
    print(f"💼 Profesión: {cliente.profesion}")
    print(f"💰 Ingresos: €{cliente.ingresos_mensuales}")
    print(f"💑 Estado civil: {cliente.estado_civil}")
    print(f"💵 Ahorro: €{cliente.nivel_ahorro}")
    print(f"🛡️ Tiene seguro: {cliente.tiene_seguro_vida}")
    print(f"🤔 Percepción: {cliente.percepcion_seguro}")
    
    # Verificar completitud
    datos_completos = [
        cliente.nombre,
        cliente.edad,
        cliente.num_dependientes,
        cliente.profesion,
        cliente.ingresos_mensuales,
        cliente.estado_civil,
        cliente.nivel_ahorro,
        cliente.tiene_seguro_vida,
        cliente.percepcion_seguro
    ]
    
    completitud = sum(1 for dato in datos_completos if dato is not None)
    print(f"\n📊 Completitud: {completitud}/9 datos ({completitud/9*100:.1f}%)")
    
    # Evaluar éxito
    success = completitud >= 6  # Al menos 6 campos extraídos
    
    print(f"\n{'✅ LLM FUNCIONA COMO EXTRACTOR PRINCIPAL' if success else '❌ LLM NO EXTRAE SUFICIENTES DATOS'}")
    
    if success:
        print("\n🚀 VENTAJAS DEL LLM COMO PRINCIPAL:")
        print("   ✅ Comprensión contextual superior")
        print("   ✅ Manejo de lenguaje natural")
        print("   ✅ Extracción de múltiples campos simultáneamente")
        print("   ✅ Interpretación inteligente de frases complejas")
        print("   ✅ Fallback a patrones si falla")
    
    return success

if __name__ == "__main__":
    test_llm_principal()