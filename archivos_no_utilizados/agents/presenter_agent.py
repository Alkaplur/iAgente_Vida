from typing import Dict, Any, List
from models import EstadoBot, Cliente, Cotizacion, EstadoConversacion
from agents.instructions_loader import cargar_instrucciones_cached
from universal_llm_client import universal_llm
from llm_config import llm_config
from handoff_tools import handoff_manager

class PresenterAgent:
    """
    Agente presentador especializado en presentar ofertas y manejar objeciones
    Migrado para usar el sistema LangGraph con handoff tools
    """
    
    def __init__(self, agent_name: str = "presenter_agent"):
        self.agent_name = agent_name
        self.config = llm_config.get_config(agent_name)
        self.instructions = cargar_instrucciones_cached('presentador')
        
    def invoke(self, state: EstadoBot) -> Dict[str, Any]:
        """
        Maneja la presentación de ofertas y responde a las consultas del cliente
        """
        
        print(f"📊 PRESENTER AGENT: Manejando presentación y ventas")
        print(f"   Cliente: {state.cliente.nombre}")
        print(f"   Cotizaciones: {len(state.cotizaciones)}")
        print(f"   Mensaje: '{state.mensaje_usuario}'")
        
        # Obtener contexto de handoff
        handoff_context = handoff_manager.get_handoff_context(self.agent_name)
        task_description = handoff_context.get('task', 'Presentar ofertas y manejar conversación')
        
        print(f"   Tarea asignada: {task_description}")
        
        # Analizar intención del mensaje
        intent = self._analyze_message_intent(state.mensaje_usuario)
        
        # Generar respuesta según la intención
        if intent == "request_details":
            response = self._handle_details_request(state)
        elif intent == "show_objection":
            response = self._handle_objection(state)
        elif intent == "show_interest":
            response = self._handle_interest(state)
        elif intent == "ready_to_buy":
            response = self._handle_closing(state)
        elif intent == "compare_options":
            response = self._handle_comparison(state)
        else:
            response = self._handle_general_conversation(state)
        
        return {
            "respuesta_bot": response,
            "etapa": EstadoConversacion.PRESENTACION_PROPUESTA,
            "agente_activo": self.agent_name
        }
    
    def _analyze_message_intent(self, message: str) -> str:
        """Analiza la intención del mensaje del cliente"""
        
        message_lower = message.lower()
        
        # Patrones de intención
        if any(word in message_lower for word in ["diferencia", "que incluye", "detalles", "explica"]):
            return "request_details"
        
        elif any(word in message_lower for word in ["caro", "mucho", "no puedo", "presupuesto"]):
            return "show_objection"
        
        elif any(word in message_lower for word in ["me gusta", "interesa", "bueno", "perfecto"]):
            return "show_interest"
        
        elif any(word in message_lower for word in ["si", "acepto", "contrato", "cuando empiezo"]):
            return "ready_to_buy"
        
        elif any(word in message_lower for word in ["comparar", "cual es mejor", "recomiendas"]):
            return "compare_options"
        
        return "general"
    
    def _handle_details_request(self, state: EstadoBot) -> str:
        """Maneja solicitudes de detalles sobre las cotizaciones"""
        
        cotizaciones_info = self._format_quotations_details(state.cotizaciones)
        
        messages = [
            {
                "role": "user",
                "content": f"""
El cliente {state.cliente.nombre} pregunta: "{state.mensaje_usuario}"

COTIZACIONES DISPONIBLES:
{cotizaciones_info}

PERFIL DEL CLIENTE:
- Edad: {state.cliente.edad} años
- Dependientes: {state.cliente.num_dependientes}
- Ingresos: €{state.cliente.ingresos_mensuales}/mes
- Profesión: {state.cliente.profesion}

INSTRUCCIONES:
1. Responde específicamente a su pregunta
2. Explica las diferencias entre opciones
3. Destaca beneficios relevantes para su perfil
4. Usa técnicas de contraste para mostrar valor
5. Mantén tono consultivo, no agresivo
6. Máximo 6 líneas
7. Incluye pregunta para continuar conversación

TÉCNICAS DE VENTA:
- Enfócate en beneficios, no solo características
- Personaliza según su situación familiar
- Crea urgencia ética apropiada
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
            print(f"⚠️ Error manejando detalles: {e}")
            return self._fallback_details_response(state)
    
    def _handle_objection(self, state: EstadoBot) -> str:
        """Maneja objeciones del cliente"""
        
        messages = [
            {
                "role": "user",
                "content": f"""
El cliente {state.cliente.nombre} ha puesto una objeción: "{state.mensaje_usuario}"

CONTEXTO DEL CLIENTE:
- Edad: {state.cliente.edad} años
- Dependientes: {state.cliente.num_dependientes}
- Ingresos: €{state.cliente.ingresos_mensuales}/mes
- Profesión: {state.cliente.profesion}

COTIZACIONES DISPONIBLES:
{self._format_quotations_summary(state.cotizaciones)}

INSTRUCCIONES PARA MANEJAR OBJECIONES:
1. Reconoce y valida su preocupación
2. Reencuadra el costo como inversión
3. Compara con gastos diarios (café, comidas)
4. Enfatiza el riesgo de no tener protección
5. Ofrece alternativas si es necesario
6. Usa técnicas de cierre suave
7. Máximo 5 líneas
8. Tono empático pero firme

TÉCNICAS ESPECÍFICAS:
- "Entiendo tu preocupación, pero piénsalo así..."
- "Si comparas €X/mes con el costo de..."
- "El verdadero riesgo es no tener protección cuando..."
- "¿Qué pasaría si algo ocurriera y no tuvieras cobertura?"
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
            print(f"⚠️ Error manejando objeción: {e}")
            return self._fallback_objection_response(state)
    
    def _handle_interest(self, state: EstadoBot) -> str:
        """Maneja cuando el cliente muestra interés"""
        
        messages = [
            {
                "role": "user",
                "content": f"""
El cliente {state.cliente.nombre} muestra interés: "{state.mensaje_usuario}"

SITUACIÓN:
- Es un momento clave para avanzar hacia el cierre
- Necesitas mantener el momentum
- Guiar hacia la siguiente acción concreta

INSTRUCCIONES:
1. Refuerza su buena decisión
2. Destaca beneficios específicos para su situación
3. Crea urgencia apropiada
4. Guía hacia próximos pasos concretos
5. Pregunta de cierre suave
6. Máximo 4 líneas
7. Tono positivo y orientado a la acción

TÉCNICAS DE CIERRE:
- "Excelente decisión, {state.cliente.nombre}..."
- "Esta opción es perfecta para tu situación porque..."
- "Para proteger a tu familia, podemos..."
- "¿Te gustaría que preparemos los documentos?"
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
            print(f"⚠️ Error manejando interés: {e}")
            return self._fallback_interest_response(state)
    
    def _handle_closing(self, state: EstadoBot) -> str:
        """Maneja el cierre de la venta"""
        
        messages = [
            {
                "role": "user",
                "content": f"""
¡EXCELENTE! El cliente {state.cliente.nombre} está listo para cerrar: "{state.mensaje_usuario}"

SITUACIÓN:
- Momento crítico de cierre
- Necesitas confirmar la decisión
- Explicar próximos pasos claramente
- Mantener profesionalismo y eficiencia

INSTRUCCIONES:
1. Felicita por la excelente decisión
2. Confirma la opción elegida
3. Explica próximos pasos del proceso
4. Indica qué documentos necesitará
5. Establece expectativas de tiempo
6. Tono profesional y congratulatorio
7. Máximo 5 líneas

PROCESO A EXPLICAR:
- Confirmación de datos
- Documentos necesarios
- Proceso de aprobación
- Tiempo estimado
- Próxima comunicación
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
            print(f"⚠️ Error manejando cierre: {e}")
            return self._fallback_closing_response(state)
    
    def _handle_comparison(self, state: EstadoBot) -> str:
        """Maneja comparaciones entre opciones"""
        
        if len(state.cotizaciones) < 2:
            return "Actualmente tienes una excelente opción. ¿Te gustaría que te prepare alternativas adicionales?"
        
        comparison = self._generate_comparison_table(state.cotizaciones)
        
        messages = [
            {
                "role": "user",
                "content": f"""
El cliente {state.cliente.nombre} quiere comparar opciones: "{state.mensaje_usuario}"

COMPARACIÓN DE OPCIONES:
{comparison}

PERFIL DEL CLIENTE:
- {state.cliente.edad} años, {state.cliente.num_dependientes} dependientes
- Ingresos: €{state.cliente.ingresos_mensuales}/mes

INSTRUCCIONES:
1. Presenta comparación clara y objetiva
2. Destaca pros y contras de cada opción
3. Haz recomendación basada en su perfil
4. Usa técnicas de contraste
5. Guía hacia decisión
6. Máximo 6 líneas
7. Incluye pregunta para avanzar

TÉCNICAS:
- "Para tu situación específica, te recomiendo..."
- "La diferencia clave es que..."
- "Considerando tus X dependientes..."
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
            print(f"⚠️ Error manejando comparación: {e}")
            return self._fallback_comparison_response(state)
    
    def _handle_general_conversation(self, state: EstadoBot) -> str:
        """Maneja conversación general"""
        
        messages = [
            {
                "role": "user",
                "content": f"""
El cliente {state.cliente.nombre} dice: "{state.mensaje_usuario}"

CONTEXTO:
- Estamos en fase de presentación de ofertas
- Tiene {len(state.cotizaciones)} opciones disponibles
- Necesitamos mantener foco en la venta

INSTRUCCIONES:
1. Responde apropiadamente a su mensaje
2. Reconducir hacia las opciones de seguro
3. Mantener conversación productiva
4. Tono profesional y orientado a objetivos
5. Máximo 4 líneas
6. Incluir pregunta para avanzar

OBJETIVO: Guiar conversación hacia decisión sobre las opciones presentadas
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
            print(f"⚠️ Error en conversación general: {e}")
            return self._fallback_general_response(state)
    
    def _format_quotations_details(self, cotizaciones: List[Cotizacion]) -> str:
        """Formatea detalles completos de las cotizaciones"""
        
        details = []
        for i, quote in enumerate(cotizaciones, 1):
            details.append(f"""
Opción {i}: {quote.tipo_plan}
• Prima mensual: €{quote.prima_mensual}
• Cobertura fallecimiento: €{quote.cobertura_fallecimiento:,.0f}
• Vigencia: {quote.vigencia_anos} años
• Aseguradora: {quote.aseguradora}
• Cobertura anual: €{quote.prima_mensual * 12:,.0f}
            """.strip())
        
        return "\n\n".join(details)
    
    def _format_quotations_summary(self, cotizaciones: List[Cotizacion]) -> str:
        """Formatea resumen de cotizaciones"""
        
        summary = []
        for quote in cotizaciones:
            summary.append(f"• {quote.tipo_plan}: €{quote.prima_mensual}/mes - Cobertura €{quote.cobertura_fallecimiento:,.0f}")
        
        return "\n".join(summary)
    
    def _generate_comparison_table(self, cotizaciones: List[Cotizacion]) -> str:
        """Genera tabla comparativa de opciones"""
        
        if len(cotizaciones) < 2:
            return "Solo hay una opción disponible"
        
        comparison = "COMPARACIÓN DE OPCIONES:\n\n"
        
        for i, quote in enumerate(cotizaciones, 1):
            comparison += f"{i}. {quote.tipo_plan}:\n"
            comparison += f"   - Prima: €{quote.prima_mensual}/mes\n"
            comparison += f"   - Cobertura: €{quote.cobertura_fallecimiento:,.0f}\n"
            comparison += f"   - Vigencia: {quote.vigencia_anos} años\n"
            comparison += f"   - Costo anual: €{quote.prima_mensual * 12:,.0f}\n\n"
        
        return comparison
    
    # Métodos de fallback
    def _fallback_details_response(self, state: EstadoBot) -> str:
        return f"Te explico las diferencias, {state.cliente.nombre}. Tienes {len(state.cotizaciones)} opciones con diferentes niveles de cobertura y precios. ¿Qué aspecto específico te interesa más?"
    
    def _fallback_objection_response(self, state: EstadoBot) -> str:
        return f"Entiendo tu preocupación, {state.cliente.nombre}. Recuerda que estamos hablando de proteger a tu familia. Si algo pasara, esta inversión pequeña hoy podría hacer una gran diferencia. ¿Qué te parece si vemos la opción más accesible?"
    
    def _fallback_interest_response(self, state: EstadoBot) -> str:
        return f"Excelente decisión, {state.cliente.nombre}. Esta protección es exactamente lo que necesitas para tu situación. ¿Te gustaría que procedamos con la opción que más te convence?"
    
    def _fallback_closing_response(self, state: EstadoBot) -> str:
        return f"¡Fantástico, {state.cliente.nombre}! Has tomado la mejor decisión para proteger a tu familia. Ahora necesito algunos documentos para proceder. Te contactaré pronto con los próximos pasos."
    
    def _fallback_comparison_response(self, state: EstadoBot) -> str:
        return f"Para tu situación con {state.cliente.num_dependientes} dependientes, te recomiendo la opción intermedia: equilibrio perfecto entre cobertura y precio. ¿Qué opinas?"
    
    def _fallback_general_response(self, state: EstadoBot) -> str:
        return f"Perfecto, {state.cliente.nombre}. Volviendo a tus opciones de seguro, ¿hay alguna de las {len(state.cotizaciones)} alternativas que te llame más la atención?"

def presenter_agent_node(state: EstadoBot) -> Dict[str, Any]:
    """Función node para LangGraph"""
    agent = PresenterAgent()
    return agent.invoke(state)