#!/usr/bin/env python3
"""
Test de persistencia de datos del cliente
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import Cliente, EstadoBot, ContextoConversacional
from agents.extractor import extraer_datos_cliente

def test_data_persistence():
    """Prueba que los datos del cliente se persisten correctamente"""
    
    print("🧪 TEST: Persistencia de datos del cliente")
    print("=" * 50)
    
    # Cliente inicial vacío
    cliente = Cliente(id_cliente="test_001")
    contexto = ContextoConversacional()
    
    print(f"📋 Cliente inicial: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    
    # Mensaje 1: Agregar nombre
    print("\n1️⃣ Mensaje: 'hola mi cliente se llama Juan'")
    cliente, cambios = extraer_datos_cliente(cliente, "hola mi cliente se llama Juan", contexto)
    print(f"   Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    print(f"   ¿Cambios detectados? {cambios}")
    
    # Mensaje 2: Agregar edad
    print("\n2️⃣ Mensaje: 'tiene 45 años'")
    cliente, cambios = extraer_datos_cliente(cliente, "tiene 45 años", contexto)
    print(f"   Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    print(f"   ¿Cambios detectados? {cambios}")
    
    # Mensaje 3: Agregar dependientes
    print("\n3️⃣ Mensaje: 'tiene 2 hijos'")
    cliente, cambios = extraer_datos_cliente(cliente, "tiene 2 hijos", contexto)
    print(f"   Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    print(f"   ¿Cambios detectados? {cambios}")
    
    # Mensaje 4: Agregar ingresos
    print("\n4️⃣ Mensaje: 'sus ingresos son de 3000 euros'")
    cliente, cambios = extraer_datos_cliente(cliente, "sus ingresos son de 3000 euros", contexto)
    print(f"   Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}, {cliente.ingresos_mensuales}")
    print(f"   ¿Cambios detectados? {cambios}")
    
    # Mensaje 5: Pregunta genérica (no debe perder datos)
    print("\n5️⃣ Mensaje: '¿qué opciones tiene?'")
    cliente, cambios = extraer_datos_cliente(cliente, "¿qué opciones tiene?", contexto)
    print(f"   Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}, {cliente.ingresos_mensuales}")
    print(f"   ¿Cambios detectados? {cambios}")
    
    # Verificar que todos los datos se mantuvieron
    print("\n✅ VERIFICACIÓN FINAL:")
    print(f"   Nombre: {cliente.nombre} (debe ser 'Juan')")
    print(f"   Edad: {cliente.edad} (debe ser 45)")
    print(f"   Dependientes: {cliente.num_dependientes} (debe ser 2)")
    print(f"   Ingresos: {cliente.ingresos_mensuales} (debe ser 3000.0)")
    
    # Resultado del test
    success = (
        cliente.nombre == "Juan" and
        cliente.edad == 45 and
        cliente.num_dependientes == 2 and
        cliente.ingresos_mensuales == 3000.0
    )
    
    print(f"\n{'🎉 TEST EXITOSO' if success else '❌ TEST FALLIDO'}")
    return success

if __name__ == "__main__":
    test_data_persistence()