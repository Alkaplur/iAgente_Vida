from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from models import EstadoBot, EstadoConversacion, Cliente, ContextoConversacional
from agents.orquestador import orquestador_node, route_to_agent
from agents.extractor import extraer_datos_cliente, resetear_contexto_pregunta
from agents.needs_based_selling import needs_based_selling_node  # ← AGREGAR ESTA LÍNEA
from groq import Groq
from config import settings
import os
from agents.instructions_loader import cargar_instrucciones_cached
from agents.llm_client import get_llm_response


# Configurar tracing si está disponible
if os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Cliente Groq
if settings.use_openai:
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
else:
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)


def _manejar_respuesta_fallida(state: EstadoBot, contexto: ContextoConversacional) -> Dict[str, Any]:
    """
    Maneja cuando no se pudo interpretar la respuesta esperada
    """
    
    contexto.intentos_pregunta_actual += 1
    campo = contexto.ultimo_campo_solicitado
    
    print(f"❌ RESPUESTA NO VÁLIDA para {campo} (intento {contexto.intentos_pregunta_actual})")
    
    # Después de 2 intentos, hacer pregunta más específica
    if contexto.intentos_pregunta_actual >= 2:
        mensaje_ayuda = _generar_mensaje_ayuda_especifico(campo, state.mensaje_usuario)
        contexto.intentos_pregunta_actual = 0  # Reset para no entrar en bucle infinito
    else:
        mensaje_ayuda = _generar_aclaracion_rapida(campo, state.mensaje_usuario)
    
    return {
        "respuesta_bot": mensaje_ayuda,
        "cliente": state.cliente,
        "contexto": contexto,
        "etapa": EstadoConversacion.NEEDS_ANALYSIS
    }

def _generar_mensaje_ayuda_especifico(campo: str, mensaje_usuario: str) -> str:
    """Ayuda específica para agentes sobre datos de clientes"""
    
    ayudas = {
        "num_dependientes": f"No pude entender '{mensaje_usuario}' como número de dependientes de tu cliente. Responde SOLO con un número:\n• '0' si no tiene dependientes\n• '2' si tiene 2 hijos\n• '3' si tiene 3 personas a cargo",
        
        "edad": f"No reconocí '{mensaje_usuario}' como edad válida de tu cliente. Necesito SOLO un número entre 18 y 80.\nEjemplo: '35' (sin 'años' ni otras palabras)",
        
        "ingresos_mensuales": f"No pude interpretar '{mensaje_usuario}' como ingresos de tu cliente. Dime SOLO la cantidad mensual en euros.\nEjemplos: '2500', '3000', '4500'",
        
        "nombre": f"Disculpa, no capté bien el nombre de tu cliente. Escribe el nombre completo claramente.\nEjemplo: 'Juan Pérez' o 'María González'",
        
        "profesion": f"No entendí bien la profesión de tu cliente. Sé más específico.\nEjemplos: 'ingeniero', 'médico', 'profesor', 'comercial'"
    }
    
    return ayudas.get(campo, f"Disculpa, no entendí la información sobre tu cliente. ¿Podrías ser más específico?")

def _generar_aclaracion_rapida(campo: str, mensaje_usuario: str) -> str:
    """Aclaraciones para agentes sobre datos de clientes"""
    
    aclaraciones = {
        "num_dependientes": f"¿Tu cliente tiene {mensaje_usuario} dependientes? Confirma con solo el número (0, 1, 2, etc.)",
        
        "edad": f"¿Tu cliente tiene {mensaje_usuario} años? Escribe solo la edad en números.",
        
        "ingresos_mensuales": f"¿Los ingresos de tu cliente son {mensaje_usuario} euros mensuales? Escribe solo la cantidad.",
        
        "nombre": f"¿Tu cliente se llama {mensaje_usuario}? Si es correcto, confirma. Si no, escribe el nombre completo.",
        
        "profesion": f"¿Tu cliente trabaja como {mensaje_usuario}? Confirma o especifica mejor la profesión."
    }
    
    return aclaraciones.get(campo, f"¿Te refieres a '{mensaje_usuario}' para tu cliente? Por favor confirma.")


