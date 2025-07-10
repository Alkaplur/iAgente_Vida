from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from models import EstadoBot, EstadoConversacion
from agents.supervisor_agent import supervisor_node
from agents.research_agent import research_agent_node
from agents.quote_agent import quote_agent_node
from agents.presenter_agent import presenter_agent_node
from handoff_tools import handoff_manager
import os

# Configurar tracing si está disponible
if os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

def route_from_supervisor(state: EstadoBot) -> Literal["research_agent", "quote_agent", "presenter_agent", "END"]:
    """
    Función de routing que determina a dónde enviar el flujo desde el supervisor
    Basada en el handoff_context establecido por el supervisor
    """
    
    # Obtener contexto de handoff
    handoff_context = getattr(state, 'handoff_context', {})
    
    if not handoff_context:
        # Si no hay contexto de handoff, usar lógica de fallback
        print("⚠️ No hay contexto de handoff, usando lógica de fallback")
        return _fallback_routing(state)
    
    handoff_type = handoff_context.get('handoff_type')
    
    print(f"📋 Routing desde supervisor: {handoff_type}")
    
    if handoff_type == "research":
        return "research_agent"
    elif handoff_type == "quote":
        return "quote_agent"
    elif handoff_type == "presenter":
        return "presenter_agent"
    elif handoff_type == "complete":
        return "END"
    else:
        return _fallback_routing(state)

def _fallback_routing(state: EstadoBot) -> Literal["research_agent", "quote_agent", "presenter_agent", "END"]:
    """Lógica de routing de fallback"""
    
    # Analizar completitud del cliente
    client_complete = all([
        state.cliente.nombre,
        state.cliente.edad,
        state.cliente.num_dependientes is not None,
        state.cliente.ingresos_mensuales,
        state.cliente.profesion
    ])
    
    if not client_complete:
        return "research_agent"
    elif not state.cotizaciones:
        return "quote_agent"
    else:
        return "presenter_agent"

def agent_should_continue(state: EstadoBot) -> Literal["supervisor", "END"]:
    """
    Determina si un agente debe devolver control al supervisor o terminar
    """
    
    # Verificar si el agente completó su tarea
    handoff_context = getattr(state, 'handoff_context', {})
    
    # Si hay una nueva respuesta del bot, volver al supervisor para coordinación
    if hasattr(state, 'respuesta_bot') and state.respuesta_bot:
        return "supervisor"
    
    # Si la conversación está marcada como finalizada
    if state.etapa == EstadoConversacion.FINALIZADO:
        return "END"
    
    # Por defecto, volver al supervisor
    return "supervisor"

def create_langgraph_workflow() -> StateGraph:
    """
    Crea el workflow LangGraph con patrón supervisor
    """
    
    # Crear el grafo
    workflow = StateGraph(EstadoBot)
    
    # Añadir nodos
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("research_agent", research_agent_node)
    workflow.add_node("quote_agent", quote_agent_node)
    workflow.add_node("presenter_agent", presenter_agent_node)
    
    # Punto de entrada: supervisor
    workflow.set_entry_point("supervisor")
    
    # Routing condicional desde supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "research_agent": "research_agent",
            "quote_agent": "quote_agent",
            "presenter_agent": "presenter_agent",
            "END": END
        }
    )
    
    # Los agentes devuelven control al supervisor
    workflow.add_conditional_edges(
        "research_agent",
        agent_should_continue,
        {
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "quote_agent",
        agent_should_continue,
        {
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "presenter_agent",
        agent_should_continue,
        {
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    return workflow

# Crear instancia del grafo
def create_compiled_workflow():
    """Crea y compila el workflow"""
    workflow = create_langgraph_workflow()
    return workflow.compile()

# Función auxiliar para invocar el workflow
def invoke_workflow(user_message: str, current_state: EstadoBot) -> EstadoBot:
    """
    Invoca el workflow con un mensaje del usuario
    """
    
    # Actualizar estado con nuevo mensaje
    updated_state = current_state.copy()
    updated_state.mensaje_usuario = user_message
    
    # Crear workflow compilado
    compiled_workflow = create_compiled_workflow()
    
    # Invocar workflow
    result = compiled_workflow.invoke(updated_state)
    
    # Convertir resultado a EstadoBot
    return EstadoBot(**result)

# Función para conversación continua
def process_conversation_turn(user_message: str, state: EstadoBot) -> EstadoBot:
    """
    Procesa un turno de conversación completo
    """
    
    print(f"\n{'='*50}")
    print(f"👤 Usuario: {user_message}")
    print(f"{'='*50}")
    
    # Procesar mensaje
    result_state = invoke_workflow(user_message, state)
    
    # Mostrar respuesta
    if result_state.respuesta_bot:
        print(f"🤖 Bot: {result_state.respuesta_bot}")
    
    # Mostrar progreso
    _show_progress(result_state)
    
    return result_state

def _show_progress(state: EstadoBot):
    """Muestra progreso del proceso de venta"""
    
    if state.cliente.nombre:
        # Calcular completitud
        essential_fields = [
            state.cliente.nombre,
            state.cliente.edad,
            state.cliente.num_dependientes,
            state.cliente.ingresos_mensuales,
            state.cliente.profesion
        ]
        
        completed = sum(1 for field in essential_fields if field is not None)
        total = len(essential_fields)
        
        print(f"📊 Progreso cliente: {completed}/{total} campos completados")
        
        if state.cotizaciones:
            print(f"💰 Cotizaciones: {len(state.cotizaciones)} opciones disponibles")
        
        print(f"🎯 Etapa actual: {state.etapa.value}")
        print(f"🤖 Agente activo: {state.agente_activo or 'supervisor'}")

# Instancia global para usar en main.py
langgraph_workflow = create_compiled_workflow()