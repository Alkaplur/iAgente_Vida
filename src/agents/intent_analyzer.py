"""
Analizador de Intenciones Avanzado - Sin hardcoding
Detecta objeciones, necesidades y sentimientos usando LLM
"""
from typing import Dict, Any, List
from dataclasses import dataclass

try:
    from .llm_client import get_llm_response
    from .instructions_loader import cargar_instrucciones_cached
    from ..models import Cliente
except ImportError:
    from agents.llm_client import get_llm_response
    from agents.instructions_loader import cargar_instrucciones_cached
    from models import Cliente


@dataclass
class AnalisisIntencion:
    """Resultado del análisis de intención"""
    intencion_principal: str  # objecion, consulta, acepta, etc.
    tipo_objecion: str = None  # precio, tiempo, confianza, necesidad
    nivel_urgencia: str = "media"  # baja, media, alta
    sentimiento: str = "neutral"  # positivo, neutral, negativo, preocupado
    necesidades_detectadas: List[str] = None
    presupuesto_mencionado: float = None
    palabras_clave: List[str] = None
    confianza_analisis: float = 0.8  # 0.0 a 1.0


def analizar_intencion_completa(mensaje: str, cliente: Cliente = None, contexto_previo: str = None) -> AnalisisIntencion:
    """
    Análisis completo de intención usando LLM
    Sin regex ni palabras hardcodeadas
    """
    
    # Construir contexto del cliente si está disponible
    contexto_cliente = ""
    if cliente:
        contexto_cliente = f"""
        PERFIL DEL CLIENTE:
        - Nombre: {cliente.nombre or 'No especificado'}
        - Edad: {cliente.edad or 'No especificada'}
        - Dependientes: {cliente.num_dependientes or 'No especificado'}
        - Ingresos: €{cliente.ingresos_mensuales or 'No especificados'}/mes
        - Profesión: {cliente.profesion or 'No especificada'}
        """
    
    # Contexto conversacional
    contexto_conversacion = ""
    if contexto_previo:
        contexto_conversacion = f"""
        CONTEXTO PREVIO:
        {contexto_previo}
        """
    
    prompt = f"""
    Eres un analista experto en comunicación y ventas de seguros.
    Tu tarea es analizar un mensaje para entender la intención real del cliente.
    
    {contexto_cliente}
    {contexto_conversacion}
    
    MENSAJE A ANALIZAR: "{mensaje}"
    
    Analiza este mensaje y proporciona un análisis JSON con esta estructura:
    
    {{
        "intencion_principal": "una de: objecion, consulta, consulta_precio, acepta, rechaza, dudas, datos, interesado, neutral",
        "tipo_objecion": "si es objeción: precio, tiempo, confianza, necesidad, complejidad, otro, null",
        "nivel_urgencia": "baja, media, alta",
        "sentimiento": "positivo, neutral, negativo, preocupado, entusiasmado, escéptico",
        "necesidades_detectadas": ["lista de necesidades mencionadas o implícitas"],
        "presupuesto_mencionado": "número o null si no menciona presupuesto",
        "palabras_clave": ["palabras importantes del mensaje"],
        "confianza_analisis": "0.0 a 1.0 - qué tan seguro estás del análisis"
    }}
    
    CRITERIOS PARA INTENCIONES:
    
    OBJECION:
    - Expresa resistencia, dudas o rechazo
    - Menciona que algo es caro, complicado, innecesario
    - Pone condiciones o limitaciones
    - Ejemplos: "muy caro", "no lo necesito", "es complicado"
    
    CONSULTA_PRECIO:
    - Pregunta específicamente por costos, precios, montos
    - Busca información financiera concreta
    - Ejemplos: "¿cuánto cuesta?", "qué precio tiene"
    
    ACEPTA:
    - Muestra acuerdo o disposición a continuar
    - Expresa satisfacción con la propuesta
    - Da señales de querer proceder
    
    NECESIDADES_DETECTADAS - busca estas señales:
    - Protección familiar ("mis hijos", "mi familia")
    - Seguridad financiera ("estar tranquilo", "no dejar deudas")
    - Ahorro ("ahorrar para el futuro", "jubilación")
    - Herencia ("dejar algo", "patrimonio")
    - Estabilidad ("tener respaldo", "estar cubierto")
    
    ANÁLISIS DEL SENTIMIENTO:
    - Positivo: entusiasmo, satisfacción, confianza
    - Negativo: frustración, rechazo, molestia
    - Preocupado: ansiedad por el futuro, inseguridad
    - Escéptico: dudas sobre el producto o vendedor
    
    Responde SOLO con el JSON, sin explicaciones adicionales.
    """
    
    try:
        response_text = get_llm_response(
            prompt=prompt,
            system_prompt="Eres un analista experto en comunicación y detectas intenciones con precisión.",
            stream=False
        )
        
        # Intentar parsear el JSON
        import json
        try:
            resultado = json.loads(response_text.strip())
            return AnalisisIntencion(
                intencion_principal=resultado.get('intencion_principal', 'neutral'),
                tipo_objecion=resultado.get('tipo_objecion'),
                nivel_urgencia=resultado.get('nivel_urgencia', 'media'),
                sentimiento=resultado.get('sentimiento', 'neutral'),
                necesidades_detectadas=resultado.get('necesidades_detectadas', []),
                presupuesto_mencionado=resultado.get('presupuesto_mencionado'),
                palabras_clave=resultado.get('palabras_clave', []),
                confianza_analisis=resultado.get('confianza_analisis', 0.8)
            )
        except json.JSONDecodeError:
            # Fallback si el JSON no es válido
            return _analisis_fallback(mensaje)
            
    except Exception as e:
        print(f"⚠️ Error en análisis de intención: {e}")
        return _analisis_fallback(mensaje)


