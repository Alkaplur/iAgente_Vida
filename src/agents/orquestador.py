from typing import Dict, Any, Literal
try:
    from ..models import EstadoBot, EstadoConversacion, Cliente, RecomendacionProducto
    from .instructions_loader import cargar_instrucciones_cached
    from ..config import settings
    from .llm_client import get_llm_response
except ImportError:
    from models import EstadoBot, EstadoConversacion, Cliente, RecomendacionProducto
    from agents.instructions_loader import cargar_instrucciones_cached
    from config import settings
    from agents.llm_client import get_llm_response
from groq import Groq



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

def orquestador_node(state: EstadoBot) -> Dict[str, Any]:
    print(f"🧠 ORQUESTADOR: {state.cliente.nombre or 'Cliente'} | {state.etapa}")
    
    # Cargar instrucciones desde archivo
    instrucciones_orquestador = cargar_instrucciones_cached('orquestador')
    
    # Evaluar estado actual del proceso
    estado_proceso = _evaluar_estado_proceso(state)
    
    # Tomar decisión usando IA con instrucciones
    decision_data = _tomar_decision_inteligente(state, estado_proceso, instrucciones_orquestador)
    
    print(f"✅ ORQUESTADOR → {decision_data['next_agent']}")
    
    # Guardar instrucciones en el contexto conversacional
    if hasattr(state.contexto, "instrucciones_agente"):
        state.contexto.instrucciones_agente = decision_data.get("instructions", "")
    else:
        # Por si el modelo ContextoConversacional aún no tiene ese campo
        state.contexto.__dict__["instrucciones_agente"] = decision_data.get("instructions", "")
    
    # ACTUALIZAR EL ESTADO PARA EL ROUTING
    # Esto es crítico para que route_to_agent funcione correctamente
    return {
        "cliente": state.cliente,  # Mantener cliente
        "cotizaciones": state.cotizaciones,  # Mantener cotizaciones 
        "recomendacion_producto": state.recomendacion_producto,  # Mantener recomendación
        "contexto": state.contexto,  # Mantener contexto
        "etapa": state.etapa,  # Mantener etapa actual
        "mensaje_usuario": state.mensaje_usuario,  # Mantener mensaje
        "mensajes": state.mensajes,  # Mantener historial
        "next_agent": decision_data["next_agent"],  # ESTO ES LO CRÍTICO
        "agente_activo": decision_data["agente_activo"]
    }

def _evaluar_estado_proceso(state: EstadoBot) -> Dict[str, Any]:
    """Evalúa el estado actual del proceso de ventas"""
    
    # Evaluar completitud de datos del cliente
    datos_cliente = _evaluar_datos_cliente(state.cliente)
    
    # Evaluar si hay recomendación de producto
    tiene_recomendacion = state.recomendacion_producto is not None
    
    # Evaluar si hay cotizaciones
    tiene_cotizaciones = len(state.cotizaciones) > 0
    
    # Evaluar intención del último mensaje
    intencion_cliente = _analizar_intencion_cliente(state.mensaje_usuario, state.cliente)
    
    return {
        "datos_cliente_completos": datos_cliente["completos"],
        "porcentaje_datos": datos_cliente["porcentaje"],
        "datos_faltantes": datos_cliente["faltantes"],
        "tiene_recomendacion": tiene_recomendacion,
        "tiene_cotizaciones": tiene_cotizaciones,
        "intencion_cliente": intencion_cliente,
        "etapa_actual": state.etapa
    }

def _evaluar_datos_cliente(cliente: Cliente) -> Dict[str, Any]:
    """Evalúa qué datos del cliente tenemos y cuáles faltan"""
    
    # Datos esenciales para needs-based selling
    datos_esenciales = {
        "nombre": cliente.nombre,
        "edad": cliente.edad,
        "num_dependientes": cliente.num_dependientes,
        "ingresos_mensuales": cliente.ingresos_mensuales,
        "profesion": cliente.profesion
    }
    
    # Datos adicionales útiles
    datos_adicionales = {
        "estado_civil": cliente.estado_civil,
        #"nivel_ahorro": cliente.nivel_ahorro,
        "tiene_seguro_vida": cliente.tiene_seguro_vida,
        "percepcion_seguro": cliente.percepcion_seguro
    }
    
    # Calcular completitud
    esenciales_completos = sum(1 for v in datos_esenciales.values() if v is not None)
    adicionales_completos = sum(1 for v in datos_adicionales.values() if v is not None)
    
    total_campos = len(datos_esenciales) + len(datos_adicionales)
    total_completos = esenciales_completos + adicionales_completos
    
    porcentaje = int((total_completos / total_campos) * 100)
    
    # Identificar datos faltantes
    faltantes_esenciales = [k for k, v in datos_esenciales.items() if v is None]
    faltantes_adicionales = [k for k, v in datos_adicionales.items() if v is None]
    
    # Consideramos completos si tenemos todos los esenciales
    completos = len(faltantes_esenciales) == 0
    
    return {
        "completos": completos,
        "porcentaje": porcentaje,
        "faltantes": faltantes_esenciales + faltantes_adicionales,
        "faltantes_esenciales": faltantes_esenciales,
        "faltantes_adicionales": faltantes_adicionales
    }