def _solicitar_siguiente_dato(cliente: Cliente, campo: str, contexto: ContextoConversacional) -> Dict[str, Any]:
    """
    Solicita el siguiente dato faltante actualizando el contexto
    """
    
    pregunta = _generar_pregunta_inteligente(cliente, campo)
    
    # Actualizar contexto
    contexto.ultimo_campo_solicitado = campo
    contexto.ultima_pregunta = pregunta
    contexto.esperando_respuesta = True
    contexto.intentos_pregunta_actual = 0
    contexto.tipo_respuesta_esperada = _determinar_tipo_respuesta(campo)
    
    print(f"   Acción: Preguntando por {campo}")
    
    return {
        "respuesta_bot": pregunta,
        "cliente": cliente,
        "contexto": contexto,
        "etapa": EstadoConversacion.NEEDS_ANALYSIS
    }

def _generar_recomendacion_final(cliente: Cliente, contexto: ContextoConversacional) -> Dict[str, Any]:
    """
    Genera la recomendación final cuando todos los datos están completos
    """
    
    recomendacion = _generar_recomendacion_producto(cliente)
    mensaje_recomendacion = _presentar_recomendacion(cliente, recomendacion)
    
    # Resetear contexto
    contexto_limpio = resetear_contexto_pregunta(contexto)
    
    print(f"   Acción: Recomendando producto {recomendacion.tipo_cobertura}")
    
    return {
        "respuesta_bot": mensaje_recomendacion,
        "cliente": cliente,
        "contexto": contexto_limpio,
        "recomendacion_producto": recomendacion,
        "etapa": EstadoConversacion.COTIZACION
    }

def _determinar_tipo_respuesta(campo: str) -> str:
    """Determina qué tipo de respuesta esperamos"""
    
    tipos = {
        "nombre": "texto",
        "edad": "numero",
        "num_dependientes": "numero", 
        "ingresos_mensuales": "numero",
        "profesion": "texto",
        "estado_civil": "opcion",
        "nivel_ahorro": "numero"
    }
    
    return tipos.get(campo, "texto")

def _generar_pregunta_inteligente(cliente: Cliente, dato_faltante: str) -> str:
    """Genera preguntas para AGENTES sobre sus CLIENTES"""
    
    preguntas = {
        "nombre": "¡Hola! Para ayudarte mejor con la venta, ¿cómo se llama tu cliente?",
        
        "edad": f"Perfecto. ¿Qué edad tiene {cliente.nombre}? (necesito el número exacto para calcular las primas correctas)",
        
        "num_dependientes": f"¿{cliente.nombre} tiene hijos o personas que dependan económicamente de él/ella? Dime cuántos (número exacto del 0 al 10)",
        
        "ingresos_mensuales": f"Para proponer productos acordes a su capacidad, ¿cuáles son los ingresos mensuales aproximados de {cliente.nombre}? (en euros)",
        
        "profesion": f"¿A qué se dedica profesionalmente {cliente.nombre}? Algunas profesiones tienen tarifas especiales o restricciones."
    }
    
    return preguntas.get(dato_faltante, f"¿Podrías contarme sobre {dato_faltante} de tu cliente?")

# IMPORTANTE: Agregar importación al inicio del archivo
from agents.extractor import extraer_datos_cliente, resetear_contexto_pregunta

def quote_node(state: EstadoBot) -> Dict[str, Any]:
    """
    Agente especializado en generar cotizaciones basadas en:
    - Datos del cliente
    - Recomendación de producto del needs-based selling
    """
    
    print(f"💰 QUOTE AGENT: Generando cotizaciones")
    print(f"   Cliente: {state.cliente.nombre}")
    print(f"   Recomendación: {state.recomendacion_producto.tipo_cobertura if state.recomendacion_producto else 'Sin recomendación'}")
    
    # Importar y usar el cotizador
    from agents.quote import calcular_cotizaciones, generar_presentacion
    
    try:
        # Generar cotizaciones basadas en cliente + recomendación
        cotizaciones = calcular_cotizaciones(state.cliente, state.recomendacion_producto)
        
        # Generar presentación de las cotizaciones
        mensaje_cotizaciones = generar_presentacion(state.cliente, cotizaciones)
        
        print(f"   Acción: {len(cotizaciones)} cotizaciones generadas")
        
        return {
            "respuesta_bot": mensaje_cotizaciones,
            "cotizaciones": cotizaciones,
            "etapa": EstadoConversacion.PRESENTACION_PROPUESTA
        }
        
    except Exception as e:
        print(f"⚠️ Error generando cotizaciones: {e}")
        return {
            "respuesta_bot": f"Disculpa {state.cliente.nombre}, estoy teniendo un problema técnico generando las cotizaciones. ¿Podrías darme un momento?",
            "etapa": EstadoConversacion.COTIZACION
        }

