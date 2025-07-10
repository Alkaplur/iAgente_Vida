from typing import List, Dict
from models import Cliente, Cotizacion, RecomendacionProducto
from groq import Groq
from config import settings
from agents.instructions_loader import cargar_instrucciones_cached
from agents.llm_client import get_llm_response

# Cliente configurado según settings
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

def calcular_cotizaciones(cliente: Cliente, recomendacion: RecomendacionProducto, ajustar_precio: bool = False, presupuesto_objetivo: float = None) -> List[Cotizacion]:
    """
    Genera cotizaciones basadas en:
    1. Perfil del cliente (edad, ingresos, dependientes)
    2. Recomendación de producto del needs-based selling
    3. ajustar_precio: si True, genera opciones más económicas
    """
    
    print(f"💰 QUOTE: {cliente.nombre} | {cliente.edad}a, {cliente.num_dependientes}dep, €{cliente.ingresos_mensuales}/mes")
    
    if ajustar_precio and presupuesto_objetivo:
        print(f"   🎯 Ajustando a €{presupuesto_objetivo}/mes")
    
    # Validar que tenemos recomendación
    if not recomendacion:
        print("⚠️ No hay recomendación, generando cotizaciones básicas")
        return _generar_cotizaciones_basicas(cliente, ajustar_precio)
    
    cotizaciones = []
    
    # Usar la recomendación como base para las cotizaciones
    cobertura_base = recomendacion.monto_recomendado
    
    # Si necesitamos ajustar precios, reducir cobertura base
    if ajustar_precio:
        if presupuesto_objetivo:
            # Calcular cobertura que se ajuste al presupuesto objetivo
            cobertura_maxima_posible = _calcular_cobertura_por_presupuesto(cliente.edad, presupuesto_objetivo)
            cobertura_base = min(cobertura_base, cobertura_maxima_posible)
        else:
            cobertura_base = cobertura_base * 0.7  # Reducir 30%
    
    # 1. Plan según la recomendación (principal)
    cotizacion_recomendada = _generar_cotizacion_recomendada(cliente, recomendacion, cobertura_base)
    cotizaciones.append(cotizacion_recomendada)
    
    # 2. Plan alternativo más económico
    if recomendacion.tipo_cobertura != "básica":
        cotizacion_economica = _generar_cotizacion_economica(cliente, cobertura_base)
        cotizaciones.append(cotizacion_economica)
    
    # 3. Plan premium (si el cliente puede permitírselo)
    if _puede_permitirse_premium(cliente, recomendacion):
        cotizacion_premium = _generar_cotizacion_premium(cliente, cobertura_base)
        cotizaciones.append(cotizacion_premium)
    
    # Filtrar por presupuesto del cliente
    cotizaciones_filtradas = _filtrar_por_presupuesto(cotizaciones, cliente)
    
    print(f"✅ {len(cotizaciones_filtradas)} cotizaciones generadas")
    return cotizaciones_filtradas

def _generar_cotizacion_recomendada(cliente: Cliente, recomendacion: RecomendacionProducto, cobertura_base: float) -> Cotizacion:
    """Genera la cotización principal basada en la recomendación"""
    
    # Prima base según edad y cobertura
    prima_base = _calcular_prima_base(cliente.edad, cobertura_base)
    
    # Ajustes según el tipo de cobertura recomendada
    if recomendacion.cobertura_principal == "fallecimiento+invalidez":
        prima_final = prima_base * 1.4  # 40% más por invalidez
        tipo_plan = "Protección Completa - Fallecimiento + Invalidez"
        vigencia = 25
    elif recomendacion.cobertura_principal == "vida+ahorro":
        prima_final = prima_base * 1.8  # 80% más por componente de ahorro
        tipo_plan = "Vida + Ahorro - Protección e Inversión"
        vigencia = 30
    else:  # fallecimiento básico
        prima_final = prima_base
        tipo_plan = "Protección Básica - Solo Fallecimiento"
        vigencia = 20
    
    # Ajuste por profesión (algunos trabajos tienen descuentos)
    if cliente.profesion and any(prof in cliente.profesion.lower() for prof in ["ingeniero", "médico", "profesor", "contador"]):
        prima_final *= 0.95  # 5% descuento profesiones de bajo riesgo
    
    return Cotizacion(
        prima_mensual=round(prima_final, 2),
        cobertura_fallecimiento=cobertura_base,
        tipo_plan=f"{tipo_plan} (Recomendado)",
        vigencia_anos=vigencia,
        aseguradora="VidaSegura"
    )

