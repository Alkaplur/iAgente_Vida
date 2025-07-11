# 🚀 Integración WhatsApp Business para iAgente_Vida

Esta documentación describe cómo configurar y usar la integración completa de WhatsApp Business API con el sistema iAgente_Vida y Chatwoot.

## 📋 Componentes Implementados

### 1. **WhatsApp Client** (`src/integrations/whatsapp_client.py`)
- ✅ Envío de mensajes de texto
- ✅ Mensajes con plantillas aprobadas
- ✅ Mensajes interactivos con botones
- ✅ Manejo de archivos multimedia
- ✅ Parsing de webhooks entrantes
- ✅ Marcado de mensajes como leídos

### 2. **Chatwoot Client** (`src/integrations/chatwoot_client.py`)
- ✅ Gestión de contactos
- ✅ Creación y seguimiento de conversaciones
- ✅ Sincronización bidireccional
- ✅ Etiquetado automático
- ✅ Tracking de leads

### 3. **Webhook System** (`src/webhooks/whatsapp_webhook.py`)
- ✅ Recepción de mensajes WhatsApp
- ✅ Verificación de webhook Meta
- ✅ Estado persistente por conversación
- ✅ Integración con grafo LangGraph
- ✅ Manejo de errores robusto

## 🔧 Configuración

### 1. Variables de Entorno (.env)

```bash
# WhatsApp Business API
WHATSAPP_TOKEN=tu_access_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_VERIFY_TOKEN=tu_token_verificacion

# Chatwoot (Opcional pero recomendado)
CHATWOOT_BASE_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=tu_account_id
CHATWOOT_USER_TOKEN=tu_user_token
CHATWOOT_PLATFORM_TOKEN=tu_platform_token
CHATWOOT_WHATSAPP_INBOX_ID=tu_inbox_id

# Webhook Configuration
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
DEBUG=false
```

### 2. Obtener Credenciales WhatsApp

#### Meta Business Suite:
1. Ir a [Meta for Developers](https://developers.facebook.com/)
2. Crear una nueva aplicación
3. Añadir producto "WhatsApp Business API"
4. Configurar webhook URL: `https://tu-servidor.com/webhook/whatsapp`
5. Token de verificación: el que pongas en `WHATSAPP_VERIFY_TOKEN`
6. Copiar `WHATSAPP_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID`

### 3. Configurar Chatwoot (Opcional)

1. Crear cuenta en [Chatwoot](https://www.chatwoot.com/)
2. Ir a Settings → Integrations → API
3. Crear API Access Token
4. Configurar inbox de WhatsApp
5. Copiar credenciales a `.env`

## 🚀 Ejecución

### Modo Desarrollo

```bash
cd src
python run_webhook.py
```

### Modo Producción

```bash
# Usando Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 "src.webhooks.whatsapp_webhook:app"

# Usando Docker (crear Dockerfile)
docker build -t iagente-vida-webhook .
docker run -p 5000:5000 --env-file .env iagente-vida-webhook
```

## 📱 Flujo de Conversación

### 1. **Mensaje Entrante**
```
WhatsApp → Webhook → Parser → iAgente_Vida → Respuesta → WhatsApp
                            ↓
                      Chatwoot (tracking)
```

### 2. **Estados de Conversación**
- `INICIO`: Primera interacción, saludo
- `NEEDS_ANALYSIS`: Recopilación de datos del cliente
- `COTIZACION`: Generación de presupuestos
- `PRESENTACION_PROPUESTA`: Presentación de opciones
- `FINALIZADO`: Conversación completada

### 3. **Persistencia**
- Estado mantenido por número de teléfono
- Historial completo en memoria
- Sincronización con Chatwoot para persistencia

## 🛠️ Endpoints Disponibles

### Webhook Principal
- `GET /webhook/whatsapp` - Verificación Meta
- `POST /webhook/whatsapp` - Recibir mensajes

### Administración
- `GET /webhook/status` - Estado del sistema
- `GET /webhook/conversations` - Lista conversaciones activas
- `DELETE /webhook/conversation/<phone>` - Reiniciar conversación

## 🧪 Testing

### 1. **Verificar Webhook**
```bash
curl "http://localhost:5000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=tu_token&hub.challenge=test123"
```

### 2. **Simular Mensaje**
```bash
curl -X POST http://localhost:5000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "id": "test123",
            "from": "34600000000",
            "type": "text",
            "timestamp": "1640995200",
            "text": {"body": "Hola, quiero información sobre seguros"}
          }],
          "contacts": [{
            "profile": {"name": "Cliente Prueba"}
          }]
        }
      }]
    }]
  }'
```

### 3. **Verificar Estado**
```bash
curl http://localhost:5000/webhook/status
curl http://localhost:5000/webhook/conversations
```

## 🔐 Seguridad

### 1. **Verificación de Webhooks**
- Token de verificación obligatorio
- Validación de origen Meta

### 2. **Datos Sensibles**
- Variables de entorno para credenciales
- No logging de tokens
- Manejo seguro de datos del cliente

### 3. **Rate Limiting** (Recomendado)
```bash
pip install flask-limiter
```

## 📊 Monitoring y Logs

### 1. **Logs del Sistema**
- Archivo: `webhook.log`
- Formato: timestamp + level + mensaje
- Rotación automática recomendada

### 2. **Métricas Importantes**
- Mensajes procesados/hora
- Tiempo de respuesta promedio
- Errores de webhook
- Conversaciones activas

### 3. **Chatwoot Analytics**
- Leads generados
- Conversiones
- Tiempo de respuesta
- Satisfacción del cliente

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. **Webhook no recibe mensajes**
```bash
# Verificar configuración
curl http://localhost:5000/webhook/status

# Verificar logs
tail -f webhook.log

# Verificar conectividad
ngrok http 5000  # Para desarrollo local
```

#### 2. **Error en envío de mensajes**
- Verificar `WHATSAPP_TOKEN`
- Comprobar que el número está verificado
- Revisar límites de API de Meta

#### 3. **Chatwoot no sincroniza**
- Verificar `CHATWOOT_USER_TOKEN`
- Comprobar `CHATWOOT_ACCOUNT_ID`
- Verificar permisos de API

#### 4. **Estado de conversación perdido**
- Implementar Redis para persistencia
- Usar base de datos para estado
- Backup periódico del `conversation_store`

## 🔄 Próximas Mejoras

### 1. **Persistencia Avanzada**
- [ ] Integración con Redis
- [ ] Base de datos PostgreSQL
- [ ] Backup automático de conversaciones

### 2. **Funcionalidades Adicionales**
- [ ] Mensajes programados
- [ ] Auto-respuestas fuera de horario
- [ ] Integración con calendario
- [ ] Análisis de sentimientos en tiempo real

### 3. **Escalabilidad**
- [ ] Queue system (Celery/Redis)
- [ ] Load balancing
- [ ] Microservicios
- [ ] Kubernetes deployment

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs en `webhook.log`
2. Verificar estado con `/webhook/status`
3. Comprobar configuración en `.env`
4. Revisar documentación de Meta WhatsApp API

---

✅ **Integración WhatsApp completada** - El sistema está listo para recibir y procesar mensajes de WhatsApp con seguimiento completo en Chatwoot.