def _analizar_intencion_cliente(mensaje: str, cliente: Cliente = None) -> str:
    """Analiza la intención del cliente usando IA inteligente"""
    
    if not mensaje or mensaje.strip() == "":
        return "neutral"
    
    try:
        # Usar el analizador inteligente
        from .intent_analyzer import analizar_intencion_completa
        
        analisis = analizar_intencion_completa(
            mensaje=mensaje,
            cliente=cliente,
            contexto_previo=None
        )
        
        print(f"🎯 Intención detectada: {analisis.intencion_principal}")
        if analisis.tipo_objecion:
            print(f"   📍 Objeción: {analisis.tipo_objecion}")
        
        return analisis.intencion_principal
        
    except Exception as e:
        print(f"❌ Error análisis inteligente: {e}")
        return _analizar_intencion_fallback(mensaje)


def _analizar_intencion_fallback(mensaje: str) -> str:
    """Fallback simple para análisis de intención"""
    
    instrucciones_orquestador = cargar_instrucciones_cached('orquestador')
    
    prompt = f"""
    {instrucciones_orquestador}
    
    TAREA ESPECÍFICA: Analizar intención del mensaje
    
    Mensaje del cliente/agente: "{mensaje}"
    
    Clasifica en UNA de estas categorías:
    - "datos": Proporciona información personal del cliente
    - "consulta": Hace preguntas sobre seguros, precios, cobertura
    - "consulta_monto": Pregunta específicamente por montos, precios o costos
    - "interesado": Muestra interés en cotizar o contratar
    - "dudas": Tiene dudas específicas sobre propuestas
    - "objecion": Pone objeciones (muy caro, no convence, etc.)
    - "acepta": Acepta una propuesta o quiere continuar
    - "rechaza": Rechaza definitivamente
    - "saludo": Saludo inicial o mensaje general
    - "neutral": No está claro o mensaje ambiguo
    
    Responde SOLO con la categoría (una palabra).
    """
    
    try:
        response_text = get_llm_response(
            prompt=prompt,
            system_prompt="Eres el orquestador y decides qué agente debe actuar.",
            stream=False
        )
        intencion = response_text.strip().lower()
        
        # Validar respuesta
        intenciones_validas = [
            "datos", "consulta", "consulta_monto", "interesado", "dudas", "objecion", "objecion_precio",
            "acepta", "rechaza", "saludo", "neutral"
        ]
        
        if intencion in intenciones_validas:
            return intencion
        else:
            print(f"⚠️ Intención no reconocida: {intencion}")
            return "neutral"
            
    except Exception as e:
        print(f"⚠️ Error analizando intención: {e}")
        return "neutral"

