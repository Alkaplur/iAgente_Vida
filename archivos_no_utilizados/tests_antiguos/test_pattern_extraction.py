#!/usr/bin/env python3
"""
Test de extracción por patrones (optimizado)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import Cliente, ContextoConversacional
from agents.extractor import extraer_datos_cliente

def test_pattern_extraction():
    """Prueba la extracción por patrones y persistencia"""
    
    print("🧪 TEST: Extracción por patrones + persistencia")
    print("=" * 60)
    
    # Cliente inicial vacío
    cliente = Cliente(id_cliente="test_001")
    contexto = ContextoConversacional()
    
    print(f"📋 Cliente inicial: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    
    # Secuencia de mensajes realista
    mensajes = [
        "hola mi cliente se llama Juan",
        "tiene 45 años",
        "tiene 2 hijos",
        "sus ingresos son de 3000 euros",
        "trabaja como ingeniero",
        "¿qué opciones tiene?" # No debe cambiar nada
    ]
    
    for i, mensaje in enumerate(mensajes, 1):
        print(f"\n{i}️⃣ Mensaje: '{mensaje}'")
        cliente, cambios = extraer_datos_cliente(cliente, mensaje, contexto)
        print(f"   Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}, {cliente.ingresos_mensuales}, {cliente.profesion}")
        print(f"   ¿Cambios detectados? {cambios}")
    
    # Verificar que todos los datos se acumularon correctamente
    print(f"\n✅ VERIFICACIÓN FINAL:")
    print(f"   Nombre: {cliente.nombre} (debe ser 'Juan')")
    print(f"   Edad: {cliente.edad} (debe ser 45)")
    print(f"   Dependientes: {cliente.num_dependientes} (debe ser 2)")
    print(f"   Ingresos: {cliente.ingresos_mensuales} (debe ser 3000.0)")
    print(f"   Profesión: {cliente.profesion} (debe ser 'ingeniero')")
    
    # Resultado del test
    success = (
        cliente.nombre == "Juan" and
        cliente.edad == 45 and
        cliente.num_dependientes == 2 and
        cliente.ingresos_mensuales == 3000.0 and
        cliente.profesion == "ingeniero"
    )
    
    print(f"\n{'🎉 TEST EXITOSO - FUNCIONA SIN API' if success else '❌ TEST FALLIDO'}")
    
    if success:
        print("\n🚀 RESUMEN:")
        print("   ✅ Extracción por patrones funciona")
        print("   ✅ Datos se acumulan correctamente")
        print("   ✅ No se pierden datos existentes")
        print("   ✅ Sistema optimizado para funcionar sin API")
        
    return success

if __name__ == "__main__":
    test_pattern_extraction()