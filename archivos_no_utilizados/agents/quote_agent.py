from typing import Dict, Any, List
from models import EstadoBot, Cliente, Cotizacion, EstadoConversacion
from agents.instructions_loader import cargar_instrucciones_cached
from universal_llm_client import universal_llm
from llm_config import llm_config
from handoff_tools import handoff_manager
import math

class QuoteAgent:
    """
    Agente de cotización especializado en generar cotizaciones personalizadas
    Migrado para usar el sistema LangGraph con handoff tools
    """
    
    def __init__(self, agent_name: str = "quote_agent"):
        self.agent_name = agent_name
        self.config = llm_config.get_config(agent_name)
        self.instructions = cargar_instrucciones_cached('quote')
        
    def invoke(self, state: EstadoBot) -> Dict[str, Any]:
        """
        Genera cotizaciones personalizadas basadas en el perfil del cliente
        """
        
        print(f"💰 QUOTE AGENT: Generando cotizaciones")
        print(f"   Cliente: {state.cliente.nombre}")
        print(f"   Edad: {state.cliente.edad} años")
        print(f"   Ingresos: €{state.cliente.ingresos_mensuales}/mes")
        
        # Obtener contexto de handoff
        handoff_context = handoff_manager.get_handoff_context(self.agent_name)
        task_description = handoff_context.get('task', 'Generar cotizaciones')
        
        print(f"   Tarea asignada: {task_description}")
        
        try:
            # Calcular cotizaciones
            cotizaciones = self._calculate_quotes(state.cliente, state.recomendacion_producto)
            
            # Generar presentación de cotizaciones
            presentation = self._generate_quotes_presentation(state.cliente, cotizaciones)
            
            print(f"   Cotizaciones generadas: {len(cotizaciones)}")
            
            # Preparar handoff a presentador
            return {
                "respuesta_bot": presentation,
                "cotizaciones": cotizaciones,
                "etapa": EstadoConversacion.PRESENTACION_PROPUESTA,
                "agente_activo": "presenter_agent",
                "handoff_context": {
                    "handoff_type": "presenter",
                    "task": "Presentar cotizaciones y manejar conversación de venta",
                    "next_agent": "presenter_agent",
                    "context": {
                        "client_profile": state.cliente.dict(),
                        "quotations": [q.dict() for q in cotizaciones],
                        "recommendation": state.recomendacion_producto.dict() if state.recomendacion_producto else None
                    }
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error generando cotizaciones: {e}")
            return self._handle_error(state, str(e))
    
    def _calculate_quotes(self, cliente: Cliente, recomendacion) -> List[Cotizacion]:
        """Calcula cotizaciones basadas en el perfil del cliente"""
        
        # Factores base
        base_premium = self._calculate_base_premium(cliente.edad)
        coverage_multiplier = self._get_coverage_multiplier(cliente)
        profession_factor = self._get_profession_factor(cliente.profesion)
        
        # Cotizaciones según recomendación
        quotes = []
        
        if recomendacion:
            # Cotización recomendada
            recommended_coverage = recomendacion.monto_recomendado
            recommended_premium = base_premium * coverage_multiplier * profession_factor
            
            quotes.append(Cotizacion(
                prima_mensual=round(recommended_premium, 2),
                cobertura_fallecimiento=recommended_coverage,
                tipo_plan=f"Plan {recomendacion.tipo_cobertura.title()}",
                vigencia_anos=20,
                aseguradora="Seguros Vida Plus"
            ))
        
        # Cotización básica
        basic_coverage = cliente.ingresos_mensuales * 12 * 5
        basic_premium = base_premium * 0.7 * profession_factor
        
        quotes.append(Cotizacion(
            prima_mensual=round(basic_premium, 2),
            cobertura_fallecimiento=basic_coverage,
            tipo_plan="Plan Básico",
            vigencia_anos=15,
            aseguradora="Seguros Vida Plus"
        ))
        
        # Cotización premium
        premium_coverage = cliente.ingresos_mensuales * 12 * 12
        premium_premium = base_premium * 1.3 * profession_factor
        
        quotes.append(Cotizacion(
            prima_mensual=round(premium_premium, 2),
            cobertura_fallecimiento=premium_coverage,
            tipo_plan="Plan Premium",
            vigencia_anos=25,
            aseguradora="Seguros Vida Plus"
        ))
        
        # Filtrar por presupuesto
        max_budget = cliente.ingresos_mensuales * 0.1  # 10% de ingresos
        affordable_quotes = [q for q in quotes if q.prima_mensual <= max_budget]
        
        return affordable_quotes if affordable_quotes else quotes[:2]
    
    def _calculate_base_premium(self, age: int) -> float:
        """Calcula prima base según edad"""
        
        if age <= 25:
            return 25.0
        elif age <= 35:
            return 35.0
        elif age <= 45:
            return 50.0
        elif age <= 55:
            return 75.0
        else:
            return 100.0
    
    def _get_coverage_multiplier(self, cliente: Cliente) -> float:
        """Calcula multiplicador según perfil de riesgo"""
        
        multiplier = 1.0
        
        # Dependientes aumentan el multiplicador
        if cliente.num_dependientes > 0:
            multiplier += cliente.num_dependientes * 0.1
        
        # Ingresos altos = mayor cobertura
        if cliente.ingresos_mensuales > 4000:
            multiplier += 0.2
        
        return multiplier
    
    def _get_profession_factor(self, profession: str) -> float:
        """Factor de riesgo por profesión"""
        
        if not profession:
            return 1.0
        
        profession_lower = profession.lower()
        
        # Profesiones de bajo riesgo
        low_risk = ["profesor", "medico", "ingeniero", "abogado", "contador", "administrativo"]
        if any(prof in profession_lower for prof in low_risk):
            return 0.9
        
        # Profesiones de alto riesgo
        high_risk = ["minero", "construccion", "bombero", "policia", "militar"]
        if any(prof in profession_lower for prof in high_risk):
            return 1.3
        
        return 1.0  # Factor neutro
    
    def _generate_quotes_presentation(self, cliente: Cliente, cotizaciones: List[Cotizacion]) -> str:
        """Genera presentación de cotizaciones usando LLM"""
        
        # Preparar información de cotizaciones
        quotes_info = []
        for i, quote in enumerate(cotizaciones, 1):
            quotes_info.append(f"""
Opción {i}: {quote.tipo_plan}
• Prima mensual: €{quote.prima_mensual}
• Cobertura: €{quote.cobertura_fallecimiento:,.0f}
• Vigencia: {quote.vigencia_anos} años
• Aseguradora: {quote.aseguradora}
            """.strip())
        
        quotes_text = "\n\n".join(quotes_info)
        
        messages = [
            {
                "role": "user",
                "content": f"""
Presenta estas cotizaciones de seguros de vida de manera profesional y persuasiva.

CLIENTE: {cliente.nombre}, {cliente.edad} años, {cliente.num_dependientes} dependientes, €{cliente.ingresos_mensuales}/mes

COTIZACIONES:
{quotes_text}

INSTRUCCIONES:
1. Saludo personalizado mencionando el análisis completado
2. Presenta las opciones de manera clara y organizada
3. Destaca los beneficios de cada opción
4. Incluye una recomendación sutil
5. Invita a hacer preguntas
6. Tono profesional pero cercano
7. Máximo 8 líneas

FORMATO:
- Usa emojis para organizar la información
- Destaca números importantes
- Incluye call-to-action suave
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
            print(f"⚠️ Error generando presentación: {e}")
            return self._fallback_presentation(cliente, cotizaciones)
    
    def _fallback_presentation(self, cliente: Cliente, cotizaciones: List[Cotizacion]) -> str:
        """Presentación de fallback cuando falla el LLM"""
        
        presentation = f"Perfecto {cliente.nombre}, he preparado {len(cotizaciones)} opciones personalizadas para ti:\n\n"
        
        for i, quote in enumerate(cotizaciones, 1):
            presentation += f"💼 **{quote.tipo_plan}**\n"
            presentation += f"   • €{quote.prima_mensual}/mes\n"
            presentation += f"   • Cobertura: €{quote.cobertura_fallecimiento:,.0f}\n"
            presentation += f"   • Vigencia: {quote.vigencia_anos} años\n\n"
        
        presentation += "¿Qué te gustaría saber sobre estas opciones?"
        
        return presentation
    
    def _handle_error(self, state: EstadoBot, error_message: str) -> Dict[str, Any]:
        """Maneja errores en la generación de cotizaciones"""
        
        error_response = f"Disculpa {state.cliente.nombre}, estoy teniendo un problema técnico generando las cotizaciones. Permíteme un momento para solucionarlo."
        
        return {
            "respuesta_bot": error_response,
            "etapa": EstadoConversacion.COTIZACION,
            "agente_activo": self.agent_name,
            "error": error_message
        }

def quote_agent_node(state: EstadoBot) -> Dict[str, Any]:
    """Función node para LangGraph"""
    agent = QuoteAgent()
    return agent.invoke(state)