def presentador_node(state: EstadoBot) -> Dict[str, Any]:
    """
    Agente especializado en:
    - Presentar cotizaciones de manera atractiva
    - Responder dudas sobre las opciones
    - Manejar objeciones
    - Guiar hacia el cierre
    """
    
    print(f"📊 PRESENTADOR: Manejando presentación")
    print(f"   Cliente: {state.cliente.nombre}")
    print(f"   Cotizaciones disponibles: {len(state.cotizaciones)}")
    print(f"   Mensaje: '{state.mensaje_usuario}'")
    
    # Analizar qué necesita el cliente
    respuesta = _manejar_presentacion_y_dudas(state)
    
    return {
        "respuesta_bot": respuesta,
        "etapa": EstadoConversacion.PRESENTACION_PROPUESTA
    }

# ============= FUNCIONES AUXILIARES =============

def _extraer_informacion_cliente(cliente: Cliente, mensaje: str) -> Cliente:
    """Usar el agente extractor especializado"""
    return extraer_datos_cliente(cliente, mensaje)

def _identificar_datos_faltantes(cliente: Cliente) -> list:
    """Identifica datos esenciales que faltan"""
    
    esenciales = {
        "nombre": cliente.nombre,
        "edad": cliente.edad,
        "num_dependientes": cliente.num_dependientes,
        "ingresos_mensuales": cliente.ingresos_mensuales,
        "profesion": cliente.profesion
    }
    
    return [campo for campo, valor in esenciales.items() if valor is None]


    """Genera pregunta contextual para obtener el dato faltante"""
    
    preguntas = {
        "nombre": "¡Hola! Para personalizar mejor mi asesoría, ¿cómo te llamas?",
        "edad": f"Perfecto, {cliente.nombre}. ¿Qué edad tienes? Es importante para calcular las primas.",
        "num_dependientes": "¿Tienes hijos o personas que dependan económicamente de ti? Es fundamental para determinar la cobertura.",
        "ingresos_mensuales": "Para diseñar un seguro acorde a tu capacidad, ¿cuáles son tus ingresos mensuales aproximados?",
        "profesion": "¿A qué te dedicas profesionalmente? Algunas profesiones tienen condiciones especiales."
    }
    
    return preguntas.get(dato_faltante, f"¿Podrías contarme sobre {dato_faltante}?")

def _generar_recomendacion_producto(cliente: Cliente):
    """Genera recomendación de producto usando needs-based selling"""
    
    from models import RecomendacionProducto
    
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

def _presentar_recomendacion(cliente: Cliente, recomendacion) -> str:
    """Presenta la recomendación de producto de manera persuasiva usando instrucciones"""
    
    # Cargar instrucciones del needs-based selling
    instrucciones_needs_based = cargar_instrucciones_cached('needs_based')
    
    prompt = f"""
{instrucciones_needs_based}

=== TAREA ESPECÍFICA: PRESENTAR RECOMENDACIÓN ===

CLIENTE: {cliente.nombre}, {cliente.edad} años, {cliente.num_dependientes} dependientes, €{cliente.ingresos_mensuales}/mes

RECOMENDACIÓN GENERADA:
- Tipo: {recomendacion.tipo_cobertura}
- Cobertura: {recomendacion.cobertura_principal}
- Monto: €{recomendacion.monto_recomendado:,.0f}
- Justificación: {recomendacion.justificacion}

=== TU TAREA ===
Presenta esta recomendación siguiendo las técnicas de needs-based selling:

1. Conecta con las necesidades emocionales del cliente
2. Explica por qué es perfecta para su situación específica
3. Crea urgencia ética apropiada
4. Incluye una llamada a la acción suave
5. Máximo 5 líneas, tono profesional y persuasivo

Usa las técnicas de las instrucciones para crear urgencia y conectar emocionalmente.
"""
    
    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return f"Perfecto {cliente.nombre}, he analizado tu perfil y te recomiendo una cobertura {recomendacion.tipo_cobertura}. ¿Te gustaría que te prepare algunas cotizaciones?"

