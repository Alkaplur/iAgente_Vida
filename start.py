#!/usr/bin/env python
"""
Launcher principal para iAgente_Vida en VS Code
"""
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Función principal"""
    print("🚀 iAgente_Vida - Sistema Optimizado")
    print("✅ Funciona CON o SIN API")
    print("✅ Extracción por patrones + respuestas inteligentes")
    print("=" * 50)
    
    try:
        # Importar y ejecutar main
        from main import conversacion_interactiva
        conversacion_interactiva()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()