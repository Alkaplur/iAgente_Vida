from typing import Dict, Any, Tuple
try:
    from ..models import EstadoBot, EstadoConversacion, Cliente, RecomendacionProducto
    from .instructions_loader import cargar_instrucciones_cached
    from .extractor import extractor_agent
    from ..config import settings
    from .llm_client import get_llm_response
    from ..models import Cliente, ContextoConversacional
    from .extractor import extraer_datos_cliente
    from ..utils.productos_loader import obtener_productos_loader
    from ..utils.motor_cotizacion import obtener_motor_cotizacion
except ImportError:
    from models import EstadoBot, EstadoConversacion, Cliente, RecomendacionProducto
    from agents.instructions_loader import cargar_instrucciones_cached
    from agents.extractor import extractor_agent
    from config import settings
    from agents.llm_client import get_llm_response
    from models import Cliente, ContextoConversacional
    from agents.extractor import extraer_datos_cliente
    from utils.productos_loader import obtener_productos_loader
    from utils.motor_cotizacion import obtener_motor_cotizacion
from groq import Groq
import asyncio

# Cliente LLM configurado según settings
def _get_llm_client():
    """Obtiene el cliente LLM según la configuración"""
    if settings.llm_provider == "openai":
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)
    elif settings.llm_provider == "groq":
        return Groq(api_key=settings.groq_api_key)
    else:
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)  # fallback

llm_client = _get_llm_client()

def needs_based_selling_node(state: EstadoBot) -> Dict[str, Any]:
    """
    Agente conversacional natural usando LLM para needs-based selling
    No más preguntas estructuradas - conversación humana y consultiva
    """
    
    print(f"🎯 NEEDS-BASED: {state.cliente.nombre or 'Cliente'} | {_contar_datos_disponibles(state.cliente)}/5 datos")
    
    # Cargar instrucciones desde archivo
    instrucciones = cargar_instrucciones_cached('needs_based')
    
    # 1. GENERAR RESPUESTA CONVERSACIONAL CON LLM
    respuesta_bot = _generar_respuesta_natural_llm(state, instrucciones)
    
    # 2. EXTRAER INFORMACIÓN DEL MENSAJE (EN PARALELO)
    cliente_actualizado = _extraer_datos_inteligente(state.cliente, state.mensaje_usuario, state.contexto)
    
    # 3. EVALUAR ESTADO Y DECIDIR SIGUIENTE PASO
    siguiente_estado, tiene_recomendacion = _evaluar_estado_conversacion(cliente_actualizado, respuesta_bot)
    
    # 4. GENERAR RECOMENDACIÓN SI ES MOMENTO APROPIADO
    recomendacion_producto = None
    if tiene_recomendacion:
        recomendacion_producto = _generar_recomendacion_producto(cliente_actualizado)
    
    # Conservar recomendación existente si no se genera una nueva
    recomendacion_final = recomendacion_producto or state.recomendacion_producto
    
    return {
        "respuesta_bot": respuesta_bot,
        "cliente": cliente_actualizado,
        "recomendacion_producto": recomendacion_final,
        "etapa": siguiente_estado,
        "contexto": state.contexto,
        "cotizaciones": state.cotizaciones,  # Mantener cotizaciones existentes
        "mensajes": state.mensajes + [{"usuario": state.mensaje_usuario}, {"bot": respuesta_bot}] if state.mensajes else [{"usuario": state.mensaje_usuario}, {"bot": respuesta_bot}]
    }

