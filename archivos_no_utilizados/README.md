# Archivos No Utilizados - iAgente_Vida

Esta carpeta contiene archivos que **NO están en uso** en el sistema principal actual.

## 📁 Estructura del Contenido

### `/agents/` - Agentes Alternativos (Sistema LangGraph Complejo)
- `supervisor_agent.py` - Sistema de supervisión alternativo
- `research_agent.py` - Agente de investigación no utilizado  
- `quote_agent.py` - Agente de cotización alternativo (clase)
- `presenter_agent.py` - Agente presentador alternativo (clase)
- `supervisor_instructions.txt` - Instrucciones del supervisor no utilizado

### `/config/` - Configuraciones Alternativas
- `llm_config.py` - Configuración LLM alternativa
- `config_manager.py` - Gestor de configuración no utilizado

### `/tests_antiguos/` - Tests de Desarrollo
- Varios archivos de pruebas utilizados durante el desarrollo
- Tests de API keys, extracción de datos, casos específicos

### `/docs_antiguas/` - Documentación de Desarrollo
- `CORRECCIONES_SISTEMA.md` - Historial de correcciones
- `MEJORAS_SISTEMA.md` - Mejoras implementadas
- `SISTEMA_LLM_PRINCIPAL.md` - Documentación técnica
- `SOLUCION_DATOS.md` - Soluciones de extracción de datos

### Archivos Raíz No Utilizados
- `universal_llm_client.py` - Cliente LLM universal más complejo
- `handoff_tools.py` - Herramientas de handoff entre agentes
- `langgraph_workflow.py` - Workflow LangGraph alternativo
- `whatsapp.py` - Integración WhatsApp opcional

## ⚠️ Importante

**Estos archivos se pueden eliminar de forma segura** ya que:
1. No se importan en el flujo principal del sistema
2. No afectan el funcionamiento del sistema actual
3. Representan implementaciones alternativas o código de desarrollo

## 🔄 Sistema Principal Actual

El sistema actual utiliza únicamente:
- `src/graph.py` - Grafo LangGraph simplificado
- `src/agents/orquestador.py` - Coordinador principal
- `src/agents/extractor.py` - Extracción de datos
- `src/agents/needs_based_selling.py` - Análisis de necesidades  
- `src/agents/quote.py` - Generación de cotizaciones
- `src/agents/instructions_loader.py` - Carga de instrucciones
- `src/agents/llm_client.py` - Cliente LLM simple

## 📅 Fecha de Limpieza
Limpieza realizada en: ${new Date().toLocaleDateString()}