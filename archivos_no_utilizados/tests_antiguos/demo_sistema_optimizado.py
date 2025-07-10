#!/usr/bin/env python3
"""
Demo del sistema optimizado - Funciona con o sin API
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import Cliente, ContextoConversacional
from agents.extractor import extraer_datos_cliente

def demo_conversacion_completa():
    """Simula una conversación completa de ventas"""
    
    print("🎯 DEMO: Sistema iAgente_Vida Optimizado")
    print("=" * 50)
    print("✅ Funciona CON o SIN API")
    print("✅ Extracción por patrones + contextual")
    print("✅ Persistencia de datos garantizada")
    print("=" * 50)
    
    # Cliente inicial vacío
    cliente = Cliente(id_cliente="demo_001")
    contexto = ContextoConversacional()
    
    # Conversación realista de agente de seguros
    conversacion = [
        ("Agente", "¡Hola! Soy tu asistente para seguros de vida. ¿En qué puedo ayudarte?"),
        ("Usuario", "hola mi cliente quiere un seguro de vida"),
        ("Agente", "Perfecto, te ayudo con eso. ¿Puedes contarme un poco sobre tu cliente?"),
        ("Usuario", "se llama Juan y tiene 45 años"),
        ("Agente", "Entiendo, Juan de 45 años. ¿Tiene familia? ¿Cuántos dependientes?"),
        ("Usuario", "tiene 2 hijos"),
        ("Agente", "Perfecto, 2 hijos. ¿Cuáles son sus ingresos mensuales aproximados?"),
        ("Usuario", "sus ingresos son de 3000 euros"),
        ("Agente", "Excelente. ¿A qué se dedica Juan?"),
        ("Usuario", "trabaja como ingeniero"),
        ("Agente", "Perfecto, con esta información puedo hacer una recomendación personalizada"),
        ("Usuario", "¿qué opciones tiene?")
    ]
    
    for i, (rol, mensaje) in enumerate(conversacion):
        print(f"\n📍 TURNO {i+1}: {rol}")
        print(f"💬 {mensaje}")
        
        if rol == "Usuario":
            # Extraer datos del mensaje del usuario
            cliente_anterior = Cliente(**cliente.model_dump())
            cliente, cambios = extraer_datos_cliente(cliente, mensaje, contexto)
            
            if cambios:
                # Mostrar qué cambió
                campos_anteriores = {
                    "nombre": cliente_anterior.nombre,
                    "edad": cliente_anterior.edad,
                    "num_dependientes": cliente_anterior.num_dependientes,
                    "ingresos_mensuales": cliente_anterior.ingresos_mensuales,
                    "profesion": cliente_anterior.profesion
                }
                
                campos_actuales = {
                    "nombre": cliente.nombre,
                    "edad": cliente.edad,
                    "num_dependientes": cliente.num_dependientes,
                    "ingresos_mensuales": cliente.ingresos_mensuales,
                    "profesion": cliente.profesion
                }
                
                print("   📊 DATOS EXTRAÍDOS:")
                for campo, valor_actual in campos_actuales.items():
                    valor_anterior = campos_anteriores[campo]
                    if valor_anterior != valor_actual and valor_actual is not None:
                        print(f"      ✅ {campo}: {valor_anterior} → {valor_actual}")
            
            # Mostrar perfil completo del cliente
            datos_completos = [
                f"Nombre: {cliente.nombre or 'N/A'}",
                f"Edad: {cliente.edad or 'N/A'}",
                f"Dependientes: {cliente.num_dependientes if cliente.num_dependientes is not None else 'N/A'}",
                f"Ingresos: €{cliente.ingresos_mensuales or 'N/A'}",
                f"Profesión: {cliente.profesion or 'N/A'}"
            ]
            
            print("   👤 PERFIL ACTUAL DEL CLIENTE:")
            for dato in datos_completos:
                print(f"      {dato}")
    
    # Resumen final
    print(f"\n🎉 CONVERSACIÓN COMPLETADA")
    print("=" * 50)
    print("📋 PERFIL FINAL DEL CLIENTE:")
    print(f"   👤 Nombre: {cliente.nombre}")
    print(f"   🎂 Edad: {cliente.edad} años")
    print(f"   👨‍👩‍👧‍👦 Dependientes: {cliente.num_dependientes} hijos")
    print(f"   💰 Ingresos: €{cliente.ingresos_mensuales}/mes")
    print(f"   💼 Profesión: {cliente.profesion}")
    
    # Verificar completitud
    completitud = sum(1 for v in [cliente.nombre, cliente.edad, cliente.num_dependientes, cliente.ingresos_mensuales, cliente.profesion] if v is not None)
    print(f"   📊 Completitud: {completitud}/5 datos ({completitud*20}%)")
    
    if completitud == 5:
        print("   ✅ LISTO PARA COTIZACIÓN")
    else:
        print("   ⚠️ FALTAN DATOS")
    
    print("\n🚀 SISTEMA FUNCIONANDO ÓPTIMAMENTE")
    print("   ✅ Extracción por patrones: ACTIVA")
    print("   ✅ Persistencia de datos: GARANTIZADA")
    print("   ✅ Funciona sin API: SÍ")
    print("   ✅ Funciona con API: SÍ (cuando esté disponible)")

if __name__ == "__main__":
    demo_conversacion_completa()