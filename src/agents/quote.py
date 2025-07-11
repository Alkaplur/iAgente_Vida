from typing import List, Dict
try:
    from ..models import Cliente, Cotizacion, RecomendacionProducto
    from ..config import settings
    from .instructions_loader import cargar_instrucciones_cached
    from .llm_client import get_llm_response
    from ..utils.motor_cotizacion import obtener_motor_cotizacion
    from ..utils.productos_loader import obtener_productos_loader
except ImportError:
    from models import Cliente, Cotizacion, RecomendacionProducto
    from config import settings
    from agents.instructions_loader import cargar_instrucciones_cached
    from agents.llm_client import get_llm_response
    from utils.motor_cotizacion import obtener_motor_cotizacion
    from utils.productos_loader import obtener_productos_loader
from groq import Groq

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
    Genera cotizaciones usando el motor de cotización modular
    """
    
    print(f"💰 QUOTE: {cliente.nombre} | {cliente.edad}a, {cliente.num_dependientes}dep, €{cliente.ingresos_mensuales}/mes")
    
    if ajustar_precio and presupuesto_objetivo:
        print(f"   🎯 Ajustando a €{presupuesto_objetivo}/mes")
    
    # Obtener motor de cotización
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Generar cotizaciones usando el motor
    cotizaciones = motor_cotizacion.generar_cotizaciones_multiples(
        cliente=cliente,
        ajustar_precio=ajustar_precio,
        presupuesto_objetivo=presupuesto_objetivo
    )
    
    print(f"✅ {len(cotizaciones)} cotizaciones generadas con motor")
    return cotizaciones

def _generar_cotizacion_recomendada(cliente: Cliente, recomendacion: RecomendacionProducto, cobertura_base: float) -> Cotizacion:
    """Genera la cotización principal usando el motor de cotización"""
    
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Usar el motor para generar la cotización
    cotizacion = motor_cotizacion.calcular_cotizacion_completa(
        cliente=cliente,
        tipo_cobertura=recomendacion.cobertura_principal,
        cobertura_deseada=cobertura_base
    )
    
    # Marcar como recomendada
    cotizacion.tipo_plan += " (Recomendado)"
    
    return cotizacion

def _generar_cotizacion_economica(cliente: Cliente, cobertura_base: float) -> Cotizacion:
    """Genera opción más económica usando el motor"""
    
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Generar cotización básica con cobertura reducida
    cotizacion = motor_cotizacion.calcular_cotizacion_completa(
        cliente=cliente,
        tipo_cobertura="fallecimiento",
        cobertura_deseada=cobertura_base * 0.6
    )
    
    cotizacion.tipo_plan = "Opción Económica - Protección Esencial"
    cotizacion.vigencia_anos = 15
    
    return cotizacion

def _generar_cotizacion_premium(cliente: Cliente, cobertura_base: float) -> Cotizacion:
    """Genera opción premium usando el motor"""
    
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Generar cotización premium con cobertura ampliada
    cotizacion = motor_cotizacion.calcular_cotizacion_completa(
        cliente=cliente,
        tipo_cobertura="vida+ahorro",
        cobertura_deseada=cobertura_base * 1.5
    )
    
    cotizacion.tipo_plan = "Premium - Cobertura Total + Enfermedades Graves + Ahorro"
    cotizacion.vigencia_anos = 35
    
    return cotizacion

def _calcular_cobertura_por_presupuesto(edad: int, presupuesto_mensual: float) -> float:
    """Calcula la cobertura máxima posible dado un presupuesto mensual usando el motor"""
    
    motor_cotizacion = obtener_motor_cotizacion()
    return motor_cotizacion._calcular_cobertura_por_presupuesto(edad, presupuesto_mensual)

def _calcular_prima_base(edad: int, cobertura: float) -> float:
    """Calcula la prima mensual base usando el motor de cotización"""
    
    motor_cotizacion = obtener_motor_cotizacion()
    return motor_cotizacion.calcular_prima_base(edad, cobertura)

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
    """Genera cotizaciones básicas usando el motor cuando no hay recomendación"""
    
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Generar cotizaciones básicas con el motor
    cotizaciones = motor_cotizacion.generar_cotizaciones_multiples(
        cliente=cliente,
        ajustar_precio=ajustar_precio
    )
    
    # Si no se generaron, crear una básica manual
    if not cotizaciones:
        ingresos_base = cliente.ingresos_mensuales or 2000.0
        cobertura_base = ingresos_base * 12 * 6
        
        cotizacion_basica = motor_cotizacion.calcular_cotizacion_completa(
            cliente=cliente,
            tipo_cobertura="fallecimiento",
            cobertura_deseada=cobertura_base * (0.6 if ajustar_precio else 1.0)
        )
        
        cotizacion_basica.tipo_plan = "Plan Básico" + (" (Ajustado)" if ajustar_precio else "")
        cotizaciones = [cotizacion_basica]
    
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
    """Genera una presentación atractiva de las cotizaciones usando IA con información de productos"""
    
    print(f"📋 Generando presentación para {len(cotizaciones)} cotizaciones")
    
    # Cargar instrucciones desde archivo
    instrucciones_quote = cargar_instrucciones_cached('quote')
    
    # Obtener información de productos para enriquecer la presentación
    productos_loader = obtener_productos_loader()
    motor_cotizacion = obtener_motor_cotizacion()
    
    # Preparar información detallada de las cotizaciones con lógica de cálculo
    cotizaciones_info = ""
    for i, cot in enumerate(cotizaciones, 1):
        # Calcular información adicional para explicar el cálculo
        cobertura_años = cot.cobertura_fallecimiento / (cliente.ingresos_mensuales * 12) if cliente.ingresos_mensuales else 0
        tasa_anual = (cot.prima_mensual * 12) / cot.cobertura_fallecimiento * 1000 if cot.cobertura_fallecimiento else 0
        
        # Buscar información del producto en el diccionario
        productos_similares = productos_loader.obtener_productos_por_cobertura("fallecimiento")
        argumentos_producto = ""
        if productos_similares:
            producto_info = productos_similares[0]  # Tomar el primero como ejemplo
            argumentos_producto = f"\n        • Ventaja: {producto_info.argumentos_venta}"
        
        cotizaciones_info += f"""
        Opción {i}: {cot.tipo_plan}
        • Prima mensual: €{cot.prima_mensual}
        • Cobertura: €{cot.cobertura_fallecimiento:,.0f}
        • Vigencia: {cot.vigencia_anos} años
        • Equivale a: {cobertura_años:.1f} años de ingresos
        • Tasa: {tasa_anual:.2f}‰ anual
        • Aseguradora: {cot.aseguradora}{argumentos_producto}
        """
    
    # Identificar la recomendada (la que tiene "Recomendado" en el nombre)
    recomendada = next((i+1 for i, cot in enumerate(cotizaciones) if "Recomendado" in cot.tipo_plan), 1)
    
    # Obtener producto recomendado para argumentos adicionales
    producto_recomendado = productos_loader.recomendar_producto(
        edad=cliente.edad or 30,
        num_dependientes=cliente.num_dependientes or 0,
        ingresos_mensuales=cliente.ingresos_mensuales,
        profesion=cliente.profesion
    )
    
    argumentos_extra = ""
    if producto_recomendado:
        argumentos_extra = f"\n\nARGUMENTOS ADICIONALES DE VENTA:\n- {producto_recomendado.argumentos_venta}\n- Público objetivo: {producto_recomendado.publico_objetivo}"
    
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
{cotizaciones_info}{argumentos_extra}

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