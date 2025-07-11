"""
Agente Presentador - Manejo de objeciones y cierre de ventas
"""
from typing import Dict, Any

try:
    from ..models import EstadoBot, EstadoConversacion
    from .instructions_loader import cargar_instrucciones_cached
    from .llm_client import get_llm_response
    from ..utils.productos_loader import obtener_productos_loader
except ImportError:
    from models import EstadoBot, EstadoConversacion
    from agents.instructions_loader import cargar_instrucciones_cached
    from agents.llm_client import get_llm_response
    from utils.productos_loader import obtener_productos_loader


def presentador_node(state: EstadoBot) -> Dict[str, Any]:
    """
    Agente especializado en:
    - Presentar cotizaciones de manera atractiva
    - Responder dudas sobre las opciones
    - Manejar objeciones
    - Guiar hacia el cierre
    """
    
    print(f"📊 PRESENTADOR: {state.cliente.nombre} | {len(state.cotizaciones)} cotizaciones")
    
    # Analizar qué necesita el cliente
    respuesta = _manejar_presentacion_y_dudas(state)
    
    return {
        "respuesta_bot": respuesta,
        "cliente": state.cliente,
        "cotizaciones": state.cotizaciones,
        "recomendacion_producto": state.recomendacion_producto,
        "etapa": EstadoConversacion.PRESENTACION_PROPUESTA,
        "contexto": state.contexto,
        "mensajes": state.mensajes + [{"usuario": state.mensaje_usuario}, {"bot": respuesta}] if state.mensajes else [{"usuario": state.mensaje_usuario}, {"bot": respuesta}]
    }


def _manejar_presentacion_y_dudas(state: EstadoBot) -> str:
    """Maneja la presentación de cotizaciones y responde dudas usando instrucciones y productos"""
    
    if not state.cotizaciones:
        return "Permíteme generar las cotizaciones para ti..."
    
    # Cargar instrucciones del presentador
    instrucciones_presentador = cargar_instrucciones_cached('presentador')
    productos_loader = obtener_productos_loader()
    
    # Obtener información de productos para enriquecer la presentación
    producto_recomendado = productos_loader.recomendar_producto(
        edad=state.cliente.edad or 30,
        num_dependientes=state.cliente.num_dependientes or 0,
        ingresos_mensuales=state.cliente.ingresos_mensuales,
        profesion=state.cliente.profesion
    )
    
    # Preparar información enriquecida de cotizaciones
    cotizaciones_texto = ""
    for i, cot in enumerate(state.cotizaciones, 1):
        cotizaciones_texto += f"\nOpción {i}: {cot.tipo_plan}\n"
        cotizaciones_texto += f"  • Prima: €{cot.prima_mensual}/mes\n"
        cotizaciones_texto += f"  • Cobertura: €{cot.cobertura_fallecimiento:,.0f}\n"
        cotizaciones_texto += f"  • Vigencia: {cot.vigencia_anos} años\n"
        
        # Añadir argumentos de venta del producto si está disponible
        if producto_recomendado and i == 1:  # Solo para la primera opción (recomendada)
            cotizaciones_texto += f"  • Ventaja: {producto_recomendado.argumentos_venta}\n"
    
    # Añadir información del producto recomendado
    info_producto = ""
    if producto_recomendado:
        info_producto = f"\n\nINFO DEL PRODUCTO RECOMENDADO:\n- Nombre: {producto_recomendado.nombre_comercial}\n- Público objetivo: {producto_recomendado.publico_objetivo}\n- Características: {producto_recomendado.caracteristicas}"
    
    prompt = f"""
{instrucciones_presentador}

=== CONTEXTO CRÍTICO ===
🎯 RECUERDA: Estás hablando con un AGENTE DE SEGUROS, NO con el cliente final.
🎯 Tu trabajo es ASESORAR AL AGENTE sobre cómo presentar y cerrar la venta.
🎯 NUNCA te dirijas directamente al cliente. Siempre habla AL AGENTE.

=== CONTEXTO DE PRESENTACIÓN ===
CLIENTE DEL AGENTE: {state.cliente.nombre}
COTIZACIONES CALCULADAS:
{cotizaciones_texto}{info_producto}

ÚLTIMO MENSAJE DEL AGENTE: "{state.mensaje_usuario}"

=== TU TAREA ===
Asesora al agente sobre cómo manejar esta situación:

- Si pregunta por detalles → Dale argumentos para explicar diferencias
- Si menciona dudas del cliente → Proporciona técnicas de manejo de objeciones
- Si el cliente muestra interés → Guía al agente hacia técnicas de cierre
- Si hay objeciones → Dale scripts específicos para manejarlas
- Si está indeciso → Sugiere cómo crear urgencia apropiada

EJEMPLOS DE RESPUESTAS CORRECTAS:
❌ MAL: "Perfecto Juan, estas son tus opciones..."
✅ BIEN: "Te sugiero presentar a Juan estas opciones de esta manera..."

❌ MAL: "¿Cuál te gusta más?"
✅ BIEN: "Pregúntale cuál opción le parece más atractiva y explora el por qué..."

IMPORTANTE:
- Habla SIEMPRE al agente, nunca al cliente
- Usa "te sugiero", "deberías decirle", "explícale que"
- Proporciona scripts y argumentos concretos
- Máximo 6 líneas por respuesta
"""
    
    try:
        response_text = get_llm_response(
            prompt=prompt,
            system_prompt=None,
            stream=False
        )
        return response_text
    except:
        return f"Te sugiero presentar las {len(state.cotizaciones)} opciones a {state.cliente.nombre} destacando los beneficios de cada una. ¿Qué reacción tuvo al ver las cifras?"