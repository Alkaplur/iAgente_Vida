from typing import Dict, Any, Tuple
from models import EstadoBot, EstadoConversacion, Cliente, RecomendacionProducto
from agents.instructions_loader import cargar_instrucciones_cached
from agents.extractor import extractor_agent
from groq import Groq
from config import settings
import asyncio

# Cliente Groq
groq_client = Groq(api_key=settings.groq_api_key)

def needs_based_selling_node(state: EstadoBot) -> Dict[str, Any]:
    """
    Agente conversacional natural usando LLM para needs-based selling
    No más preguntas estructuradas - conversación humana y consultiva
    """
    
    print(f"🎯 NEEDS-BASED SELLING: Conversación natural con LLM")
    print(f"   Cliente actual: {state.cliente.nombre or 'Datos por recopilar'}")
    print(f"   Mensaje: '{state.mensaje_usuario}'")
    print(f"   Datos disponibles: {_contar_datos_disponibles(state.cliente)}/5")
    
    # Cargar instrucciones desde archivo
    instrucciones = cargar_instrucciones_cached('needs_based')
    
    # 1. GENERAR RESPUESTA CONVERSACIONAL CON LLM
    respuesta_bot = _generar_respuesta_natural_llm(state, instrucciones)
    
    # 2. EXTRAER INFORMACIÓN DEL MENSAJE (EN PARALELO)
    cliente_actualizado = _extraer_datos_inteligente(state.cliente, state.mensaje_usuario)
    
    # 3. EVALUAR ESTADO Y DECIDIR SIGUIENTE PASO
    siguiente_estado, tiene_recomendacion = _evaluar_estado_conversacion(cliente_actualizado, respuesta_bot)
    
    # 4. GENERAR RECOMENDACIÓN SI ES MOMENTO APROPIADO
    recomendacion_producto = None
    if tiene_recomendacion:
        recomendacion_producto = _generar_recomendacion_producto(cliente_actualizado)
        print(f"   ✅ RECOMENDACIÓN GENERADA: {recomendacion_producto.tipo_cobertura}")
    
    print(f"   📊 Siguiente estado: {siguiente_estado}")
    
    return {
        "respuesta_bot": respuesta_bot,
        "cliente": cliente_actualizado,
        "recomendacion_producto": recomendacion_producto,
        "etapa": siguiente_estado,
        "contexto": state.contexto
    }

def _generar_respuesta_natural_llm(state: EstadoBot, instrucciones: str) -> str:
    """
    Genera respuesta completamente natural usando LLM con instrucciones consultivas
    """
    
    # Preparar contexto rico para el LLM
    datos_cliente = _preparar_resumen_cliente(state.cliente)
    
    prompt_conversacional = f"""
{instrucciones}

=== CONTEXTO ACTUAL ===
DATOS DEL CLIENTE HASTA AHORA:
{datos_cliente}

ÚLTIMO MENSAJE DEL CLIENTE/AGENTE:
"{state.mensaje_usuario}"

ETAPA ACTUAL: {state.etapa}

HISTORIAL RECIENTE:
{_obtener_historial_reciente(state)}

=== TU TAREA ===
Responde como InsuranceBot de manera natural y consultiva:

1. Si es el primer contacto → Saluda calurosamente y genera confianza
2. Si faltan datos → Pregunta de forma conversacional (no interrogatorio)
3. Si detectas preocupaciones → Aborda las emociones primero
4. Si tienes datos suficientes → Transiciona naturalmente a recomendación
5. Si hay objeciones → Manéjalas con empatía según las instrucciones

IMPORTANTE:
- Sé humano, no robótico
- Pregunta el "por qué" detrás de cada dato
- Crea urgencia ética cuando sea apropiado
- Máximo 4-5 líneas por respuesta
- Adapta el tono al contexto emocional
"""

    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        
        respuesta = response.choices[0].message.content.strip()
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

