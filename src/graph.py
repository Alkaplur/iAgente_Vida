"""
Orquestador principal usando LangGraph para el sistema multi-agente
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

try:
    from .models import EstadoBot, EstadoConversacion, Cliente, ContextoConversacional, RecomendacionProducto
    from .agents.orquestador import orquestador_node, route_to_agent
    from .agents.extractor import extraer_datos_cliente, resetear_contexto_pregunta
    from .agents.needs_based_selling import needs_based_selling_node
    from .agents.presentador import presentador_node
    from .config import settings
    from .agents.instructions_loader import cargar_instrucciones_cached
    from .agents.llm_client import get_llm_response
except ImportError:
    from models import EstadoBot, EstadoConversacion, Cliente, ContextoConversacional, RecomendacionProducto
    from agents.orquestador import orquestador_node, route_to_agent
    from agents.extractor import extraer_datos_cliente, resetear_contexto_pregunta
    from agents.needs_based_selling import needs_based_selling_node
    from agents.presentador import presentador_node
    from config import settings
    from agents.instructions_loader import cargar_instrucciones_cached
    from agents.llm_client import get_llm_response

from groq import Groq
import os


# Configurar tracing si está disponible
if os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"


def process_message(state: EstadoBot) -> EstadoBot:
    """
    Función principal para procesar mensajes desde webhooks externos
    Ejecuta el grafo completo y retorna el estado actualizado
    """
    try:
        # Crear el grafo si no existe
        graph = crear_grafo()
        
        # Ejecutar el grafo con el estado proporcionado
        result = graph.invoke(state)
        
        return result
        
    except Exception as e:
        print(f"❌ Error en process_message: {e}")
        
        # Retornar estado con mensaje de error
        state.mensajes.append({
            "role": "assistant", 
            "content": "Disculpa, hubo un problema técnico. ¿Puedes repetir tu consulta?",
            "timestamp": str(os.getenv("TIMESTAMP", ""))
        })
        return state


def quote_node(state: EstadoBot) -> Dict[str, Any]:
    """
    Agente especializado en generar cotizaciones basadas en:
    - Datos del cliente
    - Recomendación de producto del needs-based selling
    """
    
    print(f"💰 QUOTE AGENT: {state.cliente.nombre}")
    
    # Importar y usar el cotizador
    try:
        from .agents.quote import calcular_cotizaciones, generar_presentacion
    except ImportError:
        from agents.quote import calcular_cotizaciones, generar_presentacion
    
    try:
        # Verificar si el orquestador indica ajuste de precio por objeción
        ajustar_precio = False
        presupuesto_objetivo = None
        
        if hasattr(state.contexto, 'instrucciones_agente') and state.contexto.instrucciones_agente:
            instrucciones = state.contexto.instrucciones_agente.lower()
            if any(palabra in instrucciones for palabra in ['muy caro', 'ajusta', 'económico', 'más barato', 'reducir', 'baja', 'menos']):
                ajustar_precio = True
                print(f"   🔧 PRECIO AJUSTADO: Generando opciones más económicas por objeción")
        elif hasattr(state.contexto, '__dict__') and 'instrucciones_agente' in state.contexto.__dict__:
            instrucciones = state.contexto.__dict__['instrucciones_agente'].lower()
            if any(palabra in instrucciones for palabra in ['muy caro', 'ajusta', 'económico', 'más barato', 'reducir', 'baja', 'menos']):
                ajustar_precio = True
                print(f"   🔧 PRECIO AJUSTADO: Generando opciones más económicas por objeción")
        
        # También verificar en el mensaje del usuario directamente
        mensaje_usuario = state.mensaje_usuario.lower()
        if any(palabra in mensaje_usuario for palabra in ['70 euros', '60 euros', '80 euros', 'euros al mes', 'baja', 'reducir', 'ajustar']):
            ajustar_precio = True
            
            # Intentar extraer presupuesto específico
            import re
            match = re.search(r'(\d+)\s*euros?\s*al\s*mes', mensaje_usuario)
            if match:
                presupuesto_objetivo = float(match.group(1))
        
        # Generar cotizaciones basadas en cliente + recomendación (con ajuste si es necesario)
        cotizaciones = calcular_cotizaciones(state.cliente, state.recomendacion_producto, ajustar_precio, presupuesto_objetivo)
        
        # Generar presentación de las cotizaciones
        mensaje_cotizaciones = generar_presentacion(state.cliente, cotizaciones)
        
        return {
            "respuesta_bot": mensaje_cotizaciones,
            "cliente": state.cliente,
            "cotizaciones": cotizaciones,
            "recomendacion_producto": state.recomendacion_producto,
            "etapa": EstadoConversacion.COTIZACION,
            "contexto": state.contexto,
            "mensajes": state.mensajes + [{"bot": mensaje_cotizaciones}] if state.mensajes else [{"bot": mensaje_cotizaciones}]
        }
        
    except Exception as e:
        print(f"⚠️ Error generando cotizaciones: {e}")
        return {
            "respuesta_bot": f"Disculpa {state.cliente.nombre}, estoy teniendo un problema técnico generando las cotizaciones. ¿Podrías darme un momento?",
            "cliente": state.cliente,
            "etapa": EstadoConversacion.COTIZACION,
            "contexto": state.contexto
        }


def crear_grafo():
    """Crea el grafo multi-agente con LangGraph"""
    
    workflow = StateGraph(EstadoBot)
    
    # Añadir todos los nodos
    workflow.add_node("orquestador", orquestador_node)
    workflow.add_node("needs_based_selling", needs_based_selling_node)
    workflow.add_node("quote", quote_node)
    workflow.add_node("presentador", presentador_node)
    
    # Punto de entrada: siempre el orquestador
    workflow.set_entry_point("orquestador")
    
    # El orquestador decide a qué agente enviar
    workflow.add_conditional_edges(
        "orquestador",
        route_to_agent,
        {
            "needs_based_selling": "needs_based_selling",
            "quote": "quote",
            "presentador": "presentador",
            "__end__": END
        }
    )
    
    # Los agentes terminan y esperan el siguiente input del usuario
    workflow.add_edge("needs_based_selling", END)
    workflow.add_edge("quote", END)
    workflow.add_edge("presentador", END)
    
    return workflow.compile()


# Crear instancia del grafo
graph = crear_grafo()


def visualizar_grafo():
    """Genera visualización del grafo en formato Mermaid"""
    
    try:
        # Intentar usar get_graph si está disponible
        mermaid_graph = graph.get_graph().draw_mermaid()
        print("=== DIAGRAMA MERMAID DEL GRAFO ===")
        print(mermaid_graph)
        
        # Guardar en archivo
        with open('graph_mermaid.md', 'w', encoding='utf-8') as f:
            f.write("# iAgente_Vida - Grafo LangGraph\n\n")
            f.write("Generado con `graph.get_graph().draw_mermaid()`\n\n")
            f.write("## Diagrama Mermaid\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_graph)
            f.write("\n```\n\n")
            f.write("## Visualización Online\n\n")
            f.write("1. Copia el código Mermaid de arriba\n")
            f.write("2. Ve a https://mermaid.live\n")
            f.write("3. Pega el código en el editor\n")
            f.write("4. Visualiza el diagrama interactivo\n")
        
        print("\n✅ Diagrama guardado en 'graph_mermaid.md'")
        print("📋 Copia el contenido y pégalo en: https://mermaid.live")
        
        return mermaid_graph
        
    except Exception as e:
        print(f"❌ Error generando diagrama: {e}")
        return None


if __name__ == "__main__":
    print("🔍 Visualizando grafo de iAgente_Vida...")
    visualizar_grafo()