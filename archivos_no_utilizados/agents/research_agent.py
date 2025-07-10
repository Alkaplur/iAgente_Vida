from typing import Dict, Any, Optional
from models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion
from agents.instructions_loader import cargar_instrucciones_cached
from universal_llm_client import universal_llm
from llm_config import llm_config
from handoff_tools import handoff_manager
from agents.extractor import extraer_datos_cliente, resetear_contexto_pregunta, validar_interpretacion
import json

class ResearchAgent:
    """
    Agente de investigación especializado en análisis de necesidades y extracción de datos del cliente
    Migrado para usar el sistema LangGraph con handoff tools
    """
    
    def __init__(self, agent_name: str = "research_agent"):
        self.agent_name = agent_name
        self.config = llm_config.get_config(agent_name)
        self.instructions = cargar_instrucciones_cached('needs_based')
        
    def invoke(self, state: EstadoBot) -> Dict[str, Any]:
        """
        Procesa el análisis de necesidades del cliente y extrae información relevante
        """
        
        print(f"🔍 RESEARCH AGENT: Iniciando análisis de necesidades")
        print(f"   Cliente: {state.cliente.nombre or 'Sin nombre'}")
        print(f"   Mensaje: '{state.mensaje_usuario}'")
        
        # Obtener contexto de handoff del supervisor
        handoff_context = handoff_manager.get_handoff_context(self.agent_name)
        task_description = handoff_context.get('task', 'Análisis de necesidades')
        
        print(f"   Tarea asignada: {task_description}")
        
        # Extraer información del cliente
        cliente_actualizado, hubo_cambios = extraer_datos_cliente(
            state.cliente, 
            state.mensaje_usuario, 
            state.contexto
        )
        
        # Evaluar si necesitamos más información
        missing_fields = self._identify_missing_fields(cliente_actualizado)
        
        if missing_fields:
            # Necesitamos más información
            return self._request_more_information(
                cliente_actualizado, 
                missing_fields, 
                state.contexto,
                hubo_cambios
            )
        else:
            # Información completa, pasar a cotización
            return self._complete_research_phase(
                cliente_actualizado,
                state.contexto,
                hubo_cambios
            )
    
    def _identify_missing_fields(self, cliente: Cliente) -> Dict[str, Any]:
        """Identifica campos esenciales que faltan"""
        
        essential_fields = {
            "nombre": cliente.nombre,
            "edad": cliente.edad,
            "num_dependientes": cliente.num_dependientes,
            "ingresos_mensuales": cliente.ingresos_mensuales,
            "profesion": cliente.profesion
        }
        
        missing = {field: value for field, value in essential_fields.items() if value is None}
        
        print(f"   Campos faltantes: {list(missing.keys())}")
        print(f"   Completitud: {((5 - len(missing)) / 5) * 100:.0f}%")
        
        return missing
    
    def _request_more_information(
        self, 
        cliente: Cliente, 
        missing_fields: Dict[str, Any], 
        contexto: ContextoConversacional,
        hubo_cambios: bool
    ) -> Dict[str, Any]:
        """Solicita información faltante del cliente"""
        
        # Tomar el primer campo faltante
        next_field = list(missing_fields.keys())[0]
        
        # Generar pregunta contextual
        question = self._generate_contextual_question(cliente, next_field, hubo_cambios)
        
        # Actualizar contexto
        contexto.ultimo_campo_solicitado = next_field
        contexto.ultima_pregunta = question
        contexto.esperando_respuesta = True
        contexto.intentos_pregunta_actual = 0
        contexto.tipo_respuesta_esperada = self._get_expected_response_type(next_field)
        
        print(f"   Preguntando por: {next_field}")
        
        return {
            "respuesta_bot": question,
            "cliente": cliente,
            "contexto": contexto,
            "etapa": EstadoConversacion.NEEDS_ANALYSIS,
            "agente_activo": self.agent_name
        }
    
    def _complete_research_phase(
        self, 
        cliente: Cliente, 
        contexto: ContextoConversacional,
        hubo_cambios: bool
    ) -> Dict[str, Any]:
        """Completa la fase de investigación y genera recomendación"""
        
        # Generar recomendación de producto
        recommendation = self._generate_product_recommendation(cliente)
        
        # Generar respuesta usando LLM
        response = self._generate_completion_response(cliente, recommendation, hubo_cambios)
        
        # Resetear contexto
        contexto_limpio = resetear_contexto_pregunta(contexto)
        
        print(f"   Investigación completada")
        print(f"   Recomendación: {recommendation.tipo_cobertura}")
        
        # Preparar handoff a cotización
        return {
            "respuesta_bot": response,
            "cliente": cliente,
            "contexto": contexto_limpio,
            "recomendacion_producto": recommendation,
            "etapa": EstadoConversacion.COTIZACION,
            "agente_activo": "quote_agent",
            "handoff_context": {
                "handoff_type": "quote",
                "task": "Generar cotizaciones basadas en análisis completo",
                "next_agent": "quote_agent",
                "context": {
                    "client_profile": cliente.dict(),
                    "recommendation": recommendation.dict()
                }
            }
        }
    
    def _generate_contextual_question(self, cliente: Cliente, field: str, hubo_cambios: bool) -> str:
        """Genera preguntas contextuales para obtener información del cliente"""
        
        # Contexto para el agente
        context = {
            "client_name": cliente.nombre,
            "field_requesting": field,
            "has_changes": hubo_cambios,
            "current_client_data": cliente.dict()
        }
        
        # Usar LLM para generar pregunta natural
        messages = [
            {
                "role": "user",
                "content": f"""
Genera una pregunta natural y profesional para obtener información sobre el campo '{field}' del cliente.

CONTEXTO:
- Cliente: {cliente.nombre or 'Sin nombre aún'}
- Campo a obtener: {field}
- Datos actuales: {cliente.dict()}
- Hubo cambios recientes: {hubo_cambios}

INSTRUCCIONES:
1. Pregunta específica y directa
2. Tono profesional pero cálido
3. Incluye el contexto del cliente si está disponible
4. Máximo 2 líneas

EJEMPLOS según campo:
- nombre: "¡Hola! Para personalizar mi asesoría, ¿cómo se llama tu cliente?"
- edad: "Perfecto. ¿Qué edad tiene [nombre]? Es importante para calcular las primas."
- num_dependientes: "¿[nombre] tiene hijos o personas que dependan económicamente de él/ella?"
- ingresos_mensuales: "Para proponer productos acordes, ¿cuáles son los ingresos mensuales de [nombre]?"
- profesion: "¿A qué se dedica profesionalmente [nombre]?"
"""
            }
        ]
        
        try:
            response = universal_llm.generate_response(
                config=self.config,
                messages=messages,
                system_prompt=self.instructions
            )
            return response.strip()
        except Exception as e:
            print(f"⚠️ Error generando pregunta: {e}")
            return self._fallback_question(field, cliente.nombre)
    
    def _fallback_question(self, field: str, client_name: Optional[str]) -> str:
        """Preguntas de fallback cuando falla el LLM"""
        
        name = client_name or "tu cliente"
        
        questions = {
            "nombre": "¡Hola! Para ayudarte mejor, ¿cómo se llama tu cliente?",
            "edad": f"¿Qué edad tiene {name}? Es importante para calcular las primas correctas.",
            "num_dependientes": f"¿{name} tiene hijos o personas que dependan económicamente de él/ella?",
            "ingresos_mensuales": f"¿Cuáles son los ingresos mensuales aproximados de {name}?",
            "profesion": f"¿A qué se dedica profesionalmente {name}?"
        }
        
        return questions.get(field, f"¿Podrías contarme sobre {field} de {name}?")
    
    def _get_expected_response_type(self, field: str) -> str:
        """Determina el tipo de respuesta esperada"""
        
        types = {
            "nombre": "texto",
            "edad": "numero",
            "num_dependientes": "numero",
            "ingresos_mensuales": "numero",
            "profesion": "texto"
        }
        
        return types.get(field, "texto")
    
    def _generate_product_recommendation(self, cliente: Cliente):
        """Genera recomendación de producto usando lógica de negocio"""
        
        from models import RecomendacionProducto
        
        # Lógica basada en perfil del cliente
        if cliente.num_dependientes > 0 and cliente.edad < 45:
            return RecomendacionProducto(
                tipo_cobertura="completa",
                cobertura_principal="fallecimiento+invalidez",
                monto_recomendado=cliente.ingresos_mensuales * 12 * 10,
                justificacion=f"Con {cliente.num_dependientes} dependientes, necesitas protección integral",
                urgencia="alta",
                productos_adicionales=["invalidez", "enfermedades_graves"]
            )
        elif cliente.edad > 45:
            return RecomendacionProducto(
                tipo_cobertura="premium",
                cobertura_principal="vida+ahorro",
                monto_recomendado=cliente.ingresos_mensuales * 12 * 8,
                justificacion="Combinar protección con ahorro es la estrategia más inteligente",
                urgencia="media",
                productos_adicionales=["ahorro", "pensiones"]
            )
        else:
            return RecomendacionProducto(
                tipo_cobertura="básica",
                cobertura_principal="fallecimiento",
                monto_recomendado=cliente.ingresos_mensuales * 12 * 6,
                justificacion="Protección básica para comenzar a asegurar tu futuro",
                urgencia="media"
            )
    
    def _generate_completion_response(self, cliente: Cliente, recommendation, hubo_cambios: bool) -> str:
        """Genera respuesta de finalización usando LLM"""
        
        messages = [
            {
                "role": "user",
                "content": f"""
He completado el análisis de necesidades del cliente. Genera una respuesta profesional que:

1. Resuma los datos del cliente
2. Presente la recomendación de manera persuasiva
3. Indique que procederemos a las cotizaciones

DATOS DEL CLIENTE:
- Nombre: {cliente.nombre}
- Edad: {cliente.edad} años
- Dependientes: {cliente.num_dependientes}
- Ingresos: €{cliente.ingresos_mensuales}/mes
- Profesión: {cliente.profesion}

RECOMENDACIÓN:
- Tipo: {recommendation.tipo_cobertura}
- Cobertura: {recommendation.cobertura_principal}
- Monto: €{recommendation.monto_recomendado:,.0f}
- Justificación: {recommendation.justificacion}

TONO: Profesional, confiado, orientado a la acción
LONGITUD: Máximo 4 líneas
OBJETIVO: Crear confianza y anticipación para las cotizaciones
"""
            }
        ]
        
        try:
            response = universal_llm.generate_response(
                config=self.config,
                messages=messages,
                system_prompt=self.instructions
            )
            return response.strip()
        except Exception as e:
            print(f"⚠️ Error generando respuesta: {e}")
            return f"Perfecto {cliente.nombre}, he analizado tu perfil y te recomiendo una cobertura {recommendation.tipo_cobertura}. Permíteme prepararte las mejores cotizaciones."

def research_agent_node(state: EstadoBot) -> Dict[str, Any]:
    """Función node para LangGraph"""
    agent = ResearchAgent()
    return agent.invoke(state)