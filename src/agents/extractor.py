from pydantic_ai import Agent
from models import Cliente, ContextoConversacional
import asyncio
import re

# Agente especializado en extracción contextual
extractor_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    result_type=Cliente,
    system_prompt="""
    Eres un extractor de datos de clientes CONTEXTUAL para seguros de vida.
    
    REGLAS CRÍTICAS:
    - Mantén SIEMPRE los datos existentes intactos
    - Solo actualiza campos con información nueva y explícita
    - Si no hay información nueva para un campo, NO lo cambies
    - El id_cliente NUNCA debe cambiar
    - PRIORIZA el contexto conversacional para interpretar respuestas cortas
    
    Busca información específica sobre:
    - nombre: nombres completos mencionados
    - edad: números seguidos de "años" (18-80 años válido)
    - profesion: trabajos mencionados
    - ingresos_mensuales: cantidades de dinero como salario (solo números, en euros)
    - num_dependientes: número de hijos/personas a cargo (0-10 válido)
    - estado_civil: soltero, casado, viudo, divorciado
    - nivel_ahorro: dinero que puede destinar mensualmente al seguro
    
    INTERPRETACIÓN CONTEXTUAL:
    - Si se está esperando una respuesta específica, prioriza esa interpretación
    - Números solos pueden ser respuestas a preguntas sobre edad, dependientes, ingresos
    - Nombres pueden ser respuestas a "¿cómo te llamas?"
    """
)

def extraer_datos_cliente(cliente: Cliente, mensaje: str, contexto: ContextoConversacional) -> tuple[Cliente, bool]:
    """
    Extrae información del mensaje del cliente usando contexto conversacional
    
    Args:
        cliente: Objeto Cliente con datos actuales
        mensaje: Nuevo mensaje del cliente
        contexto: Contexto de la conversación actual
        
    Returns:
        tuple[Cliente actualizado, bool indicando si hubo cambios]
    """
    
    print(f"🔍 EXTRACTOR CONTEXTUAL: Analizando '{mensaje}'")
    
    # PASO 1: Intentar interpretación contextual PRIMERO
    if contexto.esperando_respuesta and contexto.ultimo_campo_solicitado:
        cliente_contextual, cambio_contextual = _interpretar_con_contexto(
            cliente, mensaje, contexto
        )
        if cambio_contextual:
            print(f"✅ CONTEXTUAL: {contexto.ultimo_campo_solicitado} = {mensaje}")
            return cliente_contextual, True
    
    # PASO 2: Interpretación con IA como fallback
    cliente_actualizado = _extraer_con_ia(cliente, mensaje, contexto)
    
    # PASO 3: Detectar cambios
    cambios = _detectar_cambios(cliente, cliente_actualizado)
    hubo_cambios = len(cambios) > 0
    
    if hubo_cambios:
        print(f"✅ IA EXTRACTOR: Cambios detectados: {', '.join(cambios)}")
    else:
        print("📝 EXTRACTOR: No se encontró información nueva")
    
    return cliente_actualizado, hubo_cambios

def _interpretar_con_contexto(cliente: Cliente, mensaje: str, contexto: ContextoConversacional) -> tuple[Cliente, bool]:
    """
    Interpreta el mensaje usando el contexto conversacional (Patrón LangGraph)
    """
    
    campo = contexto.ultimo_campo_solicitado
    mensaje_limpio = mensaje.strip()
    
    # Crear copia del cliente para modificar
    cliente_dict = cliente.model_dump()
    
    print(f"🎯 CONTEXTO: Esperando respuesta para '{campo}', recibido: '{mensaje_limpio}'")
    
    try:
        if campo == "num_dependientes":
            # Esperamos un número para dependientes
            if mensaje_limpio.isdigit():
                valor = int(mensaje_limpio)
                if 0 <= valor <= 10:
                    cliente_dict["num_dependientes"] = valor
                    return Cliente(**cliente_dict), True
                    
        elif campo == "edad":
            # Esperamos un número para edad
            if mensaje_limpio.isdigit():
                valor = int(mensaje_limpio)
                if 18 <= valor <= 80:
                    cliente_dict["edad"] = valor
                    return Cliente(**cliente_dict), True
                    
        elif campo == "ingresos_mensuales":
            # Esperamos número o cantidad en euros
            numeros = re.findall(r'\d+', mensaje_limpio)
            if numeros:
                valor = int(numeros[0])
                if 500 <= valor <= 50000:
                    cliente_dict["ingresos_mensuales"] = float(valor)
                    return Cliente(**cliente_dict), True
                    
        elif campo == "nombre":
            # Esperamos un nombre
            if len(mensaje_limpio) >= 2 and any(c.isalpha() for c in mensaje_limpio):
                cliente_dict["nombre"] = mensaje_limpio.title()
                return Cliente(**cliente_dict), True
                
        elif campo == "profesion":
            # Esperamos profesión
            if len(mensaje_limpio) >= 3:
                cliente_dict["profesion"] = mensaje_limpio.lower()
                return Cliente(**cliente_dict), True
                
        elif campo == "nivel_ahorro":
            # Esperamos cantidad de ahorro mensual
            numeros = re.findall(r'\d+', mensaje_limpio)
            if numeros:
                valor = int(numeros[0])
                if 20 <= valor <= 2000:
                    cliente_dict["nivel_ahorro"] = float(valor)
                    return Cliente(**cliente_dict), True
    
    except Exception as e:
        print(f"⚠️ Error en interpretación contextual: {e}")
    
    print(f"❌ CONTEXTO: No se pudo interpretar '{mensaje_limpio}' como {campo}")
    return cliente, False