def _tomar_decision_inteligente(state: EstadoBot, estado_proceso: Dict[str, Any], instrucciones: str) -> Dict[str, str]:
    """Toma la decisión de qué agente debe actuar y devuelve instrucciones específicas."""

    # Nueva lógica: Si preguntan por montos específicos, dar respuesta concreta
    if estado_proceso["intencion_cliente"] == "consulta_monto":
        instrucciones_para_el_agente = (
            "El cliente pregunta por montos específicos. PROPORCIONA CIFRAS CONCRETAS. "
            "Si tienes ingresos del cliente, calcula la recomendación específica (6-10 años de ingresos según perfil). "
            "No des rangos generales, da montos específicos en euros. "
            "Justifica brevemente el cálculo. "
        )
        if state.etapa != EstadoConversacion.INICIO:
            instrucciones_para_el_agente += " No saludes nuevamente, continúa la conversación."

        return {
            "next_agent": "needs_based_selling",
            "agente_activo": "needs_based_selling",
            "instructions": instrucciones_para_el_agente
        }
    
    # Lógica original: falta solo capital_deseado
    faltantes = estado_proceso["datos_faltantes"]
    if len(faltantes) == 1 and "capital_deseado" in faltantes:
        instrucciones_para_el_agente = (
            "Calcula un rango estimado de capital asegurado (6-10 años de ingresos). "
            "Propon cifras concretas basadas en los datos del cliente. "
            "No repreguntes sin proponer rangos. "
        )
        if state.etapa != EstadoConversacion.INICIO:
            instrucciones_para_el_agente += " No saludes nuevamente, continúa la conversación."

        return {
            "next_agent": "needs_based_selling",
            "agente_activo": "needs_based_selling",
            "instructions": instrucciones_para_el_agente
        }

    # Forzar progresión si tenemos datos suficientes
    if estado_proceso['porcentaje_datos'] >= 80 and not estado_proceso['tiene_recomendacion']:
        instrucciones_para_el_agente = (
            "Tienes suficientes datos. GENERA UNA RECOMENDACIÓN ESPECÍFICA ahora. "
            "No pidas más datos, procede a recomendar cobertura y monto. "
        )
        if state.etapa != EstadoConversacion.INICIO:
            instrucciones_para_el_agente += " No saludes nuevamente, continúa la conversación."

        return {
            "next_agent": "needs_based_selling",
            "agente_activo": "needs_based_selling",
            "instructions": instrucciones_para_el_agente
        }
    
    # Forzar cotización si tenemos recomendación pero no cotizaciones
    if estado_proceso['tiene_recomendacion'] and not estado_proceso['tiene_cotizaciones']:
        return {
            "next_agent": "quote",
            "agente_activo": "quote",
            "instructions": "Genera cotización basada en la recomendación existente."
        }
    
    # LÓGICA ESPECIAL: Si es objeción de precio, volver al cotizador para ajustar
    if estado_proceso['intencion_cliente'] == "objecion_precio" and estado_proceso['tiene_cotizaciones']:
        return {
            "next_agent": "quote",
            "agente_activo": "quote",
            "instructions": "El cliente quiere ajustar las cotizaciones. Genera opciones más económicas."
        }
    
    # Si tenemos cotizaciones Y el usuario pregunta sobre detalles, ir al presentador
    if (estado_proceso['tiene_cotizaciones'] and 
        state.etapa in [EstadoConversacion.COTIZACION, EstadoConversacion.PRESENTACION_PROPUESTA] and
        estado_proceso['intencion_cliente'] in ['consulta', 'consulta_monto', 'dudas']):
        return {
            "next_agent": "presentador",
            "agente_activo": "presentador",
            "instructions": "El usuario pregunta sobre las cotizaciones. Responde específicamente y maneja la conversación."
        }
    
    # Si no, usar IA
    contexto = f"""
    {instrucciones}

    === SITUACIÓN ACTUAL ===
    ETAPA: {estado_proceso['etapa_actual']}
    CLIENTE: {state.cliente.nombre or 'Sin identificar'}
    DATOS COMPLETITUD: {estado_proceso['porcentaje_datos']}% completos
    DATOS FALTANTES ESENCIALES: {', '.join(estado_proceso['datos_faltantes'][:3]) if estado_proceso['datos_faltantes'] else 'Ninguno'}
    TIENE RECOMENDACIÓN: {'SÍ' if estado_proceso['tiene_recomendacion'] else 'NO'}
    TIENE COTIZACIONES: {'SÍ' if estado_proceso['tiene_cotizaciones'] else 'NO'}
    INTENCIÓN CLIENTE: {estado_proceso['intencion_cliente']}
    ÚLTIMO MENSAJE: "{state.mensaje_usuario}"

    === REGLAS DE PROGRESIÓN ===
    - Si datos >= 80% y no hay recomendación → needs_based_selling (forzar recomendación)
    - Si hay recomendación pero no cotización → quote
    - Si hay cotización → presentador
    - Si acepta/rechaza → FINISH

    === TU DECISIÓN ===
    Analiza la situación y decide qué agente debe actuar siguiendo las reglas de progresión.
    Responde SOLO con: needs_based_selling, quote, presentador, o FINISH
    """

    try:
        response_text = get_llm_response(
            prompt=contexto,
            system_prompt="Eres el orquestador y decides qué agente debe actuar.",
            stream=False
        )
        decision = response_text.strip()

        agentes_validos = ["needs_based_selling", "quote", "presentador", "FINISH"]
        if decision in agentes_validos:
            instrucciones_para_el_agente = ""
            if state.etapa != EstadoConversacion.INICIO:
                instrucciones_para_el_agente = "No saludes nuevamente, continúa la conversación."
            return {
                "next_agent": decision,
                "agente_activo": decision,
                "instructions": instrucciones_para_el_agente
            }
        else:
            print(f"⚠️ Decisión no válida: {decision}, usando fallback")
            decision = _decision_fallback(estado_proceso)
            return {
                "next_agent": decision,
                "agente_activo": decision,
                "instructions": ""
            }

    except Exception as e:
        print(f"⚠️ Error en decisión IA: {e}, usando fallback")
        decision = _decision_fallback(estado_proceso)
        return {
            "next_agent": decision,
            "agente_activo": decision,
            "instructions": ""
        }