def _generar_cotizacion_economica(cliente: Cliente, cobertura_base: float) -> Cotizacion:
    """Genera opción más económica"""
    
    # Reducir cobertura pero mantener protección esencial
    cobertura_economica = cobertura_base * 0.6
    prima_economica = _calcular_prima_base(cliente.edad, cobertura_economica) * 0.8
    
    return Cotizacion(
        prima_mensual=round(prima_economica, 2),
        cobertura_fallecimiento=cobertura_economica,
        tipo_plan="Opción Económica - Protección Esencial",
        vigencia_anos=15,
        aseguradora="VidaSegura"
    )

def _generar_cotizacion_premium(cliente: Cliente, cobertura_base: float) -> Cotizacion:
    """Genera opción premium con máxima cobertura"""
    
    # Aumentar cobertura y añadir beneficios extra
    cobertura_premium = cobertura_base * 1.5
    prima_premium = _calcular_prima_base(cliente.edad, cobertura_premium) * 2.2
    
    return Cotizacion(
        prima_mensual=round(prima_premium, 2),
        cobertura_fallecimiento=cobertura_premium,
        tipo_plan="Premium - Cobertura Total + Enfermedades Graves + Ahorro",
        vigencia_anos=35,
        aseguradora="VidaSegura"
    )

def _calcular_cobertura_por_presupuesto(edad: int, presupuesto_mensual: float) -> float:
    """Calcula la cobertura máxima posible dado un presupuesto mensual"""
    
    # Obtener la tasa anual por edad
    if edad < 25:
        tasa_anual = 0.0005
    elif edad < 30:
        tasa_anual = 0.0008
    elif edad < 35:
        tasa_anual = 0.0012
    elif edad < 40:
        tasa_anual = 0.0018
    elif edad < 45:
        tasa_anual = 0.0025
    elif edad < 50:
        tasa_anual = 0.0035
    elif edad < 55:
        tasa_anual = 0.0050
    else:
        tasa_anual = 0.0075
    
    # Prima anual disponible
    prima_anual_disponible = presupuesto_mensual * 12
    
    # Calcular cobertura máxima: cobertura = prima_anual / tasa
    cobertura_maxima = prima_anual_disponible / tasa_anual
    
    return cobertura_maxima

def _calcular_prima_base(edad: int, cobertura: float) -> float:
    """Calcula la prima mensual base según tablas actuariales simplificadas"""
    
    # Tasas por edad (por cada €1000 de cobertura)
    if edad < 25:
        tasa_anual = 0.0005
    elif edad < 30:
        tasa_anual = 0.0008
    elif edad < 35:
        tasa_anual = 0.0012
    elif edad < 40:
        tasa_anual = 0.0018
    elif edad < 45:
        tasa_anual = 0.0025
    elif edad < 50:
        tasa_anual = 0.0035
    elif edad < 55:
        tasa_anual = 0.0050
    else:
        tasa_anual = 0.0075
    
    # Prima anual = cobertura × tasa
    prima_anual = cobertura * tasa_anual
    
    # Convertir a mensual
    prima_mensual = prima_anual / 12
    
    return prima_mensual

def _puede_permitirse_premium(cliente: Cliente, recomendacion: RecomendacionProducto) -> bool:
    """Evalúa si el cliente puede permitirse la opción premium"""
    
    # Estimación rápida de capacidad
    ingresos_disponibles = cliente.ingresos_mensuales * 0.1  # 10% máximo recomendado
    
    # Solo ofrecer premium si:
    # 1. Ingresos altos (>3000)
    # 2. Ya expresó interés en cobertura alta
    # 3. Profesión estable
    
    return (
        cliente.ingresos_mensuales > 3000 and
        recomendacion.urgencia == "alta" and
        cliente.profesion is not None
    )

def _filtrar_por_presupuesto(cotizaciones: List[Cotizacion], cliente: Cliente) -> List[Cotizacion]:
    """Filtra cotizaciones que estén dentro del rango de presupuesto del cliente"""
    
    # Determinar presupuesto máximo
    if cliente.nivel_ahorro:
        presupuesto_max = cliente.nivel_ahorro * 1.2  # 20% más que lo que mencionó
    else:
        presupuesto_max = cliente.ingresos_mensuales * 0.08  # 8% de ingresos máximo
    
    
    # Filtrar cotizaciones
    cotizaciones_viables = [
        cot for cot in cotizaciones 
        if cot.prima_mensual <= presupuesto_max * 1.1  # Permitir 10% de flexibilidad
    ]
    
    # Si todas están fuera de presupuesto, ajustar la más barata
    if not cotizaciones_viables and cotizaciones:
        cotizacion_minima = min(cotizaciones, key=lambda c: c.prima_mensual)
        cotizacion_ajustada = _ajustar_cotizacion_a_presupuesto(cotizacion_minima, presupuesto_max)
        return [cotizacion_ajustada]
    
    return cotizaciones_viables if cotizaciones_viables else cotizaciones

