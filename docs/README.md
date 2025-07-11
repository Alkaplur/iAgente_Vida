# iAgente_Vida - Sistema Multi-Agente para Seguros de Vida

## 📋 Estructura del Proyecto

```
iAgente_Vida/
├── src/                    # Código fuente
│   ├── agents/            # Agentes especializados
│   │   ├── orquestador.py    # Coordina el flujo
│   │   ├── needs_based_selling.py # Análisis consultivo
│   │   ├── quote.py          # Cotizaciones
│   │   ├── extractor.py      # Extracción de datos
│   │   ├── llm_client.py     # Cliente universal LLM
│   │   └── instructions_loader.py # Carga instrucciones
│   ├── utils/             # Utilidades modulares
│   │   ├── motor_cotizacion.py   # Cálculos actuariales
│   │   └── productos_loader.py   # Catálogo de productos
│   ├── data/              # Datos externos (editables)
│   │   ├── productos_seguros.txt # Catálogo de productos
│   │   └── motor_cotizacion.txt  # Fórmulas actuariales
│   ├── models.py          # Estructuras de datos (Pydantic)
│   ├── config.py          # Configuración del sistema
│   ├── graph.py           # Orquestador LangGraph
│   └── main.py            # Función principal
├── start.py               # Punto de entrada
├── langgraph.json         # Configuración LangGraph Studio
├── requirements.txt       # Dependencias Python
└── .env                   # Variables de entorno

```

## 🚀 Modos de Ejecución

### Chat Interactivo
```bash
python start.py
```

### LangGraph Studio (Visualización Web)
```bash
langgraph dev
```
Luego abrir: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

## 🎯 Agentes Especializados

1. **Orquestador**: Analiza intención y deriva al agente apropiado
2. **Needs-Based Selling**: Recopila datos y recomienda productos
3. **Quote**: Genera cotizaciones actuariales precisas
4. **Extractor**: Captura información del cliente
5. **Presentador**: Maneja objeciones y cierre de ventas

## 📊 Sistema Modular

- **Productos**: 18 seguros de vida en `data/productos_seguros.txt`
- **Cotizaciones**: Fórmulas actuariales en `data/motor_cotizacion.txt`
- **Configuración**: Variables en `.env`

## 🔧 Configuración

Ver `.env` para configurar:
- Proveedor LLM (OpenAI, Groq, Anthropic)
- API Keys
- LangChain Tracing
- Parámetros del sistema