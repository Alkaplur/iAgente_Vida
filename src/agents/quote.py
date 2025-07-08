from typing import List
from src.models import Cliente, Cotizacion, RecomendacionProducto
from groq import Groq
from src.config import settings
from agents.instructions_loader import cargar_instrucciones_cached
from agents.llm_client import get_llm_response

# Cliente Groq
groq_client = Groq(api_key=settings.groq_api_key)

def calcular_cotizaciones(cliente: Cliente, recomendacion: RecomendacionProducto) -> List[Cotizacion]:
    """
    Genera cotizaciones basadas en:
    1. Perfil del cliente (edad, ingresos, dependientes)
    2. Recomendación de producto del needs-based selling
    """
    
    print(f"💰 COTIZADOR: Calculando para {cliente.nombre}")
    print(f"   Perfil: {cliente.edad} años, {cliente.num_dependientes} dependientes, €{cliente.ingresos_mensuales}/mes")
    print(f"   Recomendación: {recomendacion.tipo_cobertura} - {recomendacion.cobertura_principal}")
    
    cotizaciones = []
    
    # Usar la recomendación como base para las cotizaciones
    cobertura_base = recomendacion.monto_recomendado
    
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
    
    print(f"   Presupuesto máximo estimado: €{presupuesto_max:.2f}/mes")
    
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


    """Genera una presentación atractiva de las cotizaciones usando IA"""
    
    print(f"📋 Generando presentación para {len(cotizaciones)} cotizaciones")
    
    # Preparar información de las cotizaciones
    cotizaciones_info = ""
    for i, cot in enumerate(cotizaciones, 1):
        cotizaciones_info += f"""
        Opción {i}: {cot.tipo_plan}
        • Prima mensual: €{cot.prima_mensual}
        • Cobertura: €{cot.cobertura_fallecimiento:,.0f}
        • Vigencia: {cot.vigencia_anos} años
        """
    
    # Identificar la recomendada (la que tiene "Recomendado" en el nombre)
    recomendada = next((i+1 for i, cot in enumerate(cotizaciones) if "Recomendado" in cot.tipo_plan), 1)
    
    prompt = f"""
    Eres iAgente_Vida, especialista en seguros de vida. Presenta estas cotizaciones de manera profesional y persuasiva.
    
    Cliente: {cliente.nombre}, {cliente.edad} años, {cliente.num_dependientes} dependientes
    Ingresos: €{cliente.ingresos_mensuales}/mes
    Presupuesto indicado: €{cliente.nivel_ahorro or 'No especificado'}/mes
    
    Cotizaciones calculadas:{cotizaciones_info}
    
    INSTRUCCIONES:
    1. Saluda y agradece su paciencia
    2. Menciona que has analizado su perfil cuidadosamente
    3. Presenta cada opción destacando sus beneficios únicos
    4. Recomienda específicamente la Opción {recomendada} y explica por qué
    5. Pregunta cuál le interesa más o si tiene dudas
    
    Sé profesional, confiado y orientado a la acción.
    Usa un tono cálido pero experto.
    Máximo 8 líneas.
    """
    
    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        
        presentacion = response.choices[0].message.content
        print(f"✅ Presentación generada exitosamente")
        return presentacion
        
    except Exception as e:
        print(f"⚠️ Error generando presentación: {e}")
        
        # Fallback manual
        return _generar_presentacion_fallback(cliente, cotizaciones)

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
    
    # Preparar información de las cotizaciones
    cotizaciones_info = ""
    for i, cot in enumerate(cotizaciones, 1):
        cotizaciones_info += f"""
        Opción {i}: {cot.tipo_plan}
        • Prima mensual: €{cot.prima_mensual}
        • Cobertura: €{cot.cobertura_fallecimiento:,.0f}
        • Vigencia: {cot.vigencia_anos} años
        """
    
    # Identificar la recomendada (la que tiene "Recomendado" en el nombre)
    recomendada = next((i+1 for i, cot in enumerate(cotizaciones) if "Recomendado" in cot.tipo_plan), 1)
    
    prompt = f"""
{instrucciones_quote}

=== CONTEXTO DE PRESENTACIÓN ===
CLIENTE: {cliente.nombre}, {cliente.edad} años, {cliente.num_dependientes} dependientes
INGRESOS: €{cliente.ingresos_mensuales}/mes
PRESUPUESTO INDICADO: €{cliente.nivel_ahorro or 'No especificado'}/mes

COTIZACIONES CALCULADAS:{cotizaciones_info}

=== TU TAREA ===
Presenta estas cotizaciones siguiendo las instrucciones de Quote Agent:

1. Saluda y agradece su paciencia
2. Menciona que has analizado su perfil cuidadosamente
3. Presenta cada opción destacando sus beneficios únicos
4. Recomienda específicamente la Opción {recomendada} y explica por qué
5. Pregunta cuál le interesa más o si tiene dudas

Sé profesional, confiado y orientado a la acción.
Usa un tono experto pero cálido.
Máximo 8 líneas.
"""
    
    try:
        response = get_llm_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        
        presentacion = response.choices[0].message.content
        print(f"✅ Presentación generada exitosamente")
        return presentacion
        
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