def _generar_cotizaciones_basicas(cliente: Cliente, ajustar_precio: bool = False) -> List[Cotizacion]:
    """Genera cotizaciones básicas cuando no hay recomendación"""
    
    # Calcular cobertura base según ingresos
    ingresos_base = cliente.ingresos_mensuales or 2000.0
    cobertura_base = ingresos_base * 12 * 6  # 6 años de ingresos
    
    # Si ajustamos precio, reducir cobertura
    if ajustar_precio:
        cobertura_base = cobertura_base * 0.6  # Reducir 40%
    
    cotizaciones = []
    
    # Plan básico
    prima_basica = _calcular_prima_base(cliente.edad, cobertura_base)
    if ajustar_precio:
        prima_basica = prima_basica * 0.8  # Reducir prima 20%
    
    cotizaciones.append(Cotizacion(
        prima_mensual=round(prima_basica, 2),
        cobertura_fallecimiento=cobertura_base,
        tipo_plan="Plan Básico" + (" (Ajustado)" if ajustar_precio else ""),
        vigencia_anos=20,
        aseguradora="VidaSegura"
    ))
    
    # Plan estándar (más cobertura) - solo si no estamos ajustando precio
    if not ajustar_precio:
        cobertura_estandar = cobertura_base * 1.5
        prima_estandar = _calcular_prima_base(cliente.edad, cobertura_estandar)
        cotizaciones.append(Cotizacion(
            prima_mensual=round(prima_estandar, 2),
            cobertura_fallecimiento=cobertura_estandar,
            tipo_plan="Plan Estándar",
            vigencia_anos=25,
            aseguradora="VidaSegura"
        ))
    else:
        # Plan económico ultra-básico
        cobertura_minima = cobertura_base * 0.5
        prima_minima = _calcular_prima_base(cliente.edad, cobertura_minima) * 0.6
        cotizaciones.append(Cotizacion(
            prima_mensual=round(prima_minima, 2),
            cobertura_fallecimiento=cobertura_minima,
            tipo_plan="Plan Económico (Mínimo)",
            vigencia_anos=15,
            aseguradora="VidaSegura"
        ))
    
    return cotizaciones

def _ajustar_cotizacion_a_presupuesto(cotizacion: Cotizacion, presupuesto: float) -> Cotizacion:
    """Ajusta una cotización para que entre en el presupuesto"""
    
    factor_ajuste = presupuesto / cotizacion.prima_mensual
    
    return Cotizacion(
        prima_mensual=round(presupuesto, 2),
        cobertura_fallecimiento=round(cotizacion.cobertura_fallecimiento * factor_ajuste, -3),
        tipo_plan=f"{cotizacion.tipo_plan} (Ajustado a Presupuesto)",
        vigencia_anos=cotizacion.vigencia_anos,
        aseguradora=cotizacion.aseguradora
    )

def _generar_presentacion_fallback(cliente: Cliente, cotizaciones: List[Cotizacion]) -> str:
    """Presentación manual en caso de que falle la IA"""
    
    presentacion = f"Perfecto {cliente.nombre}, he calculado {len(cotizaciones)} opciones personalizadas para ti:\n\n"
    
    for i, cot in enumerate(cotizaciones, 1):
        destacado = " ⭐ RECOMENDADA" if "Recomendado" in cot.tipo_plan else ""
        presentacion += f"Opción {i}: {cot.tipo_plan}{destacado}\n"
        presentacion += f"€{cot.prima_mensual}/mes - Cobertura: €{cot.cobertura_fallecimiento:,.0f}\n\n"
    
    presentacion += "¿Cuál de estas opciones te parece más interesante? ¿Tienes alguna pregunta?"
    
    return presentacion

def calcular_ahorros_vs_competencia(cotizacion: Cotizacion) -> Dict[str, float]:
    """Calcula ahorros comparado con la competencia (para argumentos de venta)"""
    
    # Precios típicos de la competencia (simulados)
    precio_competencia = cotizacion.prima_mensual * 1.15  # 15% más caro
    
    ahorro_mensual = precio_competencia - cotizacion.prima_mensual
    ahorro_anual = ahorro_mensual * 12
    
    return {
        "precio_competencia": round(precio_competencia, 2),
        "ahorro_mensual": round(ahorro_mensual, 2),
        "ahorro_anual": round(ahorro_anual, 2),
        "porcentaje_ahorro": round((ahorro_mensual / precio_competencia) * 100, 1)
    }