def _decision_fallback(estado_proceso: Dict[str, Any]) -> str:
    """Lógica de fallback para decisiones cuando falla la IA"""
    
    # Datos esenciales mínimos para proceder
    datos_minimos = estado_proceso['porcentaje_datos'] >= 60  # Al menos 60% de datos
    
    # Si no hay datos mínimos
    if not datos_minimos:
        return "needs_based_selling"
    
    # Si hay datos mínimos pero no hay recomendación
    elif not estado_proceso['tiene_recomendacion']:
        return "needs_based_selling"
    
    # Si hay recomendación pero no cotizaciones
    elif not estado_proceso['tiene_cotizaciones']:
        return "quote"
    
    # Si hay cotizaciones
    elif estado_proceso['tiene_cotizaciones']:
        intencion = estado_proceso['intencion_cliente']
        if intencion in ["acepta", "rechaza"]:
            return "FINISH"
        else:
            return "presentador"
    
    # Default
    else:
        return "needs_based_selling"

def route_to_agent(state: EstadoBot) -> Literal["needs_based_selling", "quote", "presentador", "__end__"]:
    """
    Función de routing para LangGraph - determina el próximo nodo
    """
    
    next_agent = getattr(state, "next_agent", "needs_based_selling")
    
    print(f"🔀 ROUTING → {next_agent}")
    
    if next_agent == "FINISH":
        return "__end__"
    elif next_agent == "quote":
        return "quote"
    elif next_agent == "presentador":
        return "presentador"
    else:
        return "needs_based_selling"

def generar_resumen_decision(state: EstadoBot, decision: str) -> str:
    """Genera un resumen de la decisión tomada para logging"""
    
    estado_proceso = _evaluar_estado_proceso(state)
    
    return f"""
    🎯 DECISIÓN DEL ORQUESTADOR:
    ├── Agente seleccionado: {decision}
    ├── Razón: Datos {estado_proceso['porcentaje_datos']}%, Recomendación: {'SÍ' if estado_proceso['tiene_recomendacion'] else 'NO'}, Cotizaciones: {len(state.cotizaciones)}
    ├── Intención cliente: {estado_proceso['intencion_cliente']}
    └── Próxima acción: {"Recopilar datos/recomendar" if decision == "needs_based_selling" else "Cotizar" if decision == "quote" else "Presentar/cerrar" if decision == "presentador" else "Finalizar"}
    """

def _validar_progresion(state: EstadoBot, estado_proceso: Dict[str, Any], agente_decidido: str) -> None:
    """Valida que el orquestador esté progresando correctamente y no se atasque"""
    
    # Detectar si podríamos estar en un bucle
    if (estado_proceso['porcentaje_datos'] >= 80 and 
        not estado_proceso['tiene_recomendacion'] and 
        agente_decidido == "needs_based_selling"):
        print(f"   ⚠️  POSIBLE BUCLE: Datos suficientes ({estado_proceso['porcentaje_datos']}%) pero sin recomendación, enviando a needs_based_selling")
    
    if (estado_proceso['tiene_recomendacion'] and 
        not estado_proceso['tiene_cotizaciones'] and 
        agente_decidido != "quote"):
        print(f"   ⚠️  POSIBLE BUCLE: Hay recomendación pero no cotizaciones, debería ir a quote pero va a {agente_decidido}")
    
    if (estado_proceso['tiene_cotizaciones'] and 
        agente_decidido not in ["presentador", "FINISH"]):
        print(f"   ⚠️  POSIBLE BUCLE: Hay cotizaciones pero no va a presentador/FINISH, va a {agente_decidido}")
    
    # Log de progresión normal
    if agente_decidido == "quote" and estado_proceso['tiene_recomendacion']:
        print(f"   ✅ PROGRESIÓN CORRECTA: Recomendación → Cotización")
    elif agente_decidido == "presentador" and estado_proceso['tiene_cotizaciones']:
        print(f"   ✅ PROGRESIÓN CORRECTA: Cotización → Presentación")
    elif agente_decidido == "FINISH":
        print(f"   ✅ PROGRESIÓN CORRECTA: Finalizando conversación")

def validar_transicion(estado_actual: EstadoConversacion, agente_destino: str) -> bool:
    """Valida si la transición de estado es válida"""
    
    transiciones_validas = {
        EstadoConversacion.INICIO: ["needs_based_selling"],
        EstadoConversacion.NEEDS_ANALYSIS: ["needs_based_selling", "quote"],
        EstadoConversacion.COTIZACION: ["quote", "presentador"],
        EstadoConversacion.PRESENTACION_PROPUESTA: ["presentador", "FINISH"],
        EstadoConversacion.FINALIZADO: ["FINISH"]
    }
    
    return agente_destino in transiciones_validas.get(estado_actual, [])