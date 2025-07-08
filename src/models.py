from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum

class EstadoConversacion(Enum):
    INICIO = "inicio"
    NEEDS_ANALYSIS = "needs_analysis" 
    COTIZACION = "cotizacion"
    PRESENTACION_PROPUESTA = "presentacion_propuesta"
    FINALIZADO = "finalizado"

class Cliente(BaseModel):
    # Identificación
    id_cliente: Optional[str] = None
    
    # Datos básicos
    nombre: Optional[str] = None
    edad: Optional[int] = None
    estado_civil: Optional[str] = None
    profesion: Optional[str] = None
    
    # Datos financieros
    ingresos_mensuales: Optional[float] = None
    nivel_ahorro: Optional[float] = None  # Capacidad de ahorro mensual
    compromisos_financieros: Optional[str] = None
    patrimonio: Optional[str] = None
    
    # Datos familiares
    num_dependientes: Optional[int] = None
    
    # Datos de seguros y percepción
    tiene_seguro_vida: Optional[bool] = None  # Si ya tiene seguro
    percepcion_seguro: Optional[str] = None  # Actitud hacia los seguros
    otros_seguros: Optional[str] = None
    capital_deseado: Optional[float] = None
    
    # Objetivos y preferencias
    objetivos_financieros: Optional[str] = None
    herencia_fiscal: Optional[str] = None
    
    # Salud
    salud_relevante: Optional[str] = None

class RecomendacionProducto(BaseModel):
    """Recomendación de producto del needs-based selling"""
    tipo_cobertura: str  # "básica", "completa", "premium"
    cobertura_principal: str  # "fallecimiento", "fallecimiento+invalidez", "vida+ahorro"
    monto_recomendado: float  # Monto de cobertura sugerido
    justificacion: str  # Por qué se recomienda este producto
    urgencia: str  # "alta", "media", "baja"
    productos_adicionales: Optional[List[str]] = None  # ["invalidez", "enfermedades_graves"]

class Cotizacion(BaseModel):
    prima_mensual: float
    cobertura_fallecimiento: float
    tipo_plan: str
    vigencia_anos: int
    aseguradora: str

class ContextoConversacional(BaseModel):
    """Nuevo: Contexto para seguimiento conversacional"""
    ultimo_campo_solicitado: Optional[str] = None
    ultima_pregunta: Optional[str] = None
    esperando_respuesta: bool = False
    intentos_pregunta_actual: int = 0
    tipo_respuesta_esperada: Optional[str] = None  # "numero", "texto", "si_no"
    confirmacion_pendiente: Optional[str] = None

class EstadoBot(BaseModel):
    # Estado actual
    etapa: EstadoConversacion = EstadoConversacion.INICIO
    mensaje_usuario: str = ""
    respuesta_bot: str = ""
    
    # Cliente
    cliente: Cliente
    
    # NUEVO: Contexto conversacional (Patrón LangGraph)
    contexto: ContextoConversacional = ContextoConversacional()
    
    # Recomendaciones del needs-based selling
    recomendacion_producto: Optional[RecomendacionProducto] = None
    
    # Cotizaciones generadas
    cotizaciones: List[Cotizacion] = []
    
    # Historial
    mensajes: List[Dict[str, str]] = []
    
    # Control del flujo
    agente_activo: Optional[str] = None
    completitud_datos: float = 0.0