#!/usr/bin/env python3
"""
Test del caso real del usuario: Eulalio
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import Cliente, ContextoConversacional
from agents.extractor import extraer_datos_cliente
from agents.needs_based_selling import _generar_recomendacion_producto

def test_caso_eulalio():
    """Prueba el caso real: Eulalio, 55 años, pintor, 3 hijos, casado"""
    
    print("🧪 TEST: Caso real - Eulalio")
    print("=" * 50)
    
    # Cliente inicial con nombre anterior (simulando el contexto)
    cliente = Cliente(id_cliente="eulalio_001", nombre="Que")  # Simular el estado anterior
    contexto = ContextoConversacional()
    
    # Mensaje del usuario
    mensaje = "se llama Eulalio, edad 55, trabaja como pintor, tiene 3 hijos, y esta casado, asi que hay 4 personas que dependen de el"
    
    print(f"📝 Mensaje: '{mensaje}'")
    print(f"🔍 Cliente antes: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    
    # Extraer datos con LLM
    cliente, cambios = extraer_datos_cliente(cliente, mensaje, contexto)
    
    print(f"✅ Cliente después: {cliente.nombre}, {cliente.edad}, {cliente.num_dependientes}")
    print(f"📊 Cambios detectados: {cambios}")
    
    # Mostrar datos extraídos
    print("\n📋 DATOS EXTRAÍDOS:")
    print(f"   👤 Nombre: {cliente.nombre}")
    print(f"   🎂 Edad: {cliente.edad}")
    print(f"   👨‍👩‍👧‍👦 Dependientes: {cliente.num_dependientes}")
    print(f"   💼 Profesión: {cliente.profesion}")
    print(f"   💑 Estado civil: {cliente.estado_civil}")
    print(f"   💰 Ingresos: {cliente.ingresos_mensuales}")
    
    # Generar recomendación (probar que no hay error matemático)
    try:
        recomendacion = _generar_recomendacion_producto(cliente)
        print(f"\n🎯 RECOMENDACIÓN GENERADA:")
        print(f"   📦 Tipo: {recomendacion.tipo_cobertura}")
        print(f"   🛡️ Cobertura: {recomendacion.cobertura_principal}")
        print(f"   💰 Monto: €{recomendacion.monto_recomendado:,.0f}")
        print(f"   📝 Justificación: {recomendacion.justificacion}")
        print(f"   ⚡ Urgencia: {recomendacion.urgencia}")
        
        success = True
    except Exception as e:
        print(f"❌ Error en recomendación: {e}")
        success = False
    
    # Verificar que se extrajeron los datos correctos
    # Nota: El LLM interpretó inteligentemente "4 personas que dependen de él" como 4 dependientes
    datos_correctos = (
        cliente.nombre == "Eulalio" and
        cliente.edad == 55 and
        cliente.num_dependientes == 4 and  # Interpretación inteligente: 3 hijos + 1 esposa
        cliente.profesion == "pintor" and
        cliente.estado_civil == "casado"
    )
    
    print(f"\n{'✅ EXTRACCIÓN CORRECTA' if datos_correctos else '❌ EXTRACCIÓN INCORRECTA'}")
    print(f"{'✅ RECOMENDACIÓN FUNCIONA' if success else '❌ ERROR EN RECOMENDACIÓN'}")
    
    if datos_correctos and success:
        print("\n🎉 SISTEMA FUNCIONA CORRECTAMENTE CON CASO REAL")
        print("   ✅ Extractor LLM captura todos los datos")
        print("   ✅ No hay errores matemáticos")
        print("   ✅ Recomendación generada sin problemas")
    
    return datos_correctos and success

if __name__ == "__main__":
    test_caso_eulalio()