def _generar_respuesta_natural_llm(state: EstadoBot, instrucciones: str) -> str:
    """
    Genera respuesta completamente natural usando LLM con instrucciones consultivas
    """
    
    # Preparar contexto rico para el LLM
    datos_cliente = _preparar_resumen_cliente(state.cliente)
    
    # Calcular recomendación de monto si tenemos datos suficientes
    monto_recomendado = ""
    validacion_capacidad = ""
    if state.cliente.ingresos_mensuales:
        ingresos_base = state.cliente.ingresos_mensuales
        # Aplicar rango 6-10 años según instrucciones (línea 151)
        if state.cliente.num_dependientes and state.cliente.num_dependientes > 0:
            # Protección familiar - usar rango alto (8-10 años) según instrucciones
            monto_min = ingresos_base * 12 * 6  # Mínimo del rango
            monto_max = ingresos_base * 12 * 10  # Máximo del rango
            monto_calc = ingresos_base * 12 * 8  # Valor medio para familia
            monto_recomendado = f"MONTO RECOMENDADO: €{monto_calc:,.0f} (rango €{monto_min:,.0f} - €{monto_max:,.0f}, 6-10 años de ingresos para protección familiar)"
        else:
            # Sin dependientes - usar rango bajo (6-7 años) según instrucciones
            monto_min = ingresos_base * 12 * 6  # Mínimo del rango
            monto_max = ingresos_base * 12 * 8  # Rango reducido sin dependientes
            monto_calc = ingresos_base * 12 * 6  # Valor conservador
            monto_recomendado = f"MONTO RECOMENDADO: €{monto_calc:,.0f} (rango €{monto_min:,.0f} - €{monto_max:,.0f}, 6-8 años de ingresos para protección básica)"
        
        # Validar capacidad de pago si tenemos datos de gastos
        validacion_capacidad = _validar_capacidad_pago(state.cliente)
    
    # Obtener instrucciones específicas del orquestador
    instrucciones_orquestador = ""
    if hasattr(state.contexto, 'instrucciones_agente') and state.contexto.instrucciones_agente:
        instrucciones_orquestador = f"\n🎯 INSTRUCCIONES ESPECÍFICAS DEL ORQUESTADOR:\n{state.contexto.instrucciones_agente}\n"
    elif hasattr(state.contexto, '__dict__') and 'instrucciones_agente' in state.contexto.__dict__:
        instrucciones_orquestador = f"\n🎯 INSTRUCCIONES ESPECÍFICAS DEL ORQUESTADOR:\n{state.contexto.__dict__['instrucciones_agente']}\n"
    
    prompt_conversacional = f"""
{instrucciones}

=== CONTEXTO CRÍTICO ===
🎯 RECUERDA: Estás hablando con un AGENTE DE SEGUROS, NO con el cliente final.
🎯 Tu trabajo es ASESORAR AL AGENTE sobre cómo manejar la venta con su cliente.
🎯 NUNCA te dirijas directamente al cliente. Siempre habla AL AGENTE.

=== DATOS DEL CLIENTE DEL AGENTE ===
{datos_cliente}

{monto_recomendado}

{validacion_capacidad}

=== MENSAJE DEL AGENTE ===
"{state.mensaje_usuario}"

ETAPA ACTUAL: {state.etapa}

HISTORIAL RECIENTE:
{_obtener_historial_reciente(state)}
{instrucciones_orquestador}

=== RECOMENDACIÓN DISPONIBLE ===
{monto_recomendado if monto_recomendado else "Necesito más datos para calcular monto específico"}

=== TU TAREA ===
Responde como iAgente_Vida ASESORANDO AL AGENTE:

1. Si faltan datos → Dile al agente qué debe preguntar al cliente y cómo
2. Si tienes datos suficientes → Sugiere al agente cómo presentar la recomendación
3. Si hay objeciones → Enseña al agente cómo manejarlas
4. Si pide montos → Proporciona cifras específicas y explica al agente cómo justificarlas

EJEMPLOS DE RESPUESTAS CORRECTAS:
❌ MAL: "Juan, te recomiendo un seguro de €300,000"
✅ BIEN: "Para Juan, te sugiero proponer una cobertura de €300,000. Explícale que..."

❌ MAL: "¿Cuántos dependientes tienes?"
✅ BIEN: "Pregúntale cuántos dependientes tiene. Esta información es clave porque..."

IMPORTANTE:
- Habla SIEMPRE al agente, nunca al cliente
- Usa "te sugiero", "deberías preguntarle", "explícale que"
- Proporciona argumentos que el agente puede usar
- Máximo 4-5 líneas por respuesta
- SIGUE LAS INSTRUCCIONES ESPECÍFICAS DEL ORQUESTADOR SI LAS HAY
"""

    try:
        response_text = get_llm_response(
            prompt=prompt_conversacional,
            system_prompt=None,    # o un texto si quieres un rol de system
            stream=False
        )
        
        return response_text
        print(f"   🤖 RESPUESTA LLM GENERADA: Longitud {len(respuesta)} chars")
        return respuesta
        
    except Exception as e:
        print(f"⚠️ Error en LLM conversacional: {e}")
        return _respuesta_fallback_natural(state)

