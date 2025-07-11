# 🚀 Configuración de Woztell para WhatsApp

Guía completa para configurar la integración de iAgente_Vida con WhatsApp usando Woztell.

## 📋 Requisitos Previos

### 1. Cuenta de Woztell
- ✅ Crear cuenta en [Woztell](https://woztell.com)
- ✅ Obtener Business Token desde el panel de control
- ✅ Configurar número de WhatsApp Business

### 2. Servidor/Hosting
- ✅ Servidor con IP pública o dominio
- ✅ HTTPS habilitado (requerido para webhooks)
- ✅ Puerto accesible desde internet

## 🔧 Configuración Paso a Paso

### Paso 1: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus datos reales
```

Configurar las siguientes variables:

```env
# =====================================
# WOZTELL INTEGRATION (WHATSAPP)
# =====================================
WOZTELL_BUSINESS_TOKEN=tu_business_token_real
WOZTELL_WEBHOOK_URL=https://tu-dominio.com/webhook
WOZTELL_WEBHOOK_SECRET=tu_secret_opcional

# =====================================
# API KEYS
# =====================================
OPENAI_API_KEY=tu_openai_key
GROQ_API_KEY=tu_groq_key

# =====================================
# WEBHOOK CONFIGURATION
# =====================================
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
DEBUG=false
```

### Paso 2: Instalar Dependencias

```bash
# Instalar dependencias
pip install -r requirements.txt

# Para desarrollo
pip install -r requirements-dev.txt
```

### Paso 3: Configurar Webhook en Woztell

1. **Ir al panel de Woztell**
2. **Configurar Webhook URL:**
   ```
   https://tu-dominio.com/webhook
   ```
3. **Configurar eventos a recibir:**
   - ✅ Mensajes entrantes
   - ✅ Estado de mensajes (opcional)
   - ✅ Cambios de estado (opcional)

### Paso 4: Probar la Configuración

```bash
# Ejecutar en modo desarrollo
python webhook_app.py

# O usando gunicorn para producción
gunicorn -w 4 -b 0.0.0.0:5000 webhook_app:app
```

## 🧪 Testing

### Test Manual de Envío

```bash
# Enviar mensaje de prueba
curl -X POST "http://localhost:5000/send_message" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "34600000000",
    "message": "¡Hola! Esto es una prueba desde iAgente_Vida."
  }'
```

### Test de Webhook

```bash
# Simular webhook entrante
curl -X POST "http://localhost:5000/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "34600000000",
    "message": {
      "type": "text",
      "text": "Hola, quiero información sobre seguros"
    }
  }'
```

### Health Check

```bash
# Verificar estado del servicio
curl http://localhost:5000/health
```

## 📊 Endpoints Disponibles

### Webhook Principal
- **POST /webhook** - Recibe mensajes de Woztell
- **GET /webhook** - Verificación de webhook (si requerido)

### Utilidades
- **GET /health** - Health check
- **GET /stats** - Estadísticas básicas
- **POST /send_message** - Enviar mensajes manuales

## 🔒 Seguridad

### Variables Sensibles
- ❌ **Nunca** commits las API keys reales
- ✅ **Siempre** usar variables de entorno
- ✅ **Configurar** HTTPS en producción
- ✅ **Validar** firmas de webhook si es posible

### Rate Limiting
- ✅ 10 mensajes por minuto por IP
- ✅ 200 mensajes por día por IP
- ✅ Protección contra spam

## 📈 Monitoreo

### Logs
Los logs se guardan en:
- `webhook.log` - Logs de la aplicación
- Stdout - Logs en tiempo real

### Métricas Importantes
- Mensajes procesados
- Usuarios activos
- Errores de API
- Tiempo de respuesta

## 🚀 Despliegue en Producción

### Usando Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "webhook_app:app"]
```

### Usando Render/Railway

```yaml
# render.yaml
services:
  - type: web
    name: iagente-vida-webhook
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT webhook_app:app
    envVars:
      - key: WOZTELL_BUSINESS_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

### Variables de Entorno en Producción

```bash
# Configurar en tu plataforma de hosting
WOZTELL_BUSINESS_TOKEN=tu_token_real
OPENAI_API_KEY=tu_key_real
GROQ_API_KEY=tu_key_real
DEBUG=false
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
```

## 🛠️ Troubleshooting

### Problema: "No se reciben mensajes"
- ✅ Verificar que la URL del webhook sea HTTPS
- ✅ Confirmar que el puerto esté abierto
- ✅ Revisar logs para errores
- ✅ Probar con curl manualmente

### Problema: "Error 401 - Invalid token"
- ✅ Verificar WOZTELL_BUSINESS_TOKEN
- ✅ Regenerar token en el panel de Woztell
- ✅ Verificar formato del token

### Problema: "Error 500 - Internal Server Error"
- ✅ Revisar logs de la aplicación
- ✅ Verificar configuración de API keys
- ✅ Comprobar estado del sistema multiagente

### Problema: "Rate limit exceeded"
- ✅ Implementar cola de mensajes
- ✅ Reducir frecuencia de envío
- ✅ Contactar soporte de Woztell

## 📞 Soporte

### Documentación Oficial
- [Woztell Docs](https://doc.woztell.com/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)

### Logs de Debug
```bash
# Activar debug mode
export DEBUG=true
python webhook_app.py

# Ver logs en tiempo real
tail -f webhook.log
```

## 🎯 Próximos Pasos

Una vez configurado correctamente:

1. **Configurar dominio personalizado**
2. **Implementar métricas avanzadas**
3. **Añadir soporte para multimedia**
4. **Integrar con CRM (Chatwoot)**
5. **Optimizar performance**

---

✨ **¡Tu integración con WhatsApp está lista!** Los usuarios ya pueden interactuar con iAgente_Vida directamente desde WhatsApp.