def _extraer_datos_inteligente(cliente: Cliente, mensaje: str) -> Cliente:
    """
    Extrae datos usando IA pero de forma más flexible y natural
    """
    
    prompt_extraccion = f"""
Eres un extractor de datos experto. Analiza este mensaje y actualiza SOLO los campos que encuentres información clara.

CLIENTE ACTUAL:
{cliente.model_dump()}

NUEVO MENSAJE:
"{mensaje}"

CAMPOS A BUSCAR:
- nombre: Nombres de personas mencionadas
- edad: Números seguidos de "años" o contexto de edad
- num_dependientes: Número de hijos, familia a cargo
- ingresos_mensuales: Cantidades de dinero mensuales
- profesion: Trabajo, ocupación mencionada

REGLAS:
1. Solo actualiza campos con información EXPLÍCITA
2. Mantén datos existentes intactos
3. Si hay dudas, NO actualices
4. Convierte todo a formato correcto (ej: "treinta años" → 30)

Devuelve el objeto Cliente actualizado manteniendo el mismo id_cliente.
"""

    try:
        result = asyncio.run(extractor_agent.run(prompt_extraccion))
        cliente_actualizado = result.data
        
        # Log de cambios
        cambios = _detectar_cambios(cliente, cliente_actualizado)
        if cambios:
            print(f"   📝 DATOS EXTRAÍDOS: {', '.join(cambios)}")
        
        return cliente_actualizado
        
    except Exception as e:
        print(f"   ⚠️ Error extrayendo datos: {e}")
        return cliente

def _detectar_cambios(cliente_original: Cliente, cliente_actualizado: Cliente) -> list:
    """Detecta qué campos cambiaron para logging"""
    
    cambios = []
    
    campos_importantes = [
        'nombre', 'edad', 'num_dependientes', 'ingresos_mensuales', 
        'profesion', 'estado_civil', 'nivel_ahorro'
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
    Respuesta de emergencia cuando falla el LLM
    """
    
    if not state.cliente.nombre:
        return "¡Hola! Soy tu asistente para seguros de vida. Cuéntame sobre tu cliente y te ayudo a crear la propuesta perfecta."
    
    datos_faltantes = _contar_datos_esenciales(state.cliente)
    
    if datos_faltantes < 3:
        return f"Perfecto, ya tengo información de {state.cliente.nombre}. ¿Puedes contarme un poco más sobre su situación para personalizar mejor la recomendación?"
    else:
        return f"Excelente, con la información de {state.cliente.nombre} puedo ayudarte. ¿Quieres que analice qué tipo de protección sería ideal?"

def _generar_recomendacion_producto(cliente: Cliente) -> RecomendacionProducto:
    """
    Genera recomendación de producto usando needs-based selling
    """
    
    # Lógica de recomendación basada en perfil
    if cliente.num_dependientes > 0 and cliente.edad < 45:
        # Familia joven - protección completa
        return RecomendacionProducto(
            tipo_cobertura="completa",
            cobertura_principal="fallecimiento+invalidez",
            monto_recomendado=cliente.ingresos_mensuales * 12 * 10,
            justificacion=f"Con {cliente.num_dependientes} dependientes, necesitas protección integral para asegurar su futuro",
            urgencia="alta",
            productos_adicionales=["invalidez", "enfermedades_graves"]
        )
    elif cliente.edad > 45:
        # Edad madura - ahorro + protección
        return RecomendacionProducto(
            tipo_cobertura="premium",
            cobertura_principal="vida+ahorro",
            monto_recomendado=cliente.ingresos_mensuales * 12 * 8,
            justificacion="A tu edad, combinar protección con ahorro es la estrategia más inteligente",
            urgencia="media",
            productos_adicionales=["ahorro", "pensiones"]
        )
    else:
        # Joven sin dependientes - protección básica
        return RecomendacionProducto(
            tipo_cobertura="básica",
            cobertura_principal="fallecimiento",
            monto_recomendado=cliente.ingresos_mensuales * 12 * 6,
            justificacion="Protección básica para comenzar a asegurar tu futuro",
            urgencia="media"
        )