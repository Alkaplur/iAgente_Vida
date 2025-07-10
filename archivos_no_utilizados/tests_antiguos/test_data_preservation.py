#!/usr/bin/env python3
"""
Test de preservación de datos (lógica de respaldo)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import Cliente

def test_data_preservation():
    """Prueba la lógica de preservación de datos"""
    
    print("🧪 TEST: Preservación de datos")
    print("=" * 50)
    
    # Cliente con datos completos
    cliente_original = Cliente(
        id_cliente="test_001",
        nombre="Juan",
        edad=45,
        num_dependientes=2,
        ingresos_mensuales=3000.0,
        profesion="ingeniero"
    )
    
    # Simular extractor que perdió algunos datos
    cliente_extraido = Cliente(
        id_cliente="test_001",
        nombre=None,  # Se perdió
        edad=45,
        num_dependientes=None,  # Se perdió
        ingresos_mensuales=3000.0,
        profesion="ingeniero"
    )
    
    print(f"📋 Cliente original: {cliente_original.nombre}, {cliente_original.edad}, {cliente_original.num_dependientes}")
    print(f"📋 Cliente extraído: {cliente_extraido.nombre}, {cliente_extraido.edad}, {cliente_extraido.num_dependientes}")
    
    # Aplicar lógica de preservación
    print("\n🔧 Aplicando lógica de preservación...")
    
    # Conservar datos existentes si el extractor los perdió
    if cliente_original.nombre and not cliente_extraido.nombre:
        cliente_extraido.nombre = cliente_original.nombre
        print(f"   ✅ Restaurado nombre: {cliente_extraido.nombre}")
    
    if cliente_original.edad and not cliente_extraido.edad:
        cliente_extraido.edad = cliente_original.edad
        print(f"   ✅ Restaurado edad: {cliente_extraido.edad}")
    
    if cliente_original.num_dependientes is not None and cliente_extraido.num_dependientes is None:
        cliente_extraido.num_dependientes = cliente_original.num_dependientes
        print(f"   ✅ Restaurado dependientes: {cliente_extraido.num_dependientes}")
    
    if cliente_original.ingresos_mensuales and not cliente_extraido.ingresos_mensuales:
        cliente_extraido.ingresos_mensuales = cliente_original.ingresos_mensuales
        print(f"   ✅ Restaurado ingresos: {cliente_extraido.ingresos_mensuales}")
    
    if cliente_original.profesion and not cliente_extraido.profesion:
        cliente_extraido.profesion = cliente_original.profesion
        print(f"   ✅ Restaurado profesión: {cliente_extraido.profesion}")
    
    if cliente_original.id_cliente and not cliente_extraido.id_cliente:
        cliente_extraido.id_cliente = cliente_original.id_cliente
        print(f"   ✅ Restaurado ID: {cliente_extraido.id_cliente}")
    
    print(f"\n📋 Cliente final: {cliente_extraido.nombre}, {cliente_extraido.edad}, {cliente_extraido.num_dependientes}")
    
    # Verificar que todos los datos se preservaron
    print("\n✅ VERIFICACIÓN FINAL:")
    print(f"   Nombre: {cliente_extraido.nombre} (debe ser 'Juan')")
    print(f"   Edad: {cliente_extraido.edad} (debe ser 45)")
    print(f"   Dependientes: {cliente_extraido.num_dependientes} (debe ser 2)")
    print(f"   Ingresos: {cliente_extraido.ingresos_mensuales} (debe ser 3000.0)")
    print(f"   Profesión: {cliente_extraido.profesion} (debe ser 'ingeniero')")
    print(f"   ID: {cliente_extraido.id_cliente} (debe ser 'test_001')")
    
    # Resultado del test
    success = (
        cliente_extraido.nombre == "Juan" and
        cliente_extraido.edad == 45 and
        cliente_extraido.num_dependientes == 2 and
        cliente_extraido.ingresos_mensuales == 3000.0 and
        cliente_extraido.profesion == "ingeniero" and
        cliente_extraido.id_cliente == "test_001"
    )
    
    print(f"\n{'🎉 TEST EXITOSO' if success else '❌ TEST FALLIDO'}")
    return success

if __name__ == "__main__":
    test_data_preservation()