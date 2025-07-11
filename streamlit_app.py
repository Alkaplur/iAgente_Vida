"""
Interfaz Web Streamlit para iAgente_Vida
Sistema multiagente para asesoramiento en seguros de vida
"""
import streamlit as st
import sys
import os
from datetime import datetime
from typing import Optional

# Añadir path del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'src'))

try:
    from src.graph import crear_grafo
    from src.models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion
except ImportError:
    # Para cuando se ejecuta desde la raíz del proyecto
    from graph import crear_grafo
    from models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion

# Configurar página
st.set_page_config(
    page_title="iAgente_Vida - Chat",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS para mejor apariencia
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e8f4fd;
        border-left: 4px solid #0066cc;
    }
    .assistant-message {
        background-color: #f0f8f0;
        border-left: 4px solid #28a745;
    }
    .metrics-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #0066cc; margin: 0;">iAgente_Vida</h1>
        <p style="color: #666; margin: 0;"><em>Sistema Multiagente para Asesoramiento en Seguros de Vida</em></p>
    </div>
    """, unsafe_allow_html=True)

# Configuración estilo WhatsApp - SIN SIDEBAR
# Los datos del cliente se recopilan por conversación

# Función para inicializar estado
def inicializar_estado():
    """Inicializa el estado del bot con datos vacíos - se recopilan por conversación"""
    cliente = Cliente(
        nombre="",
        edad=0,
        estado_civil="",
        profesion="",
        ingresos_mensuales=0.0,
        gastos_fijos_mensuales=0.0,
        num_dependientes=0,
        salud_relevante="",
        tiene_seguro_vida=False
    )
    
    contexto = ContextoConversacional(
        plataforma="web",
        canal_origen="streamlit_demo",
        timestamp_inicio=datetime.now()
    )
    
    return EstadoBot(
        cliente=cliente,
        etapa=EstadoConversacion.INICIO,
        contexto=contexto,
        mensajes=[],
        cotizaciones=[],
        mensaje_usuario="",
        next_agent="needs_based_selling",
        agente_activo="orquestador"
    )

# Funciones auxiliares para manejo seguro del estado
def validar_y_reparar_estado():
    """Valida el estado y lo repara si es necesario"""
    if ("estado_bot" not in st.session_state or 
        not hasattr(st.session_state.estado_bot, 'mensajes') or 
        isinstance(st.session_state.estado_bot, dict)):
        st.session_state.estado_bot = inicializar_estado()

def obtener_mensajes():
    """Obtiene los mensajes de forma segura"""
    validar_y_reparar_estado()
    return getattr(st.session_state.estado_bot, 'mensajes', [])

def agregar_mensaje(role, content):
    """Agrega un mensaje de forma segura"""
    validar_y_reparar_estado()
    try:
        if hasattr(st.session_state.estado_bot, 'mensajes'):
            st.session_state.estado_bot.mensajes.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
    except Exception:
        # Si falla, reinicializar y intentar de nuevo
        st.session_state.estado_bot = inicializar_estado()
        if hasattr(st.session_state.estado_bot, 'mensajes'):
            st.session_state.estado_bot.mensajes.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

def generar_respuesta_contextual(mensaje_usuario, estado_bot):
    """Genera una respuesta contextual basada en el mensaje del usuario"""
    mensaje = mensaje_usuario.lower().strip()
    
    # Respuestas basadas en palabras clave
    if any(word in mensaje for word in ["hola", "hello", "hi", "buenas"]):
        return f"¡Hola! Soy iAgente_Vida, tu asistente especializado en seguros de vida. Veo que tienes {estado_bot.cliente.edad} años. ¿En qué puedo ayudarte hoy?"
    
    elif any(word in mensaje for word in ["seguro", "vida", "protección"]):
        if estado_bot.cliente.ingresos_mensuales > 0:
            return f"Perfecto, hablemos de seguros de vida. Con ingresos de €{estado_bot.cliente.ingresos_mensuales:,.0f}/mes, podemos encontrar una cobertura ideal para ti. ¿Tienes dependientes que proteger?"
        else:
            return "Me alegra que te interesen los seguros de vida. Para recomendarte la mejor opción, necesito conocer tu situación financiera. ¿Podrías completar tus ingresos mensuales?"
    
    elif any(word in mensaje for word in ["precio", "costo", "cotización", "cuanto"]):
        if estado_bot.cliente.ingresos_mensuales > 0:
            prima_estimada = estado_bot.cliente.ingresos_mensuales * 0.05  # 5% como estimación
            return f"Basándome en tu perfil, una prima estimada sería de €{prima_estimada:.0f}/mes. ¿Te gustaría que analice opciones específicas según tus necesidades?"
        else:
            return "Para calcular un precio personalizado, necesito conocer mejor tu situación. ¿Podrías completar tus datos financieros en el panel lateral?"
    
    elif any(word in mensaje for word in ["familia", "hijos", "esposa", "marido", "dependientes"]):
        return f"Entiendo que quieres proteger a tu familia. Con {estado_bot.cliente.num_dependientes} dependientes, es muy importante tener una buena cobertura. ¿Cuál es tu principal preocupación?"
    
    elif any(word in mensaje for word in ["edad", "años"]):
        return f"A los {estado_bot.cliente.edad} años, es el momento perfecto para asegurar una buena protección. Las primas son más favorables cuando eres joven. ¿Qué tipo de cobertura te interesa más?"
    
    elif any(word in mensaje for word in ["trabajo", "profesión", "empleo"]):
        if estado_bot.cliente.profesion:
            return f"Como {estado_bot.cliente.profesion}, entiendo que valoras la estabilidad. ¿Tu trabajo tiene algún riesgo particular que debamos considerar?"
        else:
            return "Me gustaría conocer tu profesión para recomendarte la cobertura más adecuada. ¿Podrías completar ese dato?"
    
    else:
        # Respuesta genérica pero más personalizada
        respuestas_genericas = [
            f"Gracias por tu consulta. Con la información que tengo de tu perfil, puedo ayudarte mejor. ¿Hay algo específico sobre seguros de vida que te preocupe?",
            f"Perfecto, estoy aquí para ayudarte. Veo que tienes {estado_bot.cliente.edad} años. ¿Qué aspecto de los seguros de vida te interesa más?",
            f"Entiendo tu interés. Para darte la mejor recomendación, ¿podrías contarme cuál es tu principal objetivo al buscar un seguro de vida?"
        ]
        import random
        return random.choice(respuestas_genericas)

# Inicializar estado si no existe o si no tiene la estructura correcta
validar_y_reparar_estado()

# Área principal de chat estilo WhatsApp
st.markdown("## 💬 iAgente_Vida")

# Contenedor para mensajes
chat_container = st.container()

with chat_container:
    # Mostrar historial de mensajes
    mensajes = obtener_mensajes()
    if mensajes:
        for i, mensaje in enumerate(mensajes):
            if mensaje.get("role") == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(mensaje.get("content"))
            elif mensaje.get("role") == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(mensaje.get("content"))
    else:
        # Mensaje de bienvenida estilo WhatsApp
        with st.chat_message("assistant", avatar="🤖"):
            mensaje_bienvenida = """¡Hola! 👋 Soy **iAgente_Vida**, tu asistente especializado en seguros de vida.

