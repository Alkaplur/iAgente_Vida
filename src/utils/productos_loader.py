"""
Loader de Productos de Seguros
Utiliza el archivo productos_seguros.txt para cargar información de productos
"""

import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ProductoSeguro:
    tipo: str
    nombre_comercial: str
    cobertura_principal: str
    caracteristicas: str
    coberturas_adicionales: List[str]
    publico_objetivo: str
    argumentos_venta: str


class ProductosLoader:
    """Cargador de productos de seguros desde archivo TXT"""
    
    def __init__(self, archivo_productos: str = None):
        if archivo_productos is None:
            archivo_productos = os.path.join(os.path.dirname(__file__), '..', 'data', 'productos_seguros.txt')
        
        self.archivo_productos = archivo_productos
        self.productos = self._cargar_productos()
        print(f"📋 Productos cargados: {len(self.productos)} productos disponibles")
    
    def _cargar_productos(self) -> List[ProductoSeguro]:
        """Carga productos desde el archivo de configuración"""
        
        if not os.path.exists(self.archivo_productos):
            print(f"⚠️ No se encontró {self.archivo_productos}")
            return []
        
        try:
            with open(self.archivo_productos, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            return self._parsear_productos(contenido)
            
        except Exception as e:
            print(f"⚠️ Error cargando productos: {e}")
            return []
    
    def _parsear_productos(self, contenido: str) -> List[ProductoSeguro]:
        """Parsea el contenido del archivo de productos"""
        
        lineas = [linea.strip() for linea in contenido.split('\n') 
                 if linea.strip() and not linea.startswith('#')]
        
        productos = []
        
        for linea in lineas:
            partes = linea.split('|')
            if len(partes) >= 6:
                # Procesar coberturas adicionales
                coberturas_adicionales = []
                if len(partes) > 4 and partes[4].strip() != "ninguna":
                    coberturas_adicionales = [cob.strip() for cob in partes[4].split(',')]
                
                producto = ProductoSeguro(
                    tipo=partes[0].strip(),
                    nombre_comercial=partes[1].strip(),
                    cobertura_principal=partes[2].strip(),
                    caracteristicas=partes[3].strip(),
                    coberturas_adicionales=coberturas_adicionales,
                    publico_objetivo=partes[5].strip() if len(partes) > 5 else "",
                    argumentos_venta=partes[6].strip() if len(partes) > 6 else ""
                )
                productos.append(producto)
        
        return productos
    
    def obtener_productos_por_tipo(self, tipo: str) -> List[ProductoSeguro]:
        """Obtiene productos de un tipo específico"""
        return [p for p in self.productos if p.tipo.upper() == tipo.upper()]
    
    def obtener_productos_por_cobertura(self, cobertura: str) -> List[ProductoSeguro]:
        """Obtiene productos que incluyen una cobertura específica"""
        return [p for p in self.productos if cobertura.lower() in p.cobertura_principal.lower()]
    
    def obtener_productos_por_publico(self, publico_keywords: List[str]) -> List[ProductoSeguro]:
        """Obtiene productos adecuados para un público específico"""
        productos_recomendados = []
        
        for producto in self.productos:
            publico_lower = producto.publico_objetivo.lower()
            if any(keyword.lower() in publico_lower for keyword in publico_keywords):
                productos_recomendados.append(producto)
        
        return productos_recomendados
    
    def recomendar_producto(self, edad: int, num_dependientes: int, 
                          ingresos_mensuales: float = None, 
                          profesion: str = None) -> Optional[ProductoSeguro]:
        """Recomienda un producto de vida basado en el perfil del cliente"""
        
        keywords = []
        
        # Determinar keywords según perfil para seguros de vida
        if edad < 30:
            keywords.extend(["jóvenes", "25-55", "familias jóvenes"])
        elif edad < 50:
            keywords.extend(["profesionales", "establecidas", "planificación"])
        else:
            keywords.extend(["+40", "jubilación", "patrimonio"])
        
        if num_dependientes > 0:
            keywords.extend(["familia", "dependientes", "hijos", "educación"])
        else:
            keywords.extend(["soltero", "individual", "sin dependientes"])
        
        if ingresos_mensuales:
            if ingresos_mensuales > 4000:
                keywords.extend(["altos ingresos", "patrimonio", "ejecutivos", "empresarios"])
            elif ingresos_mensuales < 2000:
                keywords.extend(["temporales", "variables", "modestos"])
        
        if profesion:
            profesion_lower = profesion.lower()
            if any(prof in profesion_lower for prof in ["empresario", "emprendedor"]):
                keywords.extend(["empresarios", "socios", "empresa"])
            elif any(prof in profesion_lower for prof in ["ejecutivo", "director", "gerente"]):
                keywords.extend(["ejecutivos", "directivos", "patrimonio alto"])
            elif any(prof in profesion_lower for prof in ["ingeniero", "médico", "abogado"]):
                keywords.extend(["profesionales", "liberales"])
        
        # Buscar productos recomendados por tipo prioritario
        productos_candidatos = self.obtener_productos_por_publico(keywords)
        
        if productos_candidatos:
            # Priorizar por tipo de producto de vida
            for tipo_prioritario in ["VIDA_AHORRO", "VIDA_COMPLETA", "VIDA_TERMINO"]:
                productos_tipo = [p for p in productos_candidatos if p.tipo == tipo_prioritario]
                if productos_tipo:
                    return productos_tipo[0]
            
            return productos_candidatos[0]
        
        # Producto por defecto según edad y dependientes
        if edad < 35 and num_dependientes == 0:
            productos_termino = self.obtener_productos_por_tipo("VIDA_TERMINO")
            return productos_termino[0] if productos_termino else None
        elif num_dependientes > 0:
            productos_completa = self.obtener_productos_por_tipo("VIDA_COMPLETA")
            return productos_completa[0] if productos_completa else None
        else:
            productos_ahorro = self.obtener_productos_por_tipo("VIDA_AHORRO")
            return productos_ahorro[0] if productos_ahorro else None
    
    def obtener_producto_por_nombre(self, nombre: str) -> Optional[ProductoSeguro]:
        """Obtiene un producto específico por nombre"""
        for producto in self.productos:
            if producto.nombre_comercial.lower() == nombre.lower():
                return producto
        return None
    
    def obtener_argumentos_venta(self, producto: ProductoSeguro, 
                               cliente_nombre: str = None) -> str:
        """Obtiene argumentos de venta personalizados para un producto"""
        
        argumentos = producto.argumentos_venta
        
        # Personalizar con nombre del cliente
        if cliente_nombre:
            argumentos = argumentos.replace("tu", f"para {cliente_nombre}")
            argumentos = argumentos.replace("Tu", f"Para {cliente_nombre}")
        
        return argumentos
    
    def obtener_productos_similares(self, producto: ProductoSeguro) -> List[ProductoSeguro]:
        """Obtiene productos similares al dado"""
        
        productos_similares = []
        
        # Buscar productos del mismo tipo
        productos_mismo_tipo = self.obtener_productos_por_tipo(producto.tipo)
        productos_similares.extend([p for p in productos_mismo_tipo if p != producto])
        
        # Buscar productos con cobertura similar
        productos_cobertura_similar = self.obtener_productos_por_cobertura(producto.cobertura_principal)
        productos_similares.extend([p for p in productos_cobertura_similar if p != producto and p not in productos_similares])
        
        return productos_similares[:3]  # Máximo 3 productos similares
    
    def obtener_resumen_producto(self, producto: ProductoSeguro) -> str:
        """Obtiene un resumen del producto para presentación"""
        
        resumen = f"**{producto.nombre_comercial}** ({producto.tipo})\n"
        resumen += f"🎯 **Cobertura:** {producto.cobertura_principal}\n"
        resumen += f"📋 **Características:** {producto.caracteristicas}\n"
        
        if producto.coberturas_adicionales:
            resumen += f"➕ **Adicionales:** {', '.join(producto.coberturas_adicionales)}\n"
        
        resumen += f"👥 **Ideal para:** {producto.publico_objetivo}\n"
        resumen += f"💡 **Ventaja:** {producto.argumentos_venta}"
        
        return resumen
    
    def filtrar_productos_por_presupuesto(self, presupuesto_maximo: float) -> List[ProductoSeguro]:
        """Filtra productos de vida adecuados para un presupuesto específico"""
        
        # Productos económicos para presupuesto bajo (vida término)
        if presupuesto_maximo < 100:
            return self.obtener_productos_por_tipo("VIDA_TERMINO")
        
        # Productos estándar para presupuesto medio (vida completa)
        elif presupuesto_maximo < 300:
            return self.obtener_productos_por_tipo("VIDA_COMPLETA") + self.obtener_productos_por_tipo("VIDA_TERMINO")
        
        # Todos los productos para presupuesto alto (incluyendo vida con ahorro)
        else:
            return self.productos
    
    def obtener_estadisticas_productos(self) -> Dict[str, int]:
        """Obtiene estadísticas de los productos cargados"""
        
        stats = {}
        for producto in self.productos:
            stats[producto.tipo] = stats.get(producto.tipo, 0) + 1
        
        return stats
    
    def recargar_productos(self):
        """Recarga los productos desde el archivo"""
        
        print("🔄 Recargando productos de seguros...")
        self.productos = self._cargar_productos()
        print(f"✅ Productos recargados: {len(self.productos)} productos disponibles")


# Instancia global del loader
productos_loader = ProductosLoader()


def obtener_productos_loader() -> ProductosLoader:
    """Obtiene la instancia del loader de productos"""
    return productos_loader