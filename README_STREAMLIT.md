# 🤖 iAgente_Vida - Interfaz Web

Interfaz web desarrollada con Streamlit para el sistema multiagente iAgente_Vida.

## 🚀 Características

- ✅ **Chat interactivo** con sistema multiagente
- ✅ **Panel de cliente** con datos editables en tiempo real
- ✅ **Análisis automático** de capacidad de pago
- ✅ **Visualización de progreso** y estadísticas
- ✅ **Interfaz profesional** y responsive
- ✅ **Debug mode** para desarrollo

## 🏃‍♂️ Ejecución Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys reales

# Ejecutar interfaz web
streamlit run streamlit_app.py
```

## 🌐 Deploy en Streamlit Cloud

### 1. Subir a GitHub
- Asegúrate de que todo el proyecto esté en GitHub
- Incluir archivos: `streamlit_app.py`, `requirements.txt`, `.streamlit/config.toml`, `.env.example`

### 2. Conectar con Streamlit Cloud
1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Conectar repositorio GitHub
4. **Main file path:** `streamlit_app.py` (detectado automáticamente)
5. **Python version:** 3.9+ 

### 3. Configurar Variables de Entorno
En Streamlit Cloud, añadir estos secrets:

```toml
# Secrets en Streamlit Cloud
[secrets]
OPENAI_API_KEY = "sk-..."
GROQ_API_KEY = "gsk_..."
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"
BOT_NAME = "iAgente_Vida"

# Opcional - para Chatwoot
CHATWOOT_BASE_URL = "https://app.chatwoot.com"
CHATWOOT_ACCOUNT_ID = "123456"
CHATWOOT_USER_TOKEN = "token_aquí"
```

## 📋 Funcionalidades de la Interfaz

### Panel Lateral (Datos del Cliente)
- **Datos básicos:** Nombre, edad, estado civil, profesión
- **Información financiera:** Ingresos, gastos, dependientes
- **Datos adicionales:** Salud, seguros actuales
- **Análisis automático:** Ingreso disponible, prima máxima

### Chat Principal
- **Conversación interactiva** con iAgente_Vida
- **Historial completo** de mensajes
- **Respuestas en tiempo real** del sistema multiagente
- **Manejo de errores** con fallbacks

### Panel de Estado
- **Etapa actual** del proceso (inicio, análisis, cotización, etc.)
- **Agente activo** (orquestador, needs-based, cotizador, etc.)
- **Estadísticas** de mensajes y cotizaciones
- **Progreso visual** de la conversación

## 🔧 Configuración Avanzada

### Variables de Entorno (Opcionales)
```bash
# Proveedor LLM
LLM_PROVIDER=openai  # o "groq"
LLM_MODEL=gpt-4o-mini

# Debug
DEBUG=false
STREAMLIT_DEV_MODE=false
```

### Personalización
- **Tema:** Editar `.streamlit/config.toml`
- **Datos por defecto:** Modificar valores en `web_interface.py`
- **Mensajes:** Personalizar texto de bienvenida

## 🐛 Debug y Desarrollo

### Modo Debug
Activar checkbox "Mostrar información de debug" para ver:
- Estado completo del bot
- Estructura JSON de datos
- Variables internas del sistema

### Logs
```bash
# Ver logs en tiempo real
streamlit run src/web_interface.py --logger.level=debug
```

## 🔐 Seguridad

### Variables Sensibles
- ❌ **Nunca** incluir API keys en el código
- ✅ **Siempre** usar secrets de Streamlit Cloud
- ✅ **Validar** entradas del usuario

### Datos del Cliente
- Los datos se mantienen solo en sesión
- No se almacenan permanentemente
- Reset automático al reiniciar

## 📈 Performance

### Optimizaciones
- **Cache** de instrucciones cargadas
- **Estado en sesión** para persistencia
- **Lazy loading** de componentes pesados

### Límites de Streamlit Community Cloud
- **RAM:** ~1GB
- **CPU:** Limitado
- **Tiempo:** Se "duerme" tras inactividad
- **Requests:** ~1000/mes en plan gratuito

## 🚀 URL Final
Una vez desplegado, tendrás una URL como:
`https://iagente-vida-tuusuario.streamlit.app`

## 📞 Soporte
Para problemas específicos de Streamlit:
- [Documentación oficial](https://docs.streamlit.io)
- [Foro de la comunidad](https://discuss.streamlit.io)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)