def _manejar_presentacion_y_dudas(state: EstadoBot) -> str:
    """Maneja la presentación de cotizaciones y responde dudas usando instrucciones"""
    
    if not state.cotizaciones:
        return "Permíteme generar las cotizaciones para ti..."
    
    # Cargar instrucciones del presentador
    instrucciones_presentador = cargar_instrucciones_cached('presentador')
    
    # Usar IA para manejar la conversación de presentación
    cotizaciones_texto = "\n".join([
        f"- {cot.tipo_plan}: €{cot.prima_mensual}/mes, Cobertura: €{cot.cobertura_fallecimiento:,.0f}"
        for cot in state.cotizaciones
    ])
    
    prompt = f"""
{instrucciones_presentador}

=== CONTEXTO DE PRESENTACIÓN ===
CLIENTE: {state.cliente.nombre}
COTIZACIONES DISPONIBLES:
{cotizaciones_texto}

ÚLTIMO MENSAJE DEL CLIENTE: "{state.mensaje_usuario}"

=== TU TAREA ===
Responde como especialista en cierre siguiendo las instrucciones del Presentador:

- Si pregunta por detalles → explica las diferencias usando técnicas de contraste
- Si tiene dudas → resuelve con confianza y maneja objeciones
- Si muestra interés → guía hacia el siguiente paso con técnicas de cierre
- Si pone objeciones → usa las técnicas específicas de manejo de objeciones
- Si está indeciso → aplica técnicas de creación de urgencia apropiadas

Máximo 6 líneas, tono persuasivo pero no agresivo.
"""
    
    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return f"Tienes {len(state.cotizaciones)} opciones excelentes, {state.cliente.nombre}. ¿Qué te gustaría saber sobre ellas?"

def _manejar_presentacion_y_dudas(state: EstadoBot) -> str:
    """Maneja la presentación de cotizaciones y responde dudas"""
    
    if not state.cotizaciones:
        return "Permíteme generar las cotizaciones para ti..."
    
    # Usar IA para manejar la conversación de presentación
    cotizaciones_texto = "\n".join([
        f"- {cot.tipo_plan}: €{cot.prima_mensual}/mes, Cobertura: €{cot.cobertura_fallecimiento:,.0f}"
        for cot in state.cotizaciones
    ])
    
    prompt = f"""
    Eres iAgente_Vida presentando cotizaciones.
    
    Cliente: {state.cliente.nombre}
    Cotizaciones disponibles:
    {cotizaciones_texto}
    
    Último mensaje del cliente: "{state.mensaje_usuario}"
    
    Responde profesionalmente:
    - Si pregunta por detalles, explica las diferencias
    - Si tiene dudas, resuelve con confianza
    - Si muestra interés, guía hacia el siguiente paso
    - Si pone objeciones, maneja con empatía
    
    Máximo 6 líneas.
    """
    
    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return f"Tienes {len(state.cotizaciones)} opciones excelentes, {state.cliente.nombre}. ¿Qué te gustaría saber sobre ellas?"

# ============= CREAR EL GRAFO =============

def crear_grafo():
    """Crea el grafo multi-agente SIN bucles automáticos"""
    
    workflow = StateGraph(EstadoBot)
    
    # Añadir todos los nodos
    workflow.add_node("orquestador", orquestador_node)
    workflow.add_node("needs_based_selling", needs_based_selling_node)
    workflow.add_node("quote", quote_node)
    workflow.add_node("presentador", presentador_node)
    
    # Punto de entrada: siempre el orquestador
    workflow.set_entry_point("orquestador")
    
    # El orquestador decide a qué agente enviar
    workflow.add_conditional_edges(
        "orquestador",
        route_to_agent,
        {
            "needs_based_selling": "needs_based_selling",
            "quote": "quote",
            "presentador": "presentador",
            "__end__": END
        }
    )
    
    # CAMBIO CLAVE: Los agentes NO vuelven al orquestador automáticamente
    # En su lugar, terminan y esperan el siguiente input del usuario
    workflow.add_edge("needs_based_selling", END)  # ← CAMBIO
    workflow.add_edge("quote", END)               # ← CAMBIO  
    workflow.add_edge("presentador", END)        # ← CAMBIO
    
    return workflow.compile()

# Crear instancia del grafo
graph = crear_grafo()