def _preparar_resumen_cliente(cliente: Cliente) -> str:
    """
    Prepara resumen legible del cliente para el LLM
    """
    
    datos = []
    
    if cliente.nombre:
        datos.append(f"Nombre: {cliente.nombre}")
    if cliente.edad:
        datos.append(f"Edad: {cliente.edad} años")
    if cliente.num_dependientes is not None:
        if cliente.num_dependientes == 0:
            datos.append("Sin dependientes")
        else:
            datos.append(f"Dependientes: {cliente.num_dependientes}")
    if cliente.ingresos_mensuales:
        datos.append(f"Ingresos: €{cliente.ingresos_mensuales:,.0f}/mes")
    if cliente.profesion:
        datos.append(f"Profesión: {cliente.profesion}")
    if cliente.compromisos_financieros:
        datos.append(f"Compromisos: {cliente.compromisos_financieros}")
    
    if not datos:
        return "Sin datos del cliente aún"
    
    return " | ".join(datos)

def _obtener_historial_reciente(state: EstadoBot) -> str:
    """
    Obtiene las últimas 2-3 interacciones para contexto
    """
    
    if not state.mensajes:
        return "Primera interacción"
    
    # Tomar últimos 3 mensajes
    historial_reciente = state.mensajes[-3:]
    
    resumen = []
    for msg in historial_reciente:
        if 'usuario' in msg:
            resumen.append(f"Cliente: {msg['usuario']}")
        if 'bot' in msg:
            resumen.append(f"Bot: {msg['bot'][:50]}...")
    
    return "\n".join(resumen) if resumen else "Primera interacción"

def _extraer_datos_inteligente(cliente: Cliente, mensaje: str, contexto: ContextoConversacional = None) -> Cliente:
    """
    Extrae datos usando el extractor especializado
    """
    
    # Usar el contexto proporcionado o crear uno vacío
    if contexto is None:
        contexto = ContextoConversacional()
    
    try:
        # Importar el extractor especializado
        from .extractor import extraer_datos_cliente
        
        # Usar la función correcta del extractor
        cliente_actualizado, hubo_cambios = extraer_datos_cliente(cliente, mensaje, contexto)
        
        if hubo_cambios:
            # Log de cambios
            cambios = _detectar_cambios(cliente, cliente_actualizado)
            if cambios:
                print(f"   📝 DATOS EXTRAÍDOS: {len(cambios)} campos actualizados")
        
        return cliente_actualizado
        
    except Exception as e:
        print(f"   ⚠️ Error extrayendo datos: {e}")
        return cliente

def _detectar_cambios(cliente_original: Cliente, cliente_actualizado: Cliente) -> list:
    """Detecta qué campos cambiaron para logging"""
    
    cambios = []
    
    campos_importantes = [
        'nombre', 'edad', 'num_dependientes', 'ingresos_mensuales', 
        'profesion', 'estado_civil', 'nivel_ahorro', 'compromisos_financieros'
    ]
    
    for campo in campos_importantes:
        valor_original = getattr(cliente_original, campo)
        valor_nuevo = getattr(cliente_actualizado, campo)
        
        if valor_original != valor_nuevo:
            cambios.append(f"{campo}: {valor_original} → {valor_nuevo}")
    
    return cambios

def _evaluar_estado_conversacion(cliente: Cliente, respuesta_bot: str) -> Tuple[EstadoConversacion, bool]:
    """
    Evalúa el estado de la conversación y si es momento de recomendar
    """
    
    # Contar datos esenciales disponibles
    datos_esenciales = _contar_datos_esenciales(cliente)
    
    # Detectar si el LLM está pidiendo cotización o recomendando
    respuesta_lower = respuesta_bot.lower()
    
    # Patrones que indican transición a cotización
    patrones_cotizacion = [
        "recomiend", "propong", "suggest", "cotiz", "simul", 
        "calcul", "seguro de vida", "protección", "prima"
    ]
    
    solicita_cotizacion = any(patron in respuesta_lower for patron in patrones_cotizacion)
    
    # Lógica de decisión
    if datos_esenciales >= 4 and solicita_cotizacion:
        return EstadoConversacion.COTIZACION, True
    elif datos_esenciales >= 3:
        return EstadoConversacion.NEEDS_ANALYSIS, False
    else:
        return EstadoConversacion.NEEDS_ANALYSIS, False

