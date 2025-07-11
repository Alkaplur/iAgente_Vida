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
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from src.graph import crear_grafo
    from src.models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion
except ImportError:
    from graph import crear_grafo
    from models import EstadoBot, Cliente, ContextoConversacional, EstadoConversacion

# Configurar página
st.set_page_config(
    page_title="iAgente_Vida - Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
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
st.markdown("""
<div class="main-header">
    <h1>🤖 iAgente_Vida</h1>
    <p><em>Sistema Multiagente para Asesoramiento en Seguros de Vida</em></p>
</div>
""", unsafe_allow_html=True)

# Sidebar con información del cliente
with st.sidebar:
    st.header("👤 Perfil del Cliente")
    
    # Datos básicos
    st.subheader("📋 Datos Básicos")
    cliente_nombre = st.text_input("Nombre", value="Juan Pérez", help="Nombre del cliente")
    cliente_edad = st.number_input("Edad", min_value=18, max_value=80, value=35)
    cliente_estado_civil = st.selectbox("Estado Civil", ["soltero", "casado", "divorciado", "viudo"], index=1)
    cliente_profesion = st.text_input("Profesión", value="Ingeniero")
    
    # Datos financieros
    st.subheader("💰 Información Financiera")
    cliente_ingresos = st.number_input("Ingresos mensuales (€)", min_value=0, value=3500, step=100)
    cliente_gastos = st.number_input("Gastos fijos mensuales (€)", min_value=0, value=2200, step=100)
    cliente_dependientes = st.number_input("Número de dependientes", min_value=0, value=2)
    
    # Datos adicionales
    st.subheader("🏥 Información Adicional")
    cliente_salud = st.selectbox("Salud relevante", ["no fumador", "fumador", "deportista", "no especificado"], index=0)
    cliente_seguro_actual = st.selectbox("¿Tiene seguro de vida actual?", ["No", "Sí - Básico", "Sí - Completo"], index=0)
    
    # Cálculo automático de ingreso disponible
    ingreso_disponible = max(0, cliente_ingresos - cliente_gastos)
    
    st.subheader("📊 Análisis Automático")
    st.metric("Ingreso Disponible", f"€{ingreso_disponible:,.0f}/mes")
    
    if ingreso_disponible > 0:
        prima_max_recomendada = ingreso_disponible * 0.10
        prima_max_absoluta = ingreso_disponible * 0.15
        st.metric("Prima Máx. Recomendada (10%)", f"€{prima_max_recomendada:.0f}/mes")
        st.metric("Prima Máx. Absoluta (15%)", f"€{prima_max_absoluta:.0f}/mes")
    
    st.divider()
    
    # Botones de control
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reiniciar", help="Reiniciar conversación", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    with col2:
        if st.button("📋 Ejemplo", help="Cargar datos de ejemplo", use_container_width=True):
            st.session_state.ejemplo_cargado = True
            st.rerun()

# Función para inicializar estado
def inicializar_estado():
    """Inicializa el estado del bot con los datos del cliente"""
    cliente = Cliente(
        nombre=cliente_nombre,
        edad=cliente_edad,
        estado_civil=cliente_estado_civil,
        profesion=cliente_profesion,
        ingresos_mensuales=float(cliente_ingresos),
        gastos_fijos_mensuales=float(cliente_gastos),
        num_dependientes=int(cliente_dependientes),
        salud_relevante=cliente_salud,
        tiene_seguro_vida=(cliente_seguro_actual != "No")
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

# Inicializar estado si no existe
if "estado_bot" not in st.session_state:
    st.session_state.estado_bot = inicializar_estado()

# Actualizar datos del cliente en tiempo real
st.session_state.estado_bot.cliente.nombre = cliente_nombre
st.session_state.estado_bot.cliente.edad = cliente_edad
st.session_state.estado_bot.cliente.estado_civil = cliente_estado_civil
st.session_state.estado_bot.cliente.profesion = cliente_profesion
st.session_state.estado_bot.cliente.ingresos_mensuales = float(cliente_ingresos)
st.session_state.estado_bot.cliente.gastos_fijos_mensuales = float(cliente_gastos)
st.session_state.estado_bot.cliente.num_dependientes = int(cliente_dependientes)
st.session_state.estado_bot.cliente.salud_relevante = cliente_salud
st.session_state.estado_bot.cliente.tiene_seguro_vida = (cliente_seguro_actual != "No")

# Área principal de chat
st.subheader("💬 Conversación con iAgente_Vida")

# Contenedor para mensajes
chat_container = st.container()

with chat_container:
    # Mostrar historial de mensajes
    if st.session_state.estado_bot.mensajes:
        for i, mensaje in enumerate(st.session_state.estado_bot.mensajes):
            if mensaje.get("role") == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(mensaje.get("content"))
            elif mensaje.get("role") == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(mensaje.get("content"))
    else:
        # Mensaje de bienvenida
        with st.chat_message("assistant", avatar="🤖"):
            st.write(f"""
            ¡Hola! Soy **iAgente_Vida**, tu asistente especializado en seguros de vida.
            
            Veo que estás asesorando a **{cliente_nombre}** ({cliente_edad} años).
            
            Con sus ingresos de **€{cliente_ingresos:,.0f}/mes** y **{cliente_dependientes} dependientes**, 
            puedo ayudarte a encontrar la protección ideal.
            
            **¿En qué puedo ayudarte hoy?**
            - Calcular cobertura recomendada
            - Generar cotizaciones personalizadas  
            - Analizar capacidad de pago
            - Comparar tipos de productos
            """)

# Input de chat
if prompt := st.chat_input("Escribe tu consulta sobre seguros de vida..."):
    # Mostrar mensaje del usuario inmediatamente
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)
    
    # Actualizar estado con el nuevo mensaje
    st.session_state.estado_bot.mensaje_usuario = prompt
    
    # Añadir mensaje del usuario al historial
    st.session_state.estado_bot.mensajes.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })
    
    # Procesar con el sistema multiagente
    try:
        with st.spinner("🤖 iAgente_Vida está procesando..."):
            # Crear el grafo y procesar
            grafo = crear_grafo()
            resultado = grafo.invoke(st.session_state.estado_bot)
            st.session_state.estado_bot = resultado
        
        # Mostrar respuesta del asistente
        if (st.session_state.estado_bot.mensajes and 
            st.session_state.estado_bot.mensajes[-1].get("role") == "assistant"):
            
            ultima_respuesta = st.session_state.estado_bot.mensajes[-1].get("content")
            with st.chat_message("assistant", avatar="🤖"):
                st.write(ultima_respuesta)
        
    except Exception as e:
        st.error(f"❌ Error procesando la consulta: {str(e)}")
        
        # Añadir mensaje de error al historial
        error_msg = "Disculpa, hubo un problema técnico. ¿Puedes repetir tu consulta?"
        st.session_state.estado_bot.mensajes.append({
            "role": "assistant",
            "content": error_msg,
            "timestamp": datetime.now().isoformat()
        })
        
        with st.chat_message("assistant", avatar="🤖"):
            st.write(error_msg)

