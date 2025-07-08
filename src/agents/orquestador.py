from typing import Dict, Any, Literal
from models import EstadoBot, EstadoConversacion, Cliente, RecomendacionProducto
from agents.instructions_loader import cargar_instrucciones_cached
from groq import Groq
from config import settings
from agents.llm_client import get_llm_response

# Cliente Groq
groq_client = Groq(api_key=settings.groq_api_key)

def orquestador_node(state: EstadoBot) -> Dict[str, Any]:
    print(f"🧠 ORQUESTADOR: Analizando situación actual")
    print(f"   Etapa: {state.etapa}")
    print(f"   Cliente: {state.cliente.nombre or 'Sin identificar'}")
    print(f"   Mensaje: '{state.mensaje_usuario}'")
    
    # Cargar instrucciones desde archivo
    instrucciones_orquestador = cargar_instrucciones_cached('orquestador')
    
    # Evaluar estado actual del proceso (sin log verboso)
    estado_proceso = _evaluar_estado_proceso(state)
    print(f"   📊 {estado_proceso['porcentaje_datos']}% datos | Intención: {estado_proceso['intencion_cliente']}")
    
    # Tomar decisión usando IA con instrucciones
    decision = _tomar_decision_inteligente(state, estado_proceso, instrucciones_orquestador)
    
    print(f"✅ ORQUESTADOR decide: {decision}")
    
    return {
        "next_agent": decision,
        "agente_activo": decision
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
    intencion_cliente = _analizar_intencion_cliente(state.mensaje_usuario)
    
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

def _analizar_intencion_cliente(mensaje: str) -> str:
    """Analiza la intención del cliente en su último mensaje"""
    
    if not mensaje or mensaje.strip() == "":
        return "neutral"
    
    # Cargar instrucciones para análisis de intención
    instrucciones_orquestador = cargar_instrucciones_cached('orquestador')
    
    prompt = f"""
    {instrucciones_orquestador}
    
    TAREA ESPECÍFICA: Analizar intención del mensaje
    
    Mensaje del cliente/agente: "{mensaje}"
    
    Clasifica en UNA de estas categorías:
    - "datos": Proporciona información personal del cliente
    - "consulta": Hace preguntas sobre seguros, precios, cobertura
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
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        intencion = response.choices[0].message.content.strip().lower()
        
        # Validar respuesta
        intenciones_validas = [
            "datos", "consulta", "interesado", "dudas", "objecion", 
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

def _tomar_decision_inteligente(state: EstadoBot, estado_proceso: Dict[str, Any], instrucciones: str) -> str:
    """Toma la decisión de qué agente debe actuar usando IA con instrucciones"""
    
    # Preparar contexto para la IA
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

=== TU DECISIÓN ===
Analiza la situación y decide qué agente debe actuar siguiendo las reglas de las instrucciones.

Responde SOLO con: needs_based_selling, quote, presentador, o FINISH
"""
    
    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        
        decision = response.choices[0].message.content.strip()
        
        # Validar decisión
        agentes_validos = ["needs_based_selling", "quote", "presentador", "FINISH"]
        if decision in agentes_validos:
            return decision
        else:
            print(f"⚠️ Decisión no válida: {decision}, usando fallback")
            return _decision_fallback(estado_proceso)
            
    except Exception as e:
        print(f"⚠️ Error en decisión IA: {e}, usando fallback")
        return _decision_fallback(estado_proceso)

def _decision_fallback(estado_proceso: Dict[str, Any]) -> str:
    """Lógica de fallback para decisiones cuando falla la IA"""
    
    # Si no hay datos completos o recomendación
    if not estado_proceso['datos_cliente_completos'] or not estado_proceso['tiene_recomendacion']:
        return "needs_based_selling"
    
    # Si hay datos y recomendación pero no cotizaciones
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