def _contar_datos_esenciales(cliente: Cliente) -> int:
    """
    Cuenta cuántos datos esenciales tenemos
    """
    
    esenciales = [
        cliente.nombre,
        cliente.edad,
        cliente.num_dependientes,
        cliente.ingresos_mensuales,
        cliente.profesion
    ]
    
    return sum(1 for dato in esenciales if dato is not None)

def _contar_datos_disponibles(cliente: Cliente) -> int:
    """
    Cuenta datos disponibles para logging
    """
    return _contar_datos_esenciales(cliente)

def _respuesta_fallback_natural(state: EstadoBot) -> str:
    """
    Respuesta de emergencia cuando falla el LLM - MÁS INTELIGENTE
    """
    
    cliente = state.cliente
    mensaje = state.mensaje_usuario.lower()
    
    # Analizar el mensaje para dar respuesta contextual
    if "hola" in mensaje or "saludo" in mensaje:
        if not cliente.nombre:
            return "¡Hola! Soy tu asistente para seguros de vida. Para ayudarte mejor, cuéntame: ¿cómo se llama tu cliente y qué edad tiene?"
        else:
            return f"¡Hola! Ya tengo algunos datos de {cliente.nombre}. ¿Qué más necesitas saber sobre seguros de vida?"
    
    # Si pregunta qué necesita saber
    if "necesitas" in mensaje or "necesito" in mensaje or "que" in mensaje:
        datos_faltantes = []
        if not cliente.nombre:
            datos_faltantes.append("nombre")
        if not cliente.edad:
            datos_faltantes.append("edad")
        if cliente.num_dependientes is None:
            datos_faltantes.append("número de dependientes")
        if not cliente.ingresos_mensuales:
            datos_faltantes.append("ingresos mensuales")
        if not cliente.profesion:
            datos_faltantes.append("profesión")
        
        if datos_faltantes:
            return f"Para crear la mejor propuesta necesito conocer: {', '.join(datos_faltantes[:3])}. ¿Puedes empezar contándome el nombre y edad de tu cliente?"
        else:
            return "¡Perfecto! Ya tengo toda la información necesaria. ¿Quieres que genere una cotización personalizada?"
    
    # Si dice que quiere un seguro o pregunta por montos
    if "seguro" in mensaje or "protección" in mensaje or "monto" in mensaje or "cuánto" in mensaje or "precio" in mensaje:
        if not cliente.nombre:
            return "Perfecto, te ayudo con el seguro de vida. Para comenzar, necesito que me digas el nombre y edad de tu cliente."
        elif cliente.ingresos_mensuales:
            # Calcular recomendación específica
            ingresos_base = cliente.ingresos_mensuales
            if cliente.num_dependientes and cliente.num_dependientes > 0 and cliente.edad and cliente.edad < 45:
                monto_calc = ingresos_base * 12 * 10
                return f"Para {cliente.nombre}, te sugiero proponer una cobertura de €{monto_calc:,.0f} (10 años de ingresos). Explícale que con {cliente.num_dependientes} dependientes, necesita esta protección integral. ¿Cómo quieres presentarle esta cifra?"
            elif cliente.edad and cliente.edad > 45:
                monto_calc = ingresos_base * 12 * 8
                return f"Para {cliente.nombre} de {cliente.edad} años, te recomiendo proponer €{monto_calc:,.0f} (8 años de ingresos) combinando protección y ahorro. Dile que a su edad, esta estrategia es la más inteligente. ¿Te parece apropiado?"
            else:
                monto_calc = ingresos_base * 12 * 6
                return f"Para {cliente.nombre}, te sugiero una cobertura de €{monto_calc:,.0f} (6 años de ingresos) como protección básica. Explícale que es el punto de partida ideal para asegurar su futuro. ¿Quieres que te ayude a preparar la presentación?"
        else:
            return f"Excelente, {cliente.nombre} está interesado en protección. Pregúntale sobre su situación familiar y laboral. Estas preguntas te ayudarán a personalizar la recomendación."
    
    # Respuesta por defecto basada en datos disponibles
    datos_disponibles = _contar_datos_esenciales(cliente)
    
    if datos_disponibles == 0:
        return "Para ayudarte mejor, necesito conocer a tu cliente. ¿Puedes decirme su nombre, edad y situación familiar?"
    elif datos_disponibles < 3:
        return f"Perfecto, ya tengo algunos datos de {cliente.nombre or 'tu cliente'}. ¿Puedes contarme más sobre su situación para personalizar la recomendación?"
    else:
        return f"Excelente información sobre {cliente.nombre}. Con estos datos puedo sugerir la protección más adecuada. ¿Quieres ver las opciones?"

