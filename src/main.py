try:
    from .graph import graph
    from .models import EstadoBot, Cliente, EstadoConversacion
    from .agents.instructions_loader import _cache_instrucciones
except ImportError:
    from graph import graph
    from models import EstadoBot, Cliente, EstadoConversacion
    from agents.instructions_loader import _cache_instrucciones

# Limpio cache de instrucciones al iniciar
_cache_instrucciones.clear()

def conversacion_interactiva():
    """Conversación real donde el usuario escribe las respuestas"""
    
    print("🤖 ¡Hola! Soy iAgente_Vida, tu asistente para vender seguros de vida.")
    print("📝 Cuéntame sobre tu cliente y te ayudo a crear la propuesta perfecta. Escribe 'salir' para terminar\n")
    
    # Estado inicial
    cliente = Cliente(id_cliente="usuario_real")
    estado = EstadoBot(cliente=cliente)
    
    # PRIMERA EJECUCIÓN - Input del usuario
    mensaje_inicial = input("👤 Tú: ").strip()
    
    if mensaje_inicial.lower() in ['salir', 'exit', 'quit']:
        print("🤖 ¡Gracias por tu tiempo! Que tengas un excelente día.")
        return
    
    # Procesar primer mensaje
    estado.mensaje_usuario = mensaje_inicial
    resultado = graph.invoke(estado)
    estado = EstadoBot(**resultado)
    
    if estado.respuesta_bot:
        print(f"🤖 iAgente_Vida: {estado.respuesta_bot}\n")
    
    while True:
        # Obtener NUEVO input del usuario
        mensaje_usuario = input("👤 Tú: ").strip()
        
        if mensaje_usuario.lower() in ['salir', 'exit', 'quit']:
            print("🤖 ¡Gracias por tu tiempo! Que tengas un excelente día.")
            break
        
        if not mensaje_usuario:
            print("🤖 No escuché nada. ¿Podrías repetir?")
            continue
        
        # ACTUALIZAR con el NUEVO mensaje
        estado.mensaje_usuario = mensaje_usuario
        
        try:
            # Ejecutar el grafo UNA VEZ por mensaje
            resultado = graph.invoke(estado)
            estado = EstadoBot(**resultado)
            
            # Mostrar respuesta del bot
            if estado.respuesta_bot:
                print(f"🤖 iAgente_Vida: {estado.respuesta_bot}")
            
            # Mostrar progreso
            if estado.cliente.nombre:
                datos_completos = sum(1 for campo in [
                    estado.cliente.nombre, estado.cliente.edad, 
                    estado.cliente.num_dependientes, estado.cliente.ingresos_mensuales
                ] if campo is not None)
                print(f"📊 Progreso: {datos_completos}/4 datos principales")
            
            # Si hay cotizaciones, mostrarlas brevemente
            if estado.cotizaciones:
                print(f"💰 {len(estado.cotizaciones)} cotizaciones disponibles")
            
            print()  # Línea en blanco
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("🤖 Disculpa, hubo un problema técnico. ¿Podrías repetir?")
            print()

if __name__ == "__main__":
    conversacion_interactiva()