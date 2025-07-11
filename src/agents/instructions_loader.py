"""
Utilidad para cargar instrucciones de archivos txt de manera consistente
"""

import os
from typing import Dict


def cargar_instrucciones(agente: str) -> str:
    # Construir path relativo al directorio del archivo actual
    current_dir = os.path.dirname(__file__)
    archivo_instrucciones = os.path.join(current_dir, "agents_instructions", f"{agente}_instructions.txt")
    
    try:
        with open(archivo_instrucciones, 'r', encoding='utf-8') as f:
            instrucciones = f.read().strip()
            return instrucciones
    
    except FileNotFoundError:  
        return _get_fallback_instructions(agente)

    except Exception as e: 
        print(f"❌ Error cargando instrucciones de {agente}: {e}")
        return _get_fallback_instructions(agente)

def _get_fallback_instructions(agente: str) -> str:
    """
    Instrucciones de emergencia si no se encuentra el archivo
    """
    
    fallbacks = {
        'needs_based': """Eres un experto en needs-based selling para seguros de vida.
Tu trabajo es asesorar al agente sobre cómo identificar necesidades del cliente y recomendar productos.
IMPORTANTE: Valida siempre la capacidad de pago (máximo 10% del ingreso disponible).
Usa las fórmulas actualizadas: 6-10 años de ingresos según perfil del cliente.""",
        
        'orquestador': """Analiza la situación y decide qué agente debe actuar según el contexto.
Considera: porcentaje de datos completados, presencia de recomendaciones, cotizaciones existentes,
y la intención específica del mensaje del usuario.""",
        
        'quote': """Eres el motor de cotización de iAgente_Vida. 
Genera cotizaciones precisas usando los parámetros del motor_cotizacion.txt.
Calcula primas considerando edad, perfil de riesgo y tipo de producto.
Valida límites técnicos y ajusta según presupuesto del cliente.
Siempre ofrece 3 opciones: recomendada, económica y premium.""",
        
        'presentador': """Eres el agente de presentación y cierre de iAgente_Vida.
Presenta cotizaciones de manera atractiva y maneja objeciones.
Usa argumentos de venta específicos de productos_seguros.txt.
Guía al agente hacia técnicas de cierre efectivas.""",
        
        'extractor': """Extrae información específica de mensajes de forma inteligente.
Actualiza campos del cliente incluyendo: gastos_fijos_mensuales, salud_relevante, riders_deseados.
Valida límites técnicos y formatos de datos."""
    }
    
    return fallbacks.get(agente, "Actúa de manera profesional y útil.")

def cargar_todas_instrucciones() -> Dict[str, str]:
    """
    Carga todas las instrucciones de una vez para optimización
    
    Returns:
        Dict con todas las instrucciones cargadas
    """
    
    agentes = ['needs_based', 'orquestador', 'quote', 'presentador', 'extractor']
    
    instrucciones = {}
    for agente in agentes:
        instrucciones[agente] = cargar_instrucciones(agente)
    
    print(f"📚 Todas las instrucciones cargadas: {len(instrucciones)} agentes")
    return instrucciones

def verificar_archivos_instrucciones() -> Dict[str, bool]:
    """
    Verifica qué archivos de instrucciones existen
    
    Returns:
        Dict indicando qué archivos existen
    """
    
    agentes = ['needs_based', 'orquestador', 'quote', 'presentador', 'extractor']
    
    estado = {}
    for agente in agentes:
        archivo = f"agents/{agente}_instructions.txt"
        estado[agente] = os.path.exists(archivo)
    
    return estado

# Cache de instrucciones para evitar leer archivos repetidamente
_cache_instrucciones = {}

def cargar_instrucciones_cached(agente: str, forzar_recarga: bool = False) -> str:
    """
    Carga instrucciones con cache para mejor rendimiento
    
    Args:
        agente: Nombre del agente
        forzar_recarga: Si True, recarga desde archivo aunque esté en cache
    
    Returns:
        str: Instrucciones del agente
    """
    
    if not forzar_recarga and agente in _cache_instrucciones:
        return _cache_instrucciones[agente]
    
    instrucciones = cargar_instrucciones(agente)
    _cache_instrucciones[agente] = instrucciones
    
    return instrucciones