# Panel de estado del sistema (parte inferior)
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📊 Estado del Sistema**")
    estado_actual = st.session_state.estado_bot.etapa.value if st.session_state.estado_bot.etapa else "inicio"
    st.info(f"**Etapa:** {estado_actual}")
    st.info(f"**Agente Activo:** {st.session_state.estado_bot.agente_activo}")

with col2:
    st.markdown("**💬 Estadísticas**")
    st.metric("Mensajes", len(st.session_state.estado_bot.mensajes))
    st.metric("Cotizaciones", len(st.session_state.estado_bot.cotizaciones))

with col3:
    st.markdown("**🎯 Progreso**")
    if st.session_state.estado_bot.recomendacion_producto:
        st.success("✅ Recomendación generada")
    else:
        st.warning("⏳ Recopilando datos...")
    
    if st.session_state.estado_bot.cotizaciones:
        st.success(f"✅ {len(st.session_state.estado_bot.cotizaciones)} cotizaciones")
    else:
        st.info("📋 Sin cotizaciones aún")

# Footer con información
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8em;">
    🤖 <strong>iAgente_Vida</strong> - Sistema Multiagente para Seguros de Vida<br>
    <em>Desarrollado con LangGraph, OpenAI/Groq y Streamlit</em>
</div>
""", unsafe_allow_html=True)

# Debug info (solo en desarrollo)
if st.checkbox("🔧 Mostrar información de debug", value=False):
    with st.expander("Estado completo del bot"):
        st.json({
            "etapa": estado_actual,
            "agente_activo": st.session_state.estado_bot.agente_activo,
            "next_agent": st.session_state.estado_bot.next_agent,
            "cliente": {
                "nombre": st.session_state.estado_bot.cliente.nombre,
                "edad": st.session_state.estado_bot.cliente.edad,
                "ingresos": st.session_state.estado_bot.cliente.ingresos_mensuales,
                "dependientes": st.session_state.estado_bot.cliente.num_dependientes
            },
            "mensajes_count": len(st.session_state.estado_bot.mensajes),
            "cotizaciones_count": len(st.session_state.estado_bot.cotizaciones)
        })