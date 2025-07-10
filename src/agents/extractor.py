from pydantic_ai import Agent
from models import Cliente, ContextoConversacional
from config import settings
from agents.instructions_loader import cargar_instrucciones_cached
import asyncio
import re

# Agente especializado en extracción contextual - USA CONFIG E INSTRUCCIONES
def _get_model_string():
    """Obtiene el modelo string según la configuración"""
    if settings.llm_provider == "openai":
        return f"openai:{settings.llm_model}"
    elif settings.llm_provider == "groq":
        return f"groq:{settings.llm_model}"
    else:
        return f"openai:gpt-4o-mini"  # fallback

# Cargar instrucciones desde archivo
def _get_extractor_instructions():
    """Obtiene las instrucciones del extractor desde archivo"""
    try:
        # Cargar instrucciones desde archivo txt
        import os
        instructions_path = os.path.join(
            os.path.dirname(__file__), 
            'agents_instructions', 
            'extractor_instructions.txt'
        )
        with open(instructions_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Error cargando instrucciones del extractor: {e}")
        return """
        Eres un extractor de datos de clientes para seguros de vida.
        Extrae información precisa manteniendo los datos existentes intactos.
        Solo actualiza campos con información nueva y explícita.
        """

extractor_agent = Agent(
    _get_model_string(),
    result_type=Cliente,
    system_prompt=_get_extractor_instructions()
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
    
    
    # PASO 1: Intentar interpretación contextual PRIMERO (respuestas directas)
    if contexto.esperando_respuesta and contexto.ultimo_campo_solicitado:
        cliente_contextual, cambio_contextual = _interpretar_con_contexto(
            cliente, mensaje, contexto
        )
        if cambio_contextual:
            return cliente_contextual, True
    
    # PASO 2: EXTRACCIÓN CON LLM (PRINCIPAL) - Instrucciones inteligentes
    try:
        cliente_actualizado = _extraer_con_ia(cliente, mensaje, contexto)
        cambios = _detectar_cambios(cliente, cliente_actualizado)
        hubo_cambios = len(cambios) > 0
        
        if hubo_cambios:
            return cliente_actualizado, True
    except Exception as e:
        print(f"⚠️ LLM EXTRACTOR falló: {e}, usando fallback...")
    
    # PASO 3: FALLBACK - Extracción por patrones (solo si LLM falla)
    cliente_con_patrones = _extraer_con_patrones(cliente, mensaje)
    cambios_patrones = _detectar_cambios(cliente, cliente_con_patrones)
    
    if cambios_patrones:
        return cliente_con_patrones, True
    
    # PASO 4: Si nada funciona, retornar sin cambios
    return cliente, False

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
            # Patrones adicionales para dependientes
            elif "hijo" in mensaje_limpio.lower():
                numeros = re.findall(r'\d+', mensaje_limpio)
                if numeros:
                    valor = int(numeros[0])
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
            # Patrones adicionales para edad
            elif "año" in mensaje_limpio.lower():
                numeros = re.findall(r'\d+', mensaje_limpio)
                if numeros:
                    valor = int(numeros[0])
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
    
    # FALLBACK: Extracción sin contexto usando patrones
    cliente_extraido = _extraer_con_patrones(cliente, mensaje_limpio)
    cambios = _detectar_cambios(cliente, cliente_extraido)
    
    if cambios:
        print(f"✅ PATRONES: Extraídos {len(cambios)} datos")
        return cliente_extraido, True
    
    print(f"❌ CONTEXTO: No se pudo interpretar '{mensaje_limpio}' como {campo}")
    return cliente, False

def _extraer_con_patrones(cliente: Cliente, mensaje: str) -> Cliente:
    """
    Extrae información usando patrones de texto (sin API)
    """
    
    # Crear copia del cliente para modificar
    cliente_dict = cliente.model_dump()
    mensaje_lower = mensaje.lower()
    
    # Extraer nombre
    if not cliente_dict.get("nombre"):
        # Patrones para nombres (orden específico para evitar conflictos)
        patrones_nombre = [
            r"se llama\s+([a-záéíóúñ]+)",
            r"su nombre es\s+([a-záéíóúñ]+)",
            r"mi nombre es\s+([a-záéíóúñ]+)",
            r"nombre\s+(?:es\s+)?([a-záéíóúñ]+)",
            r"soy\s+([a-záéíóúñ]+)",
            # Evitar capturar "quiere" como nombre
            r"(?:cliente|paciente)\s+(?:se\s+)?(?:llama\s+)?([a-záéíóúñ]+)(?!\s+quiere)"
        ]
        
        for patron in patrones_nombre:
            match = re.search(patron, mensaje_lower)
            if match:
                nombre = match.group(1).strip()
                # Filtrar palabras que no son nombres
                palabras_excluidas = ['quiere', 'necesita', 'tiene', 'busca', 'desea', 'pide', 'solicita']
                if (len(nombre) >= 2 and nombre.isalpha() and 
                    nombre not in palabras_excluidas):
                    cliente_dict["nombre"] = nombre.title()
                    break
    
    # Extraer edad
    if not cliente_dict.get("edad"):
        # Patrones para edad
        patrones_edad = [
            r"(\d+)\s+años?",
            r"edad\s+(?:es\s+)?(\d+)",
            r"tiene\s+(\d+)\s+años?",
            r"tengo\s+(\d+)\s+años?"
        ]
        
        for patron in patrones_edad:
            match = re.search(patron, mensaje_lower)
            if match:
                edad = int(match.group(1))
                if 18 <= edad <= 80:
                    cliente_dict["edad"] = edad
                    break
    
    # Extraer dependientes
    if cliente_dict.get("num_dependientes") is None:
        # Patrones para dependientes
        patrones_dependientes = [
            r"(\d+)\s+hijos?",
            r"(\d+)\s+dependientes?",
            r"tiene\s+(\d+)\s+hijos?",
            r"tengo\s+(\d+)\s+hijos?",
            r"sin\s+hijos?" # 0 hijos
        ]
        
        for patron in patrones_dependientes:
            match = re.search(patron, mensaje_lower)
            if match:
                if "sin" in patron:
                    cliente_dict["num_dependientes"] = 0
                else:
                    dependientes = int(match.group(1))
                    if 0 <= dependientes <= 10:
                        cliente_dict["num_dependientes"] = dependientes
                break
    
    # Extraer ingresos
    if not cliente_dict.get("ingresos_mensuales"):
        # Patrones para ingresos en euros y USD (mensuales y anuales)
        patrones_ingresos = [
            # Anuales
            r"(\d+)\s*(eur|euros?)\s*al\s*(anio|año)",
            r"(\d+)\s*(usd|dólares?|dollars?)\s*al\s*(anio|año)",
            r"ingreso[s]?\s*[,]?\s*(?:de\s+)?(?:unos\s+)?(\d+)\s*(eur|euros?)\s*al\s*(anio|año)",
            r"gana\s+(?:unos\s+)?(\d+)\s*(eur|euros?)\s*al\s*(anio|año)",
            # Mensuales
            r"(\d+)\s*(eur|euros?)\s*(?:al\s+mes|mensuales?)",
            r"(\d+)\s*(usd|dólares?|dollars?)\s*(?:al\s+mes|mensuales?)",
            r"ingreso[s]?\s*[,]?\s*(?:de\s+)?(?:unos\s+)?(\d+)\s*(eur|euros?)\s*(?:al\s+mes|mensuales?)?",
            r"gana\s+(?:unos\s+)?(\d+)\s*(eur|euros?|usd|dólares?)",
            r"(\d+)\s*€\s*(?:al\s+mes|mensuales?)?"
        ]
        
        for patron in patrones_ingresos:
            match = re.search(patron, mensaje_lower)
            if match:
                ingresos = int(match.group(1))
                moneda = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                
                # Detectar si son ingresos anuales por el tercer grupo o el texto completo
                texto_completo = match.group(0)
                es_anual = (len(match.groups()) > 2 and match.group(3) and 
                           any(palabra in match.group(3) for palabra in ['año', 'anio'])) or \
                          any(palabra in texto_completo for palabra in ['año', 'anio'])
                
                # Convertir anuales a mensuales
                if es_anual:
                    ingresos_mensuales = ingresos / 12
                else:
                    ingresos_mensuales = ingresos
                
                # Convertir USD a EUR (tasa aproximada 1 USD = 0.92 EUR)
                if moneda and any(m in moneda.lower() for m in ['usd', 'dólar', 'dollar']):
                    ingresos_eur = int(ingresos_mensuales * 0.92)  # Conversión USD a EUR
                else:
                    ingresos_eur = int(ingresos_mensuales)
                
                if 100 <= ingresos_eur <= 50000:  # Reducir mínimo para ingresos anuales bajos
                    cliente_dict["ingresos_mensuales"] = float(ingresos_eur)
                    break
    
    # Extraer profesión
    if not cliente_dict.get("profesion"):
        # Patrones para profesión
        patrones_profesion = [
            r"trabaja\s+como\s+([a-záéíóúñ]+)",
            r"es\s+([a-záéíóúñ]+)",
            r"profesión\s+([a-záéíóúñ]+)",
            r"soy\s+([a-záéíóúñ]+)"
        ]
        
        for patron in patrones_profesion:
            match = re.search(patron, mensaje_lower)
            if match:
                profesion = match.group(1).strip()
                if len(profesion) >= 3:
                    cliente_dict["profesion"] = profesion
                    break
    
    # Extraer compromisos financieros
    if not cliente_dict.get("compromisos_financieros"):
        # Patrones para compromisos financieros (incluyendo errores tipográficos)
        patrones_compromisos = [
            r"hipet?e?ca\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"hipoteca\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"préstamo\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"deuda\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"paga\s+(?:unos\s+)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?\s*(?:de\s+)?(?:hipet?e?ca|hipoteca|préstamo|deuda)",
            r"debe\s+(?:unos\s+)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"tiene\s+(?:una\s+)?hipet?e?ca\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"tiene\s+(?:una\s+)?hipoteca\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?",
            r"compromiso\s+(?:de\s+(?:unos\s+)?)?([0-9.,]+)\s*(usd|eur|euros?|dólares?|pesos?|ars)?"
        ]
        
        for patron in patrones_compromisos:
            match = re.search(patron, mensaje_lower)
            if match:
                monto = match.group(1).replace(",", "").replace(".", "")
                moneda = match.group(2) if match.group(2) else ""
                
                # Construir texto del compromiso
                if "hipet" in patron or "hipoteca" in patron:
                    compromiso = f"hipoteca {monto} {moneda}".strip()
                elif "préstamo" in patron:
                    compromiso = f"préstamo {monto} {moneda}".strip()
                elif "deuda" in patron:
                    compromiso = f"deuda {monto} {moneda}".strip()
                else:
                    compromiso = f"compromiso financiero {monto} {moneda}".strip()
                
                cliente_dict["compromisos_financieros"] = compromiso
                break
    
    return Cliente(**cliente_dict)

def _extraer_con_ia(cliente: Cliente, mensaje: str, contexto: ContextoConversacional) -> Cliente:
    """
    Extrae información usando IA como fallback
    """
    
    contexto_info = ""
    if contexto.esperando_respuesta:
        contexto_info = f"\nCONTEXTO IMPORTANTE: Se acaba de preguntar por '{contexto.ultimo_campo_solicitado}'. Si el mensaje parece ser una respuesta a eso, prioriza esa interpretación."
    
    prompt = f"""
    DATOS ACTUALES DEL CLIENTE (CONSERVAR TODOS):
    - Nombre: {cliente.nombre}
    - Edad: {cliente.edad}
    - Num_dependientes: {cliente.num_dependientes}
    - Ingresos_mensuales: {cliente.ingresos_mensuales}
    - Profesion: {cliente.profesion}
    - Estado_civil: {cliente.estado_civil}
    - Compromisos_financieros: {cliente.compromisos_financieros}
    - ID: {cliente.id_cliente}
    
    Nuevo mensaje del cliente: "{mensaje}"
    {contexto_info}
    
    INSTRUCCIONES CRÍTICAS:
    1. MANTÉN TODOS los datos existentes que no sean None
    2. SOLO actualiza campos donde encuentres información nueva y explícita
    3. NUNCA sobrescribas datos existentes con None
    4. NUNCA cambies el id_cliente
    5. Si no encuentras información nueva, devuelve el cliente tal como está
    
    IMPORTANTE - COMPROMISOS FINANCIEROS:
    Busca menciones de hipotecas, préstamos, deudas, pagos mensuales. Ejemplos:
    - "hipoteca 600 USD" → compromisos_financieros: "hipoteca 600 USD"
    - "paga 500 euros de préstamo" → compromisos_financieros: "préstamo 500 euros"
    - "tiene una deuda de 1000 pesos" → compromisos_financieros: "deuda 1000 pesos"
    
    Devuelve el objeto Cliente completo MANTENIENDO todos los datos existentes.
    """
    
    try:
        result = asyncio.run(extractor_agent.run(prompt))
        
        # Validar que no se perdieron datos
        extracted_client = result.data
        
        # Conservar datos existentes si el extractor los perdió
        if cliente.nombre and not extracted_client.nombre:
            extracted_client.nombre = cliente.nombre
        if cliente.edad and not extracted_client.edad:
            extracted_client.edad = cliente.edad
        if cliente.num_dependientes is not None and extracted_client.num_dependientes is None:
            extracted_client.num_dependientes = cliente.num_dependientes
        if cliente.ingresos_mensuales and not extracted_client.ingresos_mensuales:
            extracted_client.ingresos_mensuales = cliente.ingresos_mensuales
        if cliente.profesion and not extracted_client.profesion:
            extracted_client.profesion = cliente.profesion
        if cliente.estado_civil and not extracted_client.estado_civil:
            extracted_client.estado_civil = cliente.estado_civil
        if cliente.compromisos_financieros and not extracted_client.compromisos_financieros:
            extracted_client.compromisos_financieros = cliente.compromisos_financieros
        if cliente.id_cliente and not extracted_client.id_cliente:
            extracted_client.id_cliente = cliente.id_cliente
            
        return extracted_client
        
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
        'profesion', 'estado_civil', 'nivel_ahorro', 'compromisos_financieros'
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