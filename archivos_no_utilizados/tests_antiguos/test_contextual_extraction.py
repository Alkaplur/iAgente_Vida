#!/usr/bin/env python3
"""
Test de extracción contextual (sin API)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import Cliente, ContextoConversacional
from agents.extractor import _interpretar_con_contexto, _detectar_cambios

def test_contextual_extraction():
    """Prueba la extracción contextual sin usar API"""
    
    print("🧪 TEST: Extracción contextual (sin API)")
    print("=" * 50)
    
    # Cliente inicial vacío
    cliente = Cliente(id_cliente="test_001")
    contexto = ContextoConversacional()
    
    print(f"📋 Cliente inicial: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    
    # Test 1: Edad con contexto
    print("\n1️⃣ Simular pregunta de edad y respuesta '45'")
    contexto.esperando_respuesta = True
    contexto.ultimo_campo_solicitado = "edad"
    
    cliente_updated, cambio = _interpretar_con_contexto(cliente, "45", contexto)
    print(f"   Cliente después: edad={cliente_updated.edad}")
    print(f"   ¿Cambio detectado? {cambio}")
    
    # Test 2: Dependientes con contexto
    print("\n2️⃣ Simular pregunta de dependientes y respuesta '2'")
    contexto.esperando_respuesta = True
    contexto.ultimo_campo_solicitado = "num_dependientes"
    
    cliente_updated, cambio = _interpretar_con_contexto(cliente_updated, "2", contexto)
    print(f"   Cliente después: dependientes={cliente_updated.num_dependientes}")
    print(f"   ¿Cambio detectado? {cambio}")
    
    # Test 3: Ingresos con contexto
    print("\n3️⃣ Simular pregunta de ingresos y respuesta '3000'")
    contexto.esperando_respuesta = True
    contexto.ultimo_campo_solicitado = "ingresos_mensuales"
    
    cliente_updated, cambio = _interpretar_con_contexto(cliente_updated, "3000", contexto)
    print(f"   Cliente después: ingresos={cliente_updated.ingresos_mensuales}")
    print(f"   ¿Cambio detectado? {cambio}")
    
    # Test 4: Nombre con contexto
    print("\n4️⃣ Simular pregunta de nombre y respuesta 'Juan'")
    contexto.esperando_respuesta = True
    contexto.ultimo_campo_solicitado = "nombre"
    
    cliente_updated, cambio = _interpretar_con_contexto(cliente_updated, "Juan", contexto)
    print(f"   Cliente después: nombre={cliente_updated.nombre}")
    print(f"   ¿Cambio detectado? {cambio}")
    
    # Test 5: Verificar que los datos se acumulan
    print("\n5️⃣ Verificar acumulación de datos")
    cambios = _detectar_cambios(cliente, cliente_updated)
    print(f"   Cambios totales: {cambios}")
    
    # Verificar que todos los datos se mantuvieron
    print("\n✅ VERIFICACIÓN FINAL:")
    print(f"   Nombre: {cliente_updated.nombre} (debe ser 'Juan')")
    print(f"   Edad: {cliente_updated.edad} (debe ser 45)")
    print(f"   Dependientes: {cliente_updated.num_dependientes} (debe ser 2)")
    print(f"   Ingresos: {cliente_updated.ingresos_mensuales} (debe ser 3000.0)")
    
    # Resultado del test
    success = (
        cliente_updated.nombre == "Juan" and
        cliente_updated.edad == 45 and
        cliente_updated.num_dependientes == 2 and
        cliente_updated.ingresos_mensuales == 3000.0
    )
    
    print(f"\n{'🎉 TEST EXITOSO' if success else '❌ TEST FALLIDO'}")
    return success

if __name__ == "__main__":
    test_contextual_extraction()