from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from models import EstadoBot, Cliente, EstadoConversacion
from agents.instructions_loader import cargar_instrucciones_cached
from universal_llm_client import universal_llm
from llm_config import llm_config
from handoff_tools import get_tools_for_agent, handoff_manager
import json

class SupervisorAgent:
    """
    Agente supervisor que coordina el flujo entre agentes especializados
    usando el patrón LangGraph con handoff tools
    """
    
    def __init__(self, agent_name: str = "supervisor"):
        self.agent_name = agent_name
        self.config = llm_config.get_config(agent_name)
        self.tools = get_tools_for_agent(agent_name)
        self.instructions = cargar_instrucciones_cached('supervisor')
    
    def invoke(self, state: EstadoBot) -> Dict[str, Any]:
        """
        Punto de entrada principal del supervisor
        Analiza el estado actual y decide qué agente debe actuar
        """
        print(f"🎯 SUPERVISOR: Analizando mensaje y estado actual")
        print(f"   Cliente: {state.cliente.nombre or 'Sin nombre'}")
        print(f"   Etapa: {state.etapa}")
        print(f"   Mensaje: '{state.mensaje_usuario}'")
        
        # Construir contexto para el supervisor
        context = self._build_context(state)
        
        # Generar respuesta del supervisor usando LLM
        supervisor_response = self._generate_supervisor_response(context, state)
        
        # Procesar respuesta y determinar próxima acción
        return self._process_supervisor_decision(supervisor_response, state)
    
    def _build_context(self, state: EstadoBot) -> Dict[str, Any]:
        """Construye contexto completo para el supervisor"""
        
        # Análisis del cliente
        client_completeness = self._analyze_client_completeness(state.cliente)
        
        # Análisis del mensaje del usuario
        message_analysis = self._analyze_message_intent(state.mensaje_usuario)
        
        # Análisis del flujo de conversación
        conversation_flow = self._analyze_conversation_flow(state)
        
        return {
            "client_completeness": client_completeness,
            "message_analysis": message_analysis,
            "conversation_flow": conversation_flow,
            "current_stage": state.etapa.value,
            "available_tools": [tool.name for tool in self.tools],
            "quotations_available": len(state.cotizaciones) > 0
        }
    
    def _analyze_client_completeness(self, cliente: Cliente) -> Dict[str, Any]:
        """Analiza qué tan completa está la información del cliente"""
        
        essential_fields = {
            "nombre": cliente.nombre,
            "edad": cliente.edad,
            "num_dependientes": cliente.num_dependientes,
            "ingresos_mensuales": cliente.ingresos_mensuales,
            "profesion": cliente.profesion
        }
        
        completed_fields = {k: v for k, v in essential_fields.items() if v is not None}
        missing_fields = [k for k, v in essential_fields.items() if v is None]
        
        return {
            "completion_percentage": len(completed_fields) / len(essential_fields) * 100,
            "completed_fields": list(completed_fields.keys()),
            "missing_fields": missing_fields,
            "ready_for_quotation": len(missing_fields) == 0
        }
    
    def _analyze_message_intent(self, message: str) -> Dict[str, Any]:
        """Analiza la intención del mensaje del usuario"""
        
        message_lower = message.lower()
        
        # Patrones de intención
        intent_patterns = {
            "new_analysis": ["analizar", "nuevo cliente", "seguro para", "cliente"],
            "provide_info": ["años", "hijos", "gana", "ingresos", "profesion"],
            "request_quotes": ["cotizar", "precio", "costo", "cuanto"],
            "ask_questions": ["que", "como", "por que", "cuando", "donde"],
            "show_interest": ["me interesa", "me gusta", "quiero", "perfecto"],
            "objections": ["caro", "mucho", "pero", "no puedo", "dificil"],
            "closing": ["si", "acepto", "contrato", "firmo", "de acuerdo"]
        }
        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                detected_intents.append(intent)
        
        return {
            "primary_intent": detected_intents[0] if detected_intents else "general",
            "all_intents": detected_intents,
            "message_type": self._classify_message_type(message_lower)
        }
    
    def _classify_message_type(self, message: str) -> str:
        """Clasifica el tipo de mensaje"""
        if "?" in message:
            return "question"
        elif any(word in message for word in ["si", "no", "acepto", "rechazo"]):
            return "decision"
        elif any(word in message for word in ["años", "hijos", "euros"]):
            return "information"
        else:
            return "general"
    
    def _analyze_conversation_flow(self, state: EstadoBot) -> Dict[str, Any]:
        """Analiza el flujo de la conversación"""
        
        return {
            "current_stage": state.etapa.value,
            "messages_count": len(state.mensajes),
            "has_recommendations": state.recomendacion_producto is not None,
            "has_quotations": len(state.cotizaciones) > 0,
            "active_agent": state.agente_activo
        }
    
    def _generate_supervisor_response(self, context: Dict[str, Any], state: EstadoBot) -> str:
        """Genera respuesta del supervisor usando LLM"""
        
        # Preparar mensajes para el LLM
        messages = [
            {
                "role": "user",
                "content": f"""
CONTEXTO DE SUPERVISIÓN:
- Cliente: {state.cliente.nombre or 'Sin nombre'}
- Etapa actual: {state.etapa.value}
- Mensaje usuario: "{state.mensaje_usuario}"
- Completitud cliente: {context['client_completeness']['completion_percentage']:.0f}%
- Campos faltantes: {context['client_completeness']['missing_fields']}
- Intención detectada: {context['message_analysis']['primary_intent']}
- Cotizaciones disponibles: {context['quotations_available']}

HERRAMIENTAS DISPONIBLES:
{json.dumps([tool.name for tool in self.tools], indent=2)}

DECISIÓN REQUERIDA:
Basándote en el contexto, decide qué agente debe manejar esta situación.
Responde en formato JSON con:
{{
  "action": "transfer_to_X" o "handle_directly",
  "target_agent": "research_agent/quote_agent/presenter_agent",
  "reasoning": "explicación de la decisión",
  "task_description": "descripción específica de la tarea",
  "context_for_agent": "contexto adicional para el agente"
}}
"""
            }
        ]
        
        try:
            response = universal_llm.generate_response(
                config=self.config,
                messages=messages,
                system_prompt=self.instructions,
                tools=None  # El supervisor no usa tools directamente en la respuesta
            )
            return response
            
        except Exception as e:
            print(f"⚠️ Error en supervisor LLM: {e}")
            return self._fallback_decision(context, state)
    
    def _fallback_decision(self, context: Dict[str, Any], state: EstadoBot) -> str:
        """Decisión de fallback cuando falla el LLM"""
        
        # Lógica determinista de fallback
        if context['client_completeness']['completion_percentage'] < 80:
            return json.dumps({
                "action": "transfer_to_research_agent",
                "target_agent": "research_agent",
                "reasoning": "Información del cliente incompleta",
                "task_description": "Completar información del cliente",
                "context_for_agent": f"Faltan: {context['client_completeness']['missing_fields']}"
            })
        
        elif not context['quotations_available']:
            return json.dumps({
                "action": "transfer_to_quote_agent",
                "target_agent": "quote_agent",
                "reasoning": "Información completa, necesita cotizaciones",
                "task_description": "Generar cotizaciones personalizadas",
                "context_for_agent": "Cliente listo para cotización"
            })
        
        else:
            return json.dumps({
                "action": "transfer_to_presenter_agent",
                "target_agent": "presenter_agent",
                "reasoning": "Tiene cotizaciones, manejar presentación",
                "task_description": "Presentar ofertas y manejar conversación",
                "context_for_agent": "Cotizaciones disponibles para presentar"
            })
    
    def _process_supervisor_decision(self, response: str, state: EstadoBot) -> Dict[str, Any]:
        """Procesa la decisión del supervisor y ejecuta la acción"""
        
        try:
            # Parsear respuesta JSON
            decision = json.loads(response)
            
            action = decision.get("action")
            target_agent = decision.get("target_agent")
            reasoning = decision.get("reasoning", "")
            task_description = decision.get("task_description", "")
            
            print(f"   🎯 Decisión: {action}")
            print(f"   🤖 Agente objetivo: {target_agent}")
            print(f"   💭 Razonamiento: {reasoning}")
            
            # Ejecutar handoff según la decisión
            if action == "transfer_to_research_agent":
                return self._handoff_to_research(task_description, state)
            
            elif action == "transfer_to_quote_agent":
                return self._handoff_to_quote(task_description, state)
            
            elif action == "transfer_to_presenter_agent":
                return self._handoff_to_presenter(task_description, state)
            
            elif action == "handle_directly":
                return self._handle_directly(task_description, state)
            
            else:
                return self._default_handoff(state)
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Error procesando decisión supervisor: {e}")
            return self._default_handoff(state)
    
    def _handoff_to_research(self, task_description: str, state: EstadoBot) -> Dict[str, Any]:
        """Transfiere control al agente de investigación"""
        
        handoff_data = {
            "handoff_type": "research",
            "task": task_description,
            "next_agent": "research_agent",
            "context": {
                "client_current_data": state.cliente.dict(),
                "message": state.mensaje_usuario
            }
        }
        
        return handoff_manager.process_handoff(handoff_data, state)
    
    def _handoff_to_quote(self, task_description: str, state: EstadoBot) -> Dict[str, Any]:
        """Transfiere control al agente de cotización"""
        
        handoff_data = {
            "handoff_type": "quote",
            "task": task_description,
            "next_agent": "quote_agent",
            "context": {
                "client_profile": state.cliente.dict(),
                "recommendation": state.recomendacion_producto.dict() if state.recomendacion_producto else None
            }
        }
        
        return handoff_manager.process_handoff(handoff_data, state)
    
    def _handoff_to_presenter(self, task_description: str, state: EstadoBot) -> Dict[str, Any]:
        """Transfiere control al agente presentador"""
        
        handoff_data = {
            "handoff_type": "presenter",
            "task": task_description,
            "next_agent": "presenter_agent",
            "context": {
                "client_profile": state.cliente.dict(),
                "quotations": [q.dict() for q in state.cotizaciones],
                "message": state.mensaje_usuario
            }
        }
        
        return handoff_manager.process_handoff(handoff_data, state)
    
    def _handle_directly(self, task_description: str, state: EstadoBot) -> Dict[str, Any]:
        """Maneja directamente sin transferir a otro agente"""
        
        direct_response = f"Entiendo que {task_description}. Permíteme ayudarte directamente."
        
        return {
            "respuesta_bot": direct_response,
            "agente_activo": "supervisor"
        }
    
    def _default_handoff(self, state: EstadoBot) -> Dict[str, Any]:
        """Handoff por defecto cuando no hay decisión clara"""
        
        # Lógica simple basada en la etapa actual
        if state.etapa == EstadoConversacion.INICIO:
            return self._handoff_to_research("Iniciar análisis de necesidades", state)
        
        elif state.etapa == EstadoConversacion.NEEDS_ANALYSIS:
            return self._handoff_to_research("Continuar análisis de necesidades", state)
        
        elif state.etapa == EstadoConversacion.COTIZACION:
            return self._handoff_to_quote("Generar o actualizar cotizaciones", state)
        
        else:
            return self._handoff_to_presenter("Manejar presentación y conversación", state)

# Función para crear instancia del supervisor
def create_supervisor_agent() -> SupervisorAgent:
    """Crea una instancia del agente supervisor"""
    return SupervisorAgent()

# Función node para LangGraph
def supervisor_node(state: EstadoBot) -> Dict[str, Any]:
    """Nodo supervisor para LangGraph"""
    supervisor = create_supervisor_agent()
    return supervisor.invoke(state)