def _generar_recomendacion_producto(cliente: Cliente) -> RecomendacionProducto:
    """
    Genera recomendación de producto usando el motor de cotización y productos loader
    """
    
    # Obtener instancias de los nuevos módulos
    productos_loader = obtener_productos_loader()
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Calcular monto base usando el motor de cotización
    ingresos_base = cliente.ingresos_mensuales or 2000.0
    anos_recomendados, tipo_cobertura_recomendada = motor_cotizacion.recomendar_cobertura(cliente)
    monto_recomendado = ingresos_base * 12 * anos_recomendados
    
    # Obtener producto recomendado
    producto_recomendado = productos_loader.recomendar_producto(
        edad=cliente.edad or 30,
        num_dependientes=cliente.num_dependientes or 0,
        ingresos_mensuales=cliente.ingresos_mensuales,
        profesion=cliente.profesion
    )
    
    # Generar justificación basada en el producto recomendado
    if producto_recomendado:
        justificacion = f"{producto_recomendado.argumentos_venta}. {producto_recomendado.caracteristicas}"
    else:
        justificacion = "Protección personalizada según tu perfil y necesidades"
    
    # Determinar urgencia según perfil
    if cliente.num_dependientes and cliente.num_dependientes > 0:
        urgencia = "alta"
    elif cliente.edad and cliente.edad > 50:
        urgencia = "media"
    else:
        urgencia = "media"
    
    # Determinar tipo de cobertura
    if tipo_cobertura_recomendada == "fallecimiento+invalidez":
        tipo_cobertura = "completa"
    elif tipo_cobertura_recomendada == "vida+ahorro":
        tipo_cobertura = "premium"
    else:
        tipo_cobertura = "básica"
    
    # Obtener productos adicionales del producto recomendado
    productos_adicionales = []
    if producto_recomendado and producto_recomendado.coberturas_adicionales:
        productos_adicionales = producto_recomendado.coberturas_adicionales
    
    return RecomendacionProducto(
        tipo_cobertura=tipo_cobertura,
        cobertura_principal=tipo_cobertura_recomendada,
        monto_recomendado=monto_recomendado,
        justificacion=justificacion,
        urgencia=urgencia,
        productos_adicionales=productos_adicionales if productos_adicionales else None
    )


def _validar_capacidad_pago(cliente: Cliente) -> str:
    """
    Valida la capacidad de pago del cliente según las reglas de las instrucciones
    Implementa las reglas de validación (líneas 63-97 de needs_based_instructions.txt)
    """
    if not cliente.ingresos_mensuales or not cliente.gastos_fijos_mensuales:
        return "INFO VALIDACIÓN: No se puede validar capacidad de pago sin datos de ingresos y gastos."
    
    try:
        # Calcular ingreso disponible
        ingreso_disponible = cliente.ingresos_mensuales - cliente.gastos_fijos_mensuales
        
        if ingreso_disponible <= 0:
            return "⚠️ ADVERTENCIA: Los gastos fijos igualan o superan los ingresos. Se requiere análisis detallado del presupuesto."
        
        # Calcular límites de prima según instrucciones
        limite_recomendado = ingreso_disponible * 0.10  # 10% máximo recomendado
        limite_absoluto = ingreso_disponible * 0.15     # 15% límite absoluto
        
        resultado = f"""
📊 ANÁLISIS DE CAPACIDAD DE PAGO:
• Ingresos mensuales: €{cliente.ingresos_mensuales:,.0f}
• Gastos fijos: €{cliente.gastos_fijos_mensuales:,.0f}
• Ingreso disponible: €{ingreso_disponible:,.0f}
• Prima máxima recomendada (10%): €{limite_recomendado:,.0f}/mes
• Prima límite absoluto (15%): €{limite_absoluto:,.0f}/mes

💡 RECOMENDACIÓN: Ajustar cotizaciones para que la prima no exceda €{limite_recomendado:,.0f} mensuales.
"""
        return resultado
        
    except Exception as e:
        return f"⚠️ Error calculando capacidad de pago: {e}"