def _extraer_con_ia(cliente: Cliente, mensaje: str, contexto: ContextoConversacional) -> Cliente:
    """
    Extrae información usando IA como fallback
    """
    
    contexto_info = ""
    if contexto.esperando_respuesta:
        contexto_info = f"\nCONTEXTO IMPORTANTE: Se acaba de preguntar por '{contexto.ultimo_campo_solicitado}'. Si el mensaje parece ser una respuesta a eso, prioriza esa interpretación."
    
    prompt = f"""
    Cliente actual con todos sus datos existentes:
    {cliente.model_dump()}
    
    Nuevo mensaje del cliente: "{mensaje}"
    {contexto_info}
    
    Instrucciones:
    1. Analiza el mensaje buscando información nueva sobre el cliente
    2. Actualiza SOLO los campos donde encuentres información explícita
    3. Mantén todos los datos existentes que no se mencionen
    4. CRÍTICO: El id_cliente debe mantenerse igual: "{cliente.id_cliente}"
    
    Devuelve el objeto Cliente completo con los datos actualizados.
    """
    
    try:
        result = asyncio.run(extractor_agent.run(prompt))
        return result.data
    except Exception as e:
        print(f"⚠️ EXTRACTOR IA: Error: {e}")
        return cliente

def generar_confirmacion_inteligente(cliente: Cliente, campo: str, valor_interpretado: str) -> str:
    """
    Genera una confirmación natural cuando hay ambigüedad
    """
    
    confirmaciones = {
        "num_dependientes": f"Perfecto, {cliente.nombre or 'entonces'} ¿confirmas que tienes {valor_interpretado} dependientes?",
        "edad": f"Entiendo, {cliente.nombre or 'entonces'} tienes {valor_interpretado} años, ¿correcto?",
        "ingresos_mensuales": f"Vale, tus ingresos son de aproximadamente €{valor_interpretado} al mes, ¿es así?",
        "nombre": f"Encantado de conocerte, {valor_interpretado}. ¿He escrito bien tu nombre?",
        "profesion": f"Muy bien, trabajas como {valor_interpretado}, ¿verdad?"
    }
    
    return confirmaciones.get(campo, f"¿Te refieres a que {campo} es {valor_interpretado}?")

def _detectar_cambios(cliente_original: Cliente, cliente_actualizado: Cliente) -> list:
    """Detecta qué campos cambiaron para logging"""
    
    cambios = []
    
    campos_importantes = [
        'nombre', 'edad', 'num_dependientes', 'ingresos_mensuales', 
        'profesion', 'estado_civil', 'nivel_ahorro'
    ]
    
    for campo in campos_importantes:
        valor_original = getattr(cliente_original, campo)
        valor_nuevo = getattr(cliente_actualizado, campo)
        
        if valor_original != valor_nuevo:
            cambios.append(f"{campo}: {valor_original} → {valor_nuevo}")
    
    return cambios

def validar_interpretacion(campo: str, valor: str) -> tuple[bool, str]:
    """
    Valida si una interpretación es válida
    
    Returns:
        tuple[bool es_valido, str mensaje_error]
    """
    
    if campo == "num_dependientes":
        if not valor.isdigit():
            return False, "Necesito un número"
        num = int(valor)
        if not (0 <= num <= 10):
            return False, "El número de dependientes debe estar entre 0 y 10"
            
    elif campo == "edad":
        if not valor.isdigit():
            return False, "Necesito tu edad en números"
        edad = int(valor)
        if not (18 <= edad <= 80):
            return False, "La edad debe estar entre 18 y 80 años"
            
    elif campo == "ingresos_mensuales":
        numeros = re.findall(r'\d+', valor)
        if not numeros:
            return False, "Necesito una cantidad en euros"
        ingreso = int(numeros[0])
        if not (500 <= ingreso <= 50000):
            return False, "Los ingresos deben estar entre €500 y €50,000"
    
    return True, ""

def resetear_contexto_pregunta(contexto: ContextoConversacional) -> ContextoConversacional:
    """Resetea el contexto después de obtener una respuesta válida"""
    contexto.ultimo_campo_solicitado = None
    contexto.ultima_pregunta = None
    contexto.esperando_respuesta = False
    contexto.intentos_pregunta_actual = 0
    contexto.tipo_respuesta_esperada = None
    contexto.confirmacion_pendiente = None
    return contexto
    """
    Resetea el contexto después de obtener una respuesta válida
    """
    
    contexto.ultimo_campo_solicitado = None
    contexto.ultima_pregunta = None
    contexto.esperando_respuesta = False
    contexto.intentos_pregunta_actual = 0
    contexto.tipo_respuesta_esperada = None
    contexto.confirmacion_pendiente = None
    
    return contexto