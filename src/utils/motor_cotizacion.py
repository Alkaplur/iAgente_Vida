"""
Motor de Cotización - Clase para calcular primas y recomendaciones
Utiliza los datos del archivo motor_cotizacion.txt
"""

import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
try:
    from ..models import Cliente, Cotizacion, RecomendacionProducto
except ImportError:
    from models import Cliente, Cotizacion, RecomendacionProducto


@dataclass
class TasaEdad:
    edad_min: int
    edad_max: int
    tasa_anual: float
    descripcion: str


@dataclass
class ParametrosCotizacion:
    tasas_edad: List[TasaEdad]
    multiplicadores_cobertura: Dict[str, float]
    ajustes_profesion: Dict[str, float]
    recomendaciones_cobertura: Dict[str, Tuple[int, str]]
    limites_cobertura: Dict[str, Tuple[float, float]]
    descuentos_especiales: Dict[str, float]
    recargos_riesgo: Dict[str, float]
    parametros: Dict[str, float]
    productos_por_perfil: Dict[str, Tuple[str, str]]


class MotorCotizacion:
    """Motor de cotización que lee configuración desde archivo TXT"""
    
    def __init__(self, archivo_config: str = None):
        if archivo_config is None:
            archivo_config = os.path.join(os.path.dirname(__file__), '..', 'data', 'motor_cotizacion.txt')
        
        self.archivo_config = archivo_config
        self.parametros = self._cargar_parametros()
        print(f"📊 Motor de cotización cargado: {len(self.parametros.tasas_edad)} tasas de edad")
    
    def _cargar_parametros(self) -> ParametrosCotizacion:
        """Carga parámetros desde el archivo de configuración"""
        
        if not os.path.exists(self.archivo_config):
            print(f"⚠️ No se encontró {self.archivo_config}, usando valores por defecto")
            return self._parametros_por_defecto()
        
        try:
            with open(self.archivo_config, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            return self._parsear_contenido(contenido)
            
        except Exception as e:
            print(f"⚠️ Error cargando motor de cotización: {e}")
            return self._parametros_por_defecto()
    
    def _parsear_contenido(self, contenido: str) -> ParametrosCotizacion:
        """Parsea el contenido del archivo de configuración"""
        
        lineas = [linea.strip() for linea in contenido.split('\n') 
                 if linea.strip() and not linea.startswith('#')]
        
        # Inicializar estructuras
        tasas_edad = []
        multiplicadores_cobertura = {}
        ajustes_profesion = {}
        recomendaciones_cobertura = {}
        limites_cobertura = {}
        descuentos_especiales = {}
        recargos_riesgo = {}
        parametros = {}
        productos_por_perfil = {}
        
        seccion_actual = None
        
        for linea in lineas:
            # Detectar secciones
            if linea in ['TASAS_EDAD', 'MULTIPLICADORES_COBERTURA', 'AJUSTES_PROFESION', 
                        'RECOMENDACIONES_COBERTURA', 'LIMITES_COBERTURA', 'DESCUENTOS_ESPECIALES',
                        'RECARGOS_RIESGO', 'PARAMETROS', 'PRODUCTOS_POR_PERFIL']:
                seccion_actual = linea
                continue
            
            # Procesar según sección
            if seccion_actual == 'TASAS_EDAD':
                partes = linea.split('|')
                if len(partes) >= 4:
                    tasas_edad.append(TasaEdad(
                        edad_min=int(partes[0]),
                        edad_max=int(partes[1]),
                        tasa_anual=float(partes[2]),
                        descripcion=partes[3]
                    ))
            
            elif seccion_actual == 'MULTIPLICADORES_COBERTURA':
                partes = linea.split('|')
                if len(partes) >= 2:
                    multiplicadores_cobertura[partes[0]] = float(partes[1])
            
            elif seccion_actual == 'AJUSTES_PROFESION':
                partes = linea.split('|')
                if len(partes) >= 2:
                    ajustes_profesion[partes[0]] = float(partes[1])
            
            elif seccion_actual == 'RECOMENDACIONES_COBERTURA':
                partes = linea.split('|')
                if len(partes) >= 3:
                    recomendaciones_cobertura[partes[0]] = (int(partes[1]), partes[2], partes[3] if len(partes) > 3 else "")
            
            elif seccion_actual == 'LIMITES_COBERTURA':
                partes = linea.split('|')
                if len(partes) >= 3:
                    limites_cobertura[partes[0]] = (float(partes[1]), float(partes[2]))
            
            elif seccion_actual == 'DESCUENTOS_ESPECIALES':
                partes = linea.split('|')
                if len(partes) >= 2:
                    descuentos_especiales[partes[0]] = float(partes[1])
            
            elif seccion_actual == 'RECARGOS_RIESGO':
                partes = linea.split('|')
                if len(partes) >= 2:
                    recargos_riesgo[partes[0]] = float(partes[1])
            
            elif seccion_actual == 'PARAMETROS':
                partes = linea.split('|')
                if len(partes) >= 2:
                    try:
                        parametros[partes[0]] = float(partes[1])
                    except ValueError:
                        parametros[partes[0]] = partes[1]  # String parameter
            
            elif seccion_actual == 'PRODUCTOS_POR_PERFIL':
                partes = linea.split('|')
                if len(partes) >= 3:
                    productos_por_perfil[partes[0]] = (partes[1], partes[2])
        
        return ParametrosCotizacion(
            tasas_edad=tasas_edad,
            multiplicadores_cobertura=multiplicadores_cobertura,
            ajustes_profesion=ajustes_profesion,
            recomendaciones_cobertura=recomendaciones_cobertura,
            limites_cobertura=limites_cobertura,
            descuentos_especiales=descuentos_especiales,
            recargos_riesgo=recargos_riesgo,
            parametros=parametros,
            productos_por_perfil=productos_por_perfil
        )
    
    def _parametros_por_defecto(self) -> ParametrosCotizacion:
        """Parámetros por defecto si no se puede cargar el archivo"""
        
        tasas_edad = [
            TasaEdad(18, 24, 0.0005, "Jóvenes - Riesgo muy bajo"),
            TasaEdad(25, 29, 0.0008, "Jóvenes adultos - Riesgo bajo"),
            TasaEdad(30, 34, 0.0012, "Adultos jóvenes - Riesgo bajo-medio"),
            TasaEdad(35, 39, 0.0018, "Adultos - Riesgo medio"),
            TasaEdad(40, 44, 0.0025, "Adultos maduros - Riesgo medio-alto"),
            TasaEdad(45, 49, 0.0035, "Maduros - Riesgo alto"),
            TasaEdad(50, 54, 0.0050, "Maduros avanzados - Riesgo alto"),
            TasaEdad(55, 99, 0.0075, "Senior - Riesgo muy alto")
        ]
        
        return ParametrosCotizacion(
            tasas_edad=tasas_edad,
            multiplicadores_cobertura={
                "fallecimiento": 1.0,
                "fallecimiento+invalidez": 1.4,
                "vida+ahorro": 1.8
            },
            ajustes_profesion={
                "ingeniero": 0.95,
                "medico": 0.95,
                "profesor": 0.95
            },
            recomendaciones_cobertura={
                "joven_sin_dependientes": (4, "vida_termino", "Protección temporal básica"),
                "joven_con_dependientes": (8, "vida_termino", "Protección temporal alta para familia"),
                "adulto_maduro": (5, "vida_ahorro", "Protección + inversión para jubilación")
            },
            limites_cobertura={},
            descuentos_especiales={},
            recargos_riesgo={},
            parametros={},
            productos_por_perfil={}
        )
    
    def obtener_tasa_por_edad(self, edad: int) -> float:
        """Obtiene la tasa actuarial para una edad específica"""
        
        for tasa in self.parametros.tasas_edad:
            if tasa.edad_min <= edad <= tasa.edad_max:
                return tasa.tasa_anual
        
        # Si no se encuentra, usar tasa por defecto
        return 0.0075  # Tasa alta por defecto
    
    def calcular_prima_base(self, edad: int, cobertura: float) -> float:
        """Calcula la prima base según edad y cobertura"""
        
        tasa = self.obtener_tasa_por_edad(edad)
        prima_anual = cobertura * tasa
        prima_mensual = prima_anual / 12
        
        return prima_mensual
    
    def aplicar_multiplicador_cobertura(self, prima_base: float, tipo_cobertura: str) -> float:
        """Aplica multiplicador según tipo de cobertura"""
        
        multiplicador = self.parametros.multiplicadores_cobertura.get(tipo_cobertura, 1.0)
        return prima_base * multiplicador
    
    def aplicar_ajuste_profesion(self, prima: float, profesion: str) -> float:
        """Aplica ajuste por profesión"""
        
        if not profesion:
            return prima
        
        # Buscar ajuste por profesión
        profesion_lower = profesion.lower()
        for prof_config, ajuste in self.parametros.ajustes_profesion.items():
            if prof_config.lower() in profesion_lower:
                return prima * ajuste
        
        return prima
    
    def determinar_perfil_cliente(self, cliente: Cliente) -> str:
        """Determina el perfil del cliente para recomendaciones de seguros de vida"""
        
        edad = cliente.edad or 30
        dependientes = cliente.num_dependientes or 0
        ingresos = cliente.ingresos_mensuales or 0
        profesion = cliente.profesion or ""
        
        # Perfiles específicos para seguros de vida
        if "empresario" in profesion.lower() or "emprendedor" in profesion.lower():
            return "empresario"
        elif "ejecutivo" in profesion.lower() or "director" in profesion.lower():
            return "ejecutivo_alto_patrimonio"
        elif edad < 30:
            if dependientes > 0:
                return "joven_pareja"
            else:
                return "joven_soltero"
        elif edad < 40:
            if dependientes > 0:
                return "familia_joven"
            else:
                return "profesional_establecido"
        elif edad < 55:
            if dependientes > 0:
                return "adulto_maduro_con_dependientes"
            else:
                return "adulto_maduro_sin_dependientes"
        else:
            return "planificacion_jubilacion"
    
    def recomendar_cobertura(self, cliente: Cliente) -> Tuple[int, str]:
        """Recomienda años de cobertura y tipo de producto de vida según perfil"""
        
        perfil = self.determinar_perfil_cliente(cliente)
        
        if perfil in self.parametros.recomendaciones_cobertura:
            anos, tipo_producto, _ = self.parametros.recomendaciones_cobertura[perfil]
            
            # Mapear tipo de producto a cobertura
            if tipo_producto == "vida_termino":
                cobertura = "fallecimiento"
            elif tipo_producto == "vida_completa":
                cobertura = "fallecimiento+valor_efectivo"
            elif tipo_producto == "vida_ahorro":
                cobertura = "fallecimiento+inversion"
            else:
                cobertura = "fallecimiento"
                
            return (anos, cobertura)
        
        # Valores por defecto para seguros de vida
        return (6, "fallecimiento+valor_efectivo")
    
    def calcular_cotizacion_completa(self, cliente: Cliente, tipo_cobertura: str, 
                                   cobertura_deseada: float = None) -> Cotizacion:
        """Calcula una cotización completa aplicando todas las reglas"""
        
        # 1. Determinar cobertura
        if cobertura_deseada is None:
            anos_recomendados, _ = self.recomendar_cobertura(cliente)
            ingresos_base = cliente.ingresos_mensuales or 2000
            cobertura_deseada = ingresos_base * 12 * anos_recomendados
        
        # 2. Calcular prima base
        prima_base = self.calcular_prima_base(cliente.edad or 30, cobertura_deseada)
        
        # 3. Aplicar multiplicador por cobertura
        prima_con_cobertura = self.aplicar_multiplicador_cobertura(prima_base, tipo_cobertura)
        
        # 4. Aplicar ajuste por profesión
        prima_con_profesion = self.aplicar_ajuste_profesion(prima_con_cobertura, cliente.profesion)
        
        # 5. Determinar vigencia
        vigencia = self._determinar_vigencia(cliente, tipo_cobertura)
        
        # 6. Determinar tipo de plan
        tipo_plan = self._determinar_tipo_plan(tipo_cobertura)
        
        # 7. Aseguradora
        aseguradora = self.parametros.parametros.get('aseguradora_principal', 'VidaSegura')
        
        return Cotizacion(
            prima_mensual=round(prima_con_profesion, 2),
            cobertura_fallecimiento=cobertura_deseada,
            tipo_plan=tipo_plan,
            vigencia_anos=vigencia,
            aseguradora=aseguradora
        )
    
    def _determinar_vigencia(self, cliente: Cliente, tipo_cobertura: str) -> int:
        """Determina la vigencia según el tipo de cobertura"""
        
        if tipo_cobertura == "fallecimiento":
            return 20
        elif tipo_cobertura == "fallecimiento+invalidez":
            return 25
        elif tipo_cobertura == "vida+ahorro":
            return 30
        else:
            return 25
    
    def _determinar_tipo_plan(self, tipo_cobertura: str) -> str:
        """Determina el nombre del plan según el tipo de cobertura de vida"""
        
        if tipo_cobertura == "fallecimiento":
            return "Vida Término - Solo Fallecimiento"
        elif tipo_cobertura == "fallecimiento+valor_efectivo":
            return "Vida Completa - Fallecimiento + Valor Efectivo"
        elif tipo_cobertura == "fallecimiento+inversion":
            return "Vida con Ahorro - Fallecimiento + Inversión"
        elif tipo_cobertura == "fallecimiento+ahorro_garantizado":
            return "Vida Universal - Fallecimiento + Ahorro Garantizado"
        else:
            return "Seguro de Vida Personalizado"
    
    def generar_cotizaciones_multiples(self, cliente: Cliente, 
                                     ajustar_precio: bool = False, 
                                     presupuesto_objetivo: float = None) -> List[Cotizacion]:
        """Genera múltiples cotizaciones basadas en la configuración"""
        
        cotizaciones = []
        
        # Obtener recomendación del perfil
        perfil = self.determinar_perfil_cliente(cliente)
        anos_recomendados, tipo_cobertura_recomendada = self.recomendar_cobertura(cliente)
        
        # Calcular cobertura base
        ingresos_base = cliente.ingresos_mensuales or 2000
        cobertura_base = ingresos_base * 12 * anos_recomendados
        
        # Ajustar si es necesario
        if ajustar_precio and presupuesto_objetivo:
            cobertura_maxima = self._calcular_cobertura_por_presupuesto(cliente.edad or 30, presupuesto_objetivo)
            cobertura_base = min(cobertura_base, cobertura_maxima)
        
        # 1. Cotización recomendada
        cotizacion_recomendada = self.calcular_cotizacion_completa(
            cliente, tipo_cobertura_recomendada, cobertura_base
        )
        cotizacion_recomendada.tipo_plan += " (Recomendado)"
        cotizaciones.append(cotizacion_recomendada)
        
        # 2. Opción económica
        if not ajustar_precio:
            cotizacion_economica = self.calcular_cotizacion_completa(
                cliente, "fallecimiento", cobertura_base * 0.6
            )
            cotizacion_economica.tipo_plan = "Opción Económica - Protección Esencial"
            cotizaciones.append(cotizacion_economica)
        
        # 3. Opción premium (si el cliente puede permitírselo)
        if cliente.ingresos_mensuales and cliente.ingresos_mensuales > 3000 and not ajustar_precio:
            cotizacion_premium = self.calcular_cotizacion_completa(
                cliente, "vida+ahorro", cobertura_base * 1.5
            )
            cotizacion_premium.tipo_plan = "Premium - Cobertura Total + Enfermedades Graves + Ahorro"
            cotizaciones.append(cotizacion_premium)
        
        return cotizaciones
    
    def _calcular_cobertura_por_presupuesto(self, edad: int, presupuesto_mensual: float) -> float:
        """Calcula la cobertura máxima posible dado un presupuesto mensual"""
        
        tasa = self.obtener_tasa_por_edad(edad)
        prima_anual_disponible = presupuesto_mensual * 12
        cobertura_maxima = prima_anual_disponible / tasa
        
        return cobertura_maxima
    
    def obtener_producto_recomendado(self, cliente: Cliente) -> Tuple[str, str]:
        """Obtiene el producto recomendado según el perfil del cliente"""
        
        perfil = self.determinar_perfil_cliente(cliente)
        
        if perfil in self.parametros.productos_por_perfil:
            return self.parametros.productos_por_perfil[perfil]
        
        # Producto por defecto
        return ("Protección Total", "Familia Segura")
    
    def recargar_configuracion(self):
        """Recarga la configuración desde el archivo"""
        
        print("🔄 Recargando configuración del motor de cotización...")
        self.parametros = self._cargar_parametros()
        print(f"✅ Configuración recargada: {len(self.parametros.tasas_edad)} tasas de edad")


# Instancia global del motor
motor_cotizacion = MotorCotizacion()


def obtener_motor_cotizacion() -> MotorCotizacion:
    """Obtiene la instancia del motor de cotización"""
    return motor_cotizacion