def _analisis_fallback(mensaje: str) -> AnalisisIntencion:
    """Análisis básico de fallback"""
    mensaje_lower = mensaje.lower()
    
    # Detección básica solo para emergencias
    if any(palabra in mensaje_lower for palabra in ['caro', 'expensive', 'mucho dinero']):
        return AnalisisIntencion(
            intencion_principal='objecion',
            tipo_objecion='precio',
            sentimiento='preocupado'
        )
    elif any(palabra in mensaje_lower for palabra in ['cuánto', 'precio', 'cuesta']):
        return AnalisisIntencion(
            intencion_principal='consulta_precio',
            sentimiento='neutral'
        )
    else:
        return AnalisisIntencion(
            intencion_principal='neutral',
            sentimiento='neutral'
        )


def detectar_necesidades_emocionales(mensaje: str, cliente: Cliente = None) -> Dict[str, Any]:
    """
    Detecta necesidades emocionales y motivaciones profundas
    """
    
    contexto_cliente = ""
    if cliente:
        contexto_cliente = f"""
        Cliente: {cliente.nombre or 'Anónimo'}, {cliente.edad or '?'} años
        Dependientes: {cliente.num_dependientes or 'No especificado'}
        """
    
    prompt = f"""
    Analiza este mensaje para detectar necesidades emocionales y motivaciones profundas
    relacionadas con seguros de vida.
    
    {contexto_cliente}
    MENSAJE: "{mensaje}"
    
    Busca indicadores de estas necesidades emocionales:
    
    1. MIEDO A DEJAR DESPROTEGIDA A LA FAMILIA
    2. ANSIEDAD POR EL FUTURO FINANCIERO
    3. CULPA POR NO TENER PROTECCIÓN
    4. ORGULLO DE SER PROVEEDOR RESPONSABLE
    5. PREOCUPACIÓN POR DEUDAS Y COMPROMISOS
    6. DESEO DE DEJAR UN LEGADO
    7. NECESIDAD DE TRANQUILIDAD Y CONTROL
    8. RESPONSABILIDAD HACIA DEPENDIENTES
    
    Responde en JSON:
    {{
        "necesidades_detectadas": ["lista de necesidades emocionales identificadas"],
        "nivel_emotional": "bajo, medio, alto",
        "motivacion_principal": "descripción de la motivación principal",
        "triggers_emocionales": ["palabras o frases que revelan emociones"],
        "oportunidad_venta": "baja, media, alta - basada en necesidades detectadas"
    }}
    """
    
    try:
        response_text = get_llm_response(
            prompt=prompt,
            system_prompt="Eres un psicólogo especializado en motivaciones de compra de seguros.",
            stream=False
        )
        
        import json
        return json.loads(response_text.strip())
        
    except Exception as e:
        return {
            "necesidades_detectadas": [],
            "nivel_emotional": "bajo",
            "motivacion_principal": "No detectada",
            "triggers_emocionales": [],
            "oportunidad_venta": "media"
        }


def extraer_objeciones_especificas(mensaje: str) -> Dict[str, Any]:
    """
    Extrae objeciones específicas y sugiere respuestas
    """
    
    prompt = f"""
    Analiza este mensaje para identificar objeciones específicas a seguros de vida.
    
    MENSAJE: "{mensaje}"
    
    Clasifica las objeciones en estas categorías:
    
    OBJECIONES DE PRECIO:
    - Muy caro, no puedo pagarlo
    - Prefiero invertir el dinero en otra cosa
    - No tengo presupuesto suficiente
    
    OBJECIONES DE NECESIDAD:
    - No lo necesito ahora
    - Soy muy joven para esto
    - No tengo familia que proteger
    
    OBJECIONES DE CONFIANZA:
    - Las aseguradoras no pagan
    - Es muy complicado
    - No entiendo el producto
    
    OBJECIONES DE TIEMPO:
    - Ahora no es el momento
    - Lo pensaré después
    - Necesito consultarlo
    
    Responde en JSON:
    {{
        "tipo_objecion": "precio, necesidad, confianza, tiempo, otro",
        "objecion_especifica": "descripción exacta de la objeción",
        "intensidad": "baja, media, alta",
        "es_objecion_real": "true/false - si es una objeción real o solo información",
        "estrategia_respuesta": "sugerencia de cómo responder",
        "argumentos_recomendados": ["lista de argumentos para contrarrestar"]
    }}
    """
    
    try:
        response_text = get_llm_response(
            prompt=prompt,
            system_prompt="Eres un experto en manejo de objeciones en ventas de seguros.",
            stream=False
        )
        
        import json
        return json.loads(response_text.strip())
        
    except Exception as e:
        return {
            "tipo_objecion": "otro",
            "objecion_especifica": "No identificada",
            "intensidad": "media",
            "es_objecion_real": False,
            "estrategia_respuesta": "Escuchar y entender mejor la preocupación",
            "argumentos_recomendados": []
        }