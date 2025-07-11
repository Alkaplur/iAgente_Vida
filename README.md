# iAgente_Vida - Sistema Multi-Agente para Seguros de Vida

## 🎯 **Sistema Especializado en Seguros de Vida**

Sistema multi-agente desarrollado con LangGraph que asiste a agentes de seguros en la venta consultiva de seguros de vida. Integra datos modulares, cálculos actuariales y técnicas de venta profesionales.

## 🏗️ **Arquitectura**

```
iAgente_Vida/
├── src/                    # Código fuente
│   ├── agents/            # Agentes especializados
│   │   ├── orquestador.py    # Coordina el flujo
│   │   ├── needs_based_selling.py # Análisis consultivo
│   │   ├── quote.py          # Cotizaciones actuariales
│   │   ├── presentador.py    # Manejo de objeciones y cierre
│   │   ├── extractor.py      # Extracción de datos del cliente
│   │   ├── llm_client.py     # Cliente universal LLM
│   │   └── instructions_loader.py # Carga instrucciones
│   ├── utils/             # Utilidades modulares
│   │   ├── motor_cotizacion.py   # Cálculos actuariales
│   │   └── productos_loader.py   # Catálogo de productos
│   ├── data/              # Datos externos (editables sin programar)
│   │   ├── productos_seguros.txt # 18 productos de vida especializados
│   │   └── motor_cotizacion.txt  # Fórmulas actuariales configurables
│   ├── models.py          # Estructuras de datos (Pydantic)
│   ├── config.py          # Configuración del sistema
│   ├── graph.py           # Orquestador LangGraph
│   └── main.py            # Función principal
├── docs/                  # Documentación y diagramas
├── start.py               # Punto de entrada
├── langgraph.json         # Configuración LangGraph Studio
├── requirements.txt       # Dependencias mínimas
└── .env                   # Variables de entorno
```

## 🚀 **Instalación y Uso**

### **1. Instalación**
```bash
git clone <repo>
cd iAgente_Vida
pip install -r requirements.txt
```

### **2. Configuración**
Edita el archivo `.env`:
```env
LLM_PROVIDER=openai  # o groq, anthropic
OPENAI_API_KEY=tu_api_key_aqui
LANGCHAIN_API_KEY=tu_langchain_key  # Para tracing
```

### **3. Modos de Ejecución**

#### **Chat Interactivo**
```bash
python start.py
```

#### **LangGraph Studio (Visualización Web)**
```bash
langgraph dev
```
Luego abrir: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

## 🧠 **Agentes Especializados**

### **1. 🎯 Orquestador**
- Analiza la intención del usuario
- Deriva al agente apropiado
- Mantiene el flujo de conversación

### **2. 📋 Needs-Based Selling**
- Análisis consultivo del cliente
- Recopila datos (edad, dependientes, ingresos)
- Recomienda productos específicos
- Usa técnicas de venta consultiva

### **3. 💰 Quote (Cotizador)**
- Cálculos actuariales precisos
- Múltiples opciones de precio
- Ajustes por profesión y riesgo
- Integración con motor de cotización

### **4. 📊 Presentador**
- Presenta cotizaciones atractivamente
- Maneja objeciones del cliente
- Técnicas de cierre profesionales
- Scripts de venta específicos

### **5. 🔍 Extractor**
- Captura datos del cliente inteligentemente
- Usa regex + LLM para extracción híbrida
- Convierte formatos y monedas
- Validación de datos extraídos

## 📊 **Sistema Modular Único**

### **Catálogo de Productos Editable**
- **18 productos** especializados en seguros de vida
- **3 categorías**: Vida Término, Vida Completa, Vida con Ahorro
- **Editable**: Sin necesidad de programar
- **Archivo**: `src/data/productos_seguros.txt`

### **Motor de Cotización Configurable**
- **Fórmulas actuariales** reales
- **Tasas por edad** y profesión
- **Multiplicadores** configurables
- **Archivo**: `src/data/motor_cotizacion.txt`

## 🎯 **Características Técnicas**

### **Multi-LLM Support**
- ✅ OpenAI (GPT-4, GPT-4o-mini)
- ✅ Groq (Llama 3, Mixtral)
- ✅ Anthropic (Claude)

### **Arquitectura Profesional**
- ✅ LangGraph para orquestación
- ✅ Pydantic para validación de datos
- ✅ Imports duales (Studio + directo)
- ✅ Configuración por archivos

### **Observabilidad**
- ✅ LangChain Tracing integrado
- ✅ Visualización web del grafo
- ✅ Debugging en tiempo real

## 📈 **Flujo de Trabajo Típico**

```
1. Usuario: "Cliente de 35 años con 2 hijos"
   → ORQUESTADOR → NEEDS_BASED_SELLING

2. "¿Cuáles son sus ingresos mensuales?"
   → "3000 euros" → NEEDS_BASED_SELLING

3. "Te recomiendo Vida Completa Plus"
   → "Dame cotizaciones" → QUOTE

4. "Opción 1: 45€/mes - 150,000€ cobertura"
   → "Muy caro" → PRESENTADOR

5. "Explícale que por 45€ protege 150,000€..."
```

## 🔧 **Configuración Avanzada**

### **LangChain Tracing**
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=tu_key
LANGCHAIN_PROJECT=iAgente_Vida
```

### **Personalización de Productos**
Edita `src/data/productos_seguros.txt`:
```
VIDA_TERMINO|Nuevo Producto|fallecimiento|Características|Adicionales|Público|Argumentos
```

### **Ajuste de Fórmulas**
Edita `src/data/motor_cotizacion.txt`:
```
TASAS_EDAD
30|35|0.0015|Adultos - Riesgo moderado
```

## 📝 **Desarrollado por:**
- **Arquitectura**: LangGraph multi-agente
- **Validación**: Pydantic
- **LLMs**: OpenAI, Groq, Anthropic
- **Especialización**: Seguros de vida únicamente
- **Modularidad**: Datos externos editables

---

**Para más detalles, consulta la documentación completa en `/docs/`**