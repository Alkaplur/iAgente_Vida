# iAgente_Vida

🤖 **Sistema Multi-Agente Inteligente para Seguros de Vida**

Sistema conversacional basado en LangGraph que asiste a agentes de seguros en el proceso de venta consultiva de seguros de vida.

## 🚀 Características

- **Multi-Agente**: 4 agentes especializados trabajando en coordinación
- **Needs-Based Selling**: Metodología consultiva de venta
- **Extracción Inteligente**: Captura automática de datos del cliente
- **Cotización Automática**: Generación de cotizaciones personalizadas
- **Soporte Multi-LLM**: OpenAI, Groq, Anthropic
- **Conversión de Monedas**: USD → EUR automática
- **Detección de Ingresos Anuales**: Convierte automáticamente a mensuales

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ORQUESTADOR   │───▶│ NEEDS-BASED     │───▶│     QUOTE       │
│   (Coordina)    │    │ SELLING         │    │ (Cotizaciones)  │
└─────────────────┘    │ (Necesidades)   │    └─────────────────┘
                       └─────────────────┘              │
                                ▲                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   EXTRACTOR     │    │  PRESENTADOR    │
                       │   (Datos)       │    │  (Cierre)       │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Estructura del Proyecto

```
iAgente_Vida/
├── start.py                     # 🚀 Punto de entrada
├── src/
│   ├── main.py                  # 💬 Función principal de conversación
│   ├── graph.py                 # 🕸️ Grafo LangGraph principal
│   ├── models.py                # 📋 Modelos Pydantic
│   ├── config.py                # ⚙️ Configuración del sistema
│   └── agents/
│       ├── orquestador.py       # 🧠 Agente coordinador
│       ├── extractor.py         # 🔍 Extracción de datos
│       ├── needs_based_selling.py # 🎯 Análisis de necesidades
│       ├── quote.py             # 💰 Generación de cotizaciones
│       ├── instructions_loader.py # 📚 Carga de instrucciones
│       ├── llm_client.py        # 🤖 Cliente LLM universal
│       └── agents_instructions/ # 📝 Instrucciones de cada agente
└── archivos_no_utilizados/      # 📦 Archivos de desarrollo (no usados)
```

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd iAgente_Vida
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus API keys
```

## ⚙️ Configuración

Crear archivo `.env` con:

```env
# LLM Provider (openai, groq, anthropic)
LLM_PROVIDER=openai

# API Keys
OPENAI_API_KEY=tu-api-key-aquí
GROQ_API_KEY=tu-api-key-aquí
ANTHROPIC_API_KEY=tu-api-key-aquí

# Modelos
OPENAI_MODEL=gpt-4
GROQ_MODEL=llama-3.1-70b-versatile
```

## 🚀 Uso

```bash
python start.py
```

El sistema iniciará una conversación interactiva donde podrás:
1. Proporcionar datos del cliente
2. Recibir análisis de necesidades
3. Obtener cotizaciones personalizadas
4. Gestionar objeciones y ajustes

## 💡 Ejemplos de Uso

```
👤 Tú: Mi cliente se llama Juan, tiene 35 años, 2 hijos
🤖 iAgente: Para Juan, te sugiero preguntar sobre sus ingresos...

👤 Tú: Gana 3000 USD al mes, hipoteca de 1200 USD
🤖 iAgente: Perfecto. Con 3 dependientes, te recomiendo...

👤 Tú: Genera cotización
💰 QUOTE: Generando 3 opciones personalizadas...
```

## 🔧 Características Técnicas

- **Extracción Inteligente**: Detecta nombres, edades, ingresos (USD/EUR), dependientes
- **Conversión Automática**: 2000 EUR/año → 166 EUR/mes
- **Detección de Objeciones**: "muy caro" → ajuste automático de precios
- **Flujo Bidireccional**: Quote ↔ Presentador para ajustes
- **Fallback Robusto**: Funciona sin API keys (patrones regex)

## 📊 Agentes Especializados

### 🧠 Orquestador
- Analiza intención del usuario
- Coordina flujo entre agentes
- Detecta objeciones de precio

### 🔍 Extractor
- Captura datos del cliente (regex + LLM)
- Convierte monedas y periodos
- Preserva datos existentes

### 🎯 Needs-Based Selling
- Metodología consultiva
- Recomienda productos según perfil
- Genera argumentos de venta

### 💰 Quote
- Calcula cotizaciones personalizadas
- Ajusta precios según presupuesto
- Soporte para múltiples opciones

### 📊 Presentador
- Presenta cotizaciones efectivamente
- Maneja objeciones
- Técnicas de cierre

## 🏆 Ventajas del Sistema

✅ **Conversacional**: Interacción natural con el agente de seguros
✅ **Inteligente**: Aprende del contexto de la conversación  
✅ **Flexible**: Soporte múltiples LLMs y configuraciones
✅ **Robusto**: Funciona offline con patrones regex
✅ **Escalable**: Arquitectura modular fácil de extender

## 🧹 Limpieza del Proyecto

Los archivos no utilizados han sido movidos a `archivos_no_utilizados/` para mantener el proyecto limpio:

- **Agentes alternativos** (supervisor_agent.py, research_agent.py, etc.)
- **Configuraciones no usadas** (config_manager.py, llm_config.py)
- **Tests de desarrollo** (múltiples archivos de prueba)
- **Documentación antigua** (archivos .md históricos)

Ver `archivos_no_utilizados/README.md` para más detalles.