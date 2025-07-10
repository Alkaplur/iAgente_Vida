from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from models import EstadoBot, EstadoConversacion
from dataclasses import dataclass

@dataclass
class HandoffRequest:
    """Estructura para solicitudes de handoff entre agentes"""
    target_agent: str
    task_description: str
    context: Dict[str, Any]
    priority: str = "normal"  # normal, high, urgent
    
@tool
def transfer_to_research_agent(
    task_description: str,
    client_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfiere control al agente de investigación/análisis de necesidades.
    
    Args:
        task_description: Descripción específica de la tarea
        client_context: Contexto adicional del cliente
    
    Returns:
        Instrucciones de handoff para el agente de investigación
    """
    return {
        "handoff_type": "research",
        "task": task_description,
        "context": client_context or "",
        "next_agent": "research_agent",
        "instructions": "Analiza las necesidades del cliente y extrae información relevante"
    }

@tool
def transfer_to_quote_agent(
    task_description: str,
    client_profile: Optional[str] = None,
    coverage_requirements: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfiere control al agente de cotización.
    
    Args:
        task_description: Descripción de la tarea de cotización
        client_profile: Perfil del cliente
        coverage_requirements: Requisitos de cobertura específicos
    
    Returns:
        Instrucciones de handoff para el agente de cotización
    """
    return {
        "handoff_type": "quote",
        "task": task_description,
        "client_profile": client_profile or "",
        "coverage_requirements": coverage_requirements or "",
        "next_agent": "quote_agent",
        "instructions": "Genera cotizaciones personalizadas basadas en el perfil del cliente"
    }

@tool
def transfer_to_presenter_agent(
    task_description: str,
    quotes_context: Optional[str] = None,
    client_objections: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfiere control al agente presentador/vendedor.
    
    Args:
        task_description: Descripción de la tarea de presentación
        quotes_context: Contexto de las cotizaciones disponibles
        client_objections: Objeciones del cliente a manejar
    
    Returns:
        Instrucciones de handoff para el agente presentador
    """
    return {
        "handoff_type": "presenter",
        "task": task_description,
        "quotes_context": quotes_context or "",
        "client_objections": client_objections or "",
        "next_agent": "presenter_agent",
        "instructions": "Presenta ofertas y maneja objeciones del cliente"
    }

@tool
def complete_conversation(
    summary: str,
    outcome: str,
    next_steps: Optional[str] = None
) -> Dict[str, Any]:
    """
    Completa la conversación con el cliente.
    
    Args:
        summary: Resumen de la conversación
        outcome: Resultado obtenido
        next_steps: Próximos pasos si aplica
    
    Returns:
        Instrucciones de finalización
    """
    return {
        "handoff_type": "complete",
        "summary": summary,
        "outcome": outcome,
        "next_steps": next_steps or "",
        "next_agent": "END",
        "instructions": "Conversación completada exitosamente"
    }

# Mapeo de herramientas disponibles para cada agente
AGENT_TOOLS = {
    "supervisor": [
        transfer_to_research_agent,
        transfer_to_quote_agent,
        transfer_to_presenter_agent,
        complete_conversation
    ],
    "research_agent": [
        transfer_to_quote_agent,
        transfer_to_presenter_agent,
        complete_conversation
    ],
    "quote_agent": [
        transfer_to_presenter_agent,
        transfer_to_research_agent,  # Por si necesita más información
        complete_conversation
    ],
    "presenter_agent": [
        transfer_to_quote_agent,  # Por si necesita nuevas cotizaciones
        transfer_to_research_agent,  # Por si necesita más información del cliente
        complete_conversation
    ]
}

def get_tools_for_agent(agent_name: str) -> List:
    """Obtiene las herramientas disponibles para un agente específico"""
    return AGENT_TOOLS.get(agent_name, [])

class HandoffManager:
    """Gestor de handoffs entre agentes"""
    
    def __init__(self):
        self.handoff_history: List[HandoffRequest] = []
    
    def process_handoff(self, handoff_data: Dict[str, Any], current_state: EstadoBot) -> Dict[str, Any]:
        """Procesa una solicitud de handoff"""
        
        handoff_type = handoff_data.get("handoff_type")
        next_agent = handoff_data.get("next_agent")
        
        # Registrar handoff
        self.handoff_history.append(HandoffRequest(
            target_agent=next_agent,
            task_description=handoff_data.get("task", ""),
            context=handoff_data
        ))
        
        # Actualizar estado según el tipo de handoff
        if handoff_type == "research":
            return {
                "etapa": EstadoConversacion.NEEDS_ANALYSIS,
                "agente_activo": "research_agent",
                "handoff_context": handoff_data
            }
        
        elif handoff_type == "quote":
            return {
                "etapa": EstadoConversacion.COTIZACION,
                "agente_activo": "quote_agent",
                "handoff_context": handoff_data
            }
        
        elif handoff_type == "presenter":
            return {
                "etapa": EstadoConversacion.PRESENTACION_PROPUESTA,
                "agente_activo": "presenter_agent",
                "handoff_context": handoff_data
            }
        
        elif handoff_type == "complete":
            return {
                "etapa": EstadoConversacion.FINALIZADO,
                "agente_activo": None,
                "handoff_context": handoff_data
            }
        
        return {}
    
    def get_handoff_context(self, agent_name: str) -> Dict[str, Any]:
        """Obtiene el contexto de handoff para un agente"""
        for handoff in reversed(self.handoff_history):
            if handoff.target_agent == agent_name:
                return handoff.context
        return {}

# Instancia global
handoff_manager = HandoffManager()