Para ayudarte mejor, vamos a empezar paso a paso:

**¿Cuál es tu nombre?** 😊

_Una vez que me digas tu nombre, te haré algunas preguntas sencillas para conocer tu perfil y encontrar el seguro de vida perfecto para ti._"""
            
            st.write(mensaje_bienvenida)

# Input de chat estilo WhatsApp
if prompt := st.chat_input("Escribe tu mensaje..."):
    # Verificar que tenemos un estado válido
    validar_y_reparar_estado()
    
    # Mostrar mensaje del usuario inmediatamente
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)
    
    # Procesar mensaje
    try:
        # Actualizar estado con el nuevo mensaje
        st.session_state.estado_bot.mensaje_usuario = prompt
        
        # Añadir mensaje del usuario al historial de forma segura
        agregar_mensaje("user", prompt)
        
        # Procesar con el sistema multiagente
        with st.spinner("🤖 iAgente_Vida está procesando..."):
            try:
                # Debug: mostrar configuración antes de crear el grafo
                with st.expander("🔍 Debug Info", expanded=False):
                    try:
                        # Cargar secrets de Streamlit primero
                        if hasattr(st, 'secrets'):
                            st.write("**Streamlit Secrets disponibles:**", list(st.secrets.keys()))
                            if 'OPENAI_API_KEY' in st.secrets:
                                api_key = st.secrets['OPENAI_API_KEY']
                                st.write("**API Key desde secrets:**", f"✅ {api_key[:8]}...{api_key[-4:]}")
                        
                        from src.config import settings
                        st.write("**Config:**", f"Provider: {settings.llm_provider}, Model: {settings.llm_model}")
                        st.write("**API Key desde settings:**", f"OpenAI: {'✅' if settings.openai_api_key and settings.openai_api_key != 'tu_openai_api_key_aqui' else '❌'}")
                        if settings.openai_api_key:
                            st.write("**API Key actual:**", f"{settings.openai_api_key[:8]}...{settings.openai_api_key[-4:]}")
                    except Exception as config_error:
                        st.write("**Error config:**", str(config_error)[:100])
                
                # Crear el grafo y procesar
                grafo = crear_grafo()
                resultado = grafo.invoke(st.session_state.estado_bot)
                
                # Debug: Mostrar qué devuelve el sistema - GUARDAR EN SESSION STATE
                debug_info = {
                    "tipo_resultado": str(type(resultado)),
                    "tiene_mensajes": hasattr(resultado, 'mensajes'),
                    "count_mensajes": len(resultado.mensajes) if hasattr(resultado, 'mensajes') else 0,
                    "ultimo_mensaje": resultado.mensajes[-1] if hasattr(resultado, 'mensajes') and resultado.mensajes else None,
                    "estructura": str(resultado)[:500],
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.debug_multiagente = debug_info
                
                # Verificar que el resultado tiene la estructura correcta
                if hasattr(resultado, 'mensajes') and hasattr(resultado, 'cliente'):
                    # Solo actualizar si el resultado es un objeto válido de EstadoBot
                    st.session_state.estado_bot = resultado
                    # Extraer último mensaje del sistema multiagente
                    if resultado.mensajes:
                        ultimo_mensaje = resultado.mensajes[-1]
                        if ultimo_mensaje.get('role') == 'assistant':
                            agregar_mensaje("assistant", ultimo_mensaje.get('content', 'Respuesta del sistema multiagente.'))
                elif isinstance(resultado, dict):
                    # NUEVO: Manejar diccionario con respuesta_bot
                    if 'respuesta_bot' in resultado:
                        # El sistema devolvió respuesta_bot directamente
                        agregar_mensaje("assistant", resultado['respuesta_bot'])
                        # Actualizar el estado con los datos del diccionario si los hay
                        if 'etapa' in resultado:
                            st.session_state.estado_bot.etapa = resultado['etapa']
                    elif 'mensajes' in resultado and resultado['mensajes']:
                        # Si hay mensajes en el diccionario
                        ultimo_mensaje = resultado['mensajes'][-1]
                        if ultimo_mensaje.get('role') == 'assistant':
                            agregar_mensaje("assistant", ultimo_mensaje.get('content', 'Respuesta procesada.'))
                    else:
                        # Respuesta contextual basada en el input del usuario
                        respuesta_contextual = generar_respuesta_contextual(prompt, st.session_state.estado_bot)
                        agregar_mensaje("assistant", respuesta_contextual)
                else:
                    # Respuesta contextual en lugar de genérica
                    respuesta_contextual = generar_respuesta_contextual(prompt, st.session_state.estado_bot)
                    agregar_mensaje("assistant", respuesta_contextual)
                    
            except ImportError as ie:
                with st.expander("❌ Error de Importación", expanded=True):
                    st.error(f"**Falta dependencia:** {str(ie)}")
                    st.write("**Posibles causas:**")
                    st.write("- Falta instalar una dependencia en requirements.txt")
                    st.write("- Falta configurar variables de entorno")
                respuesta_contextual = generar_respuesta_contextual(prompt, st.session_state.estado_bot)
                agregar_mensaje("assistant", respuesta_contextual)
            except Exception as grafo_error:
                with st.expander("⚠️ Error Sistema Multiagente", expanded=True):
                    st.warning(f"**Error:** {str(grafo_error)}")
                    st.write("**Tipo error:** ", type(grafo_error).__name__)
                    if hasattr(grafo_error, '__traceback__'):
                        import traceback
                        st.code(traceback.format_exc())
                # Usar respuesta contextual como fallback
                respuesta_contextual = generar_respuesta_contextual(prompt, st.session_state.estado_bot)
                agregar_mensaje("assistant", respuesta_contextual)
        
        # Forzar actualización de la interfaz
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error procesando la consulta: {str(e)}")
        
        # Añadir mensaje de error al historial de forma segura
        try:
            error_msg = "Disculpa, hubo un problema técnico. ¿Puedes repetir tu consulta?"
            agregar_mensaje("assistant", error_msg)
            
            with st.chat_message("assistant", avatar="🤖"):
                st.write(error_msg)
        except:
            # Último recurso: reinicializar completamente
            validar_y_reparar_estado()
            st.warning("Sistema reiniciado. Por favor, inténtalo de nuevo.")

# Panel de estado del sistema (parte inferior)
st.divider()

# Debug persistente del sistema multiagente
if "debug_multiagente" in st.session_state:
    debug = st.session_state.debug_multiagente
    with st.expander(f"🔍 Último Debug Sistema Multiagente ({debug['timestamp']})", expanded=False):
        st.write("**Tipo resultado:**", debug["tipo_resultado"])
        st.write("**Tiene mensajes:**", debug["tiene_mensajes"])
        st.write("**Count mensajes:**", debug["count_mensajes"])
        if debug["ultimo_mensaje"]:
            st.write("**Último mensaje:**", debug["ultimo_mensaje"])
        st.code(debug["estructura"], language="text")

# Botón de reiniciar conversación estilo WhatsApp
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Nueva Conversación", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Footer minimalista
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.7em; margin-top: 2rem;">
    🤖 iAgente_Vida - Tu asistente de seguros
</div>
""", unsafe_allow_html=True)

# Debug info removido para versión demo