def generar_presentacion(cliente: Cliente, cotizaciones: List[Cotizacion]) -> str:
    """Genera una presentación atractiva de las cotizaciones usando IA con instrucciones"""
    
    print(f"📋 Generando presentación para {len(cotizaciones)} cotizaciones")
    
    # Cargar instrucciones desde archivo
    instrucciones_quote = cargar_instrucciones_cached('quote')
    
    # Preparar información detallada de las cotizaciones con lógica de cálculo
    cotizaciones_info = ""
    for i, cot in enumerate(cotizaciones, 1):
        # Calcular información adicional para explicar el cálculo
        cobertura_años = cot.cobertura_fallecimiento / (cliente.ingresos_mensuales * 12) if cliente.ingresos_mensuales else 0
        tasa_anual = (cot.prima_mensual * 12) / cot.cobertura_fallecimiento * 1000 if cot.cobertura_fallecimiento else 0
        
        cotizaciones_info += f"""
        Opción {i}: {cot.tipo_plan}
        • Prima mensual: €{cot.prima_mensual}
        • Cobertura: €{cot.cobertura_fallecimiento:,.0f}
        • Vigencia: {cot.vigencia_anos} años
        • Equivale a: {cobertura_años:.1f} años de ingresos
        • Tasa: {tasa_anual:.2f}‰ anual
        • Aseguradora: {cot.aseguradora}
        """
    
    # Identificar la recomendada (la que tiene "Recomendado" en el nombre)
    recomendada = next((i+1 for i, cot in enumerate(cotizaciones) if "Recomendado" in cot.tipo_plan), 1)
    
    prompt = f"""
{instrucciones_quote}

=== CONTEXTO CRÍTICO ===
🎯 RECUERDA: Estás hablando con un AGENTE DE SEGUROS, NO con el cliente final.
🎯 Tu trabajo es ASESORAR AL AGENTE sobre cómo presentar estas cotizaciones.
🎯 NUNCA te dirijas directamente al cliente. Siempre habla AL AGENTE.

=== DATOS DEL CLIENTE DEL AGENTE ===
CLIENTE: {cliente.nombre}, {cliente.edad} años, {cliente.num_dependientes} dependientes
INGRESOS: €{cliente.ingresos_mensuales}/mes
PRESUPUESTO INDICADO: €{cliente.nivel_ahorro or 'No especificado'}/mes

=== COTIZACIONES CALCULADAS ===
{cotizaciones_info}

=== TU TAREA ===
Asesora al agente sobre cómo presentar estas cotizaciones:

1. Proporciona las cotizaciones de forma clara y organizada
2. Sugiere al agente cómo destacar los beneficios de cada opción
3. Recomienda específicamente la Opción {recomendada} y explica por qué
4. Dale argumentos que puede usar con el cliente
5. Sugiere cómo debe preguntar al cliente

EJEMPLOS DE RESPUESTAS CORRECTAS:
❌ MAL: "Perfecto Juan, he calculado estas opciones para ti..."
✅ BIEN: "Te sugiero presentar a Juan estas opciones. Explícale que..."

❌ MAL: "¿Cuál te interesa más?"
✅ BIEN: "Pregúntale cuál opción le parece más interesante y por qué..."

IMPORTANTE:
- Habla SIEMPRE al agente, nunca al cliente
- Usa "te sugiero", "deberías explicarle", "dile que"
- Proporciona argumentos de venta específicos
- Máximo 8 líneas por respuesta
"""
    
    try:
        response_text = get_llm_response(
            prompt=prompt,
            system_prompt=None,    # o un texto si quieres un rol de system
            stream=False
        )
        
        print(f"✅ Presentación generada exitosamente")
        return response_text
        
    except Exception as e:
        print(f"⚠️ Error generando presentación: {e}")
        
        # Fallback manual
        return _generar_presentacion_fallback(cliente, cotizaciones)

def validar_cotizacion(cotizacion: Cotizacion, cliente: Cliente) -> Dict[str, bool]:
    """Valida que la cotización sea viable para el cliente"""
    
    # Validaciones básicas
    validaciones = {
        "prima_razonable": cotizacion.prima_mensual < cliente.ingresos_mensuales * 0.15,
        "cobertura_adecuada": cotizacion.cobertura_fallecimiento >= cliente.ingresos_mensuales * 12 * 3,
        "edad_compatible": cliente.edad < 65,  # Límite de edad
        "vigencia_sensata": 10 <= cotizacion.vigencia_anos <= 40
    }
    
    return validaciones

# Función bridge para LangGraph
def quote_agent_node(state):
    """Función node para compatibilidad con LangGraph"""
    from quote_agent import QuoteAgent
    agent = QuoteAgent()
    return agent.invoke(state)