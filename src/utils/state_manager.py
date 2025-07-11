"""
Gestor de estado para usuarios de WhatsApp
"""

import os
import json
import pickle
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class StateManager:
    """
    Gestor de estado para conversaciones de WhatsApp
    Mantiene el estado de cada usuario entre mensajes
    """
    
    def __init__(self, storage_path: str = None):
        """
        Inicializa el gestor de estado
        
        Args:
            storage_path: Ruta donde guardar los estados (opcional)
        """
        self.storage_path = storage_path or os.path.join(os.getcwd(), "user_states")
        self.states_cache = {}
        self.last_cleanup = datetime.now()
        
        # Crear directorio si no existe
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StateManager inicializado con storage_path: {self.storage_path}")
    
    def get_user_state(self, user_id: str) -> Optional[Any]:
        """
        Obtiene el estado de un usuario
        
        Args:
            user_id: ID del usuario (número de teléfono)
            
        Returns:
            Estado del usuario o None si no existe
        """
        try:
            # Limpiar cache periódicamente
            self._cleanup_old_states()
            
            # Intentar obtener desde cache
            if user_id in self.states_cache:
                state_data = self.states_cache[user_id]
                
                # Verificar si no ha expirado
                if self._is_state_valid(state_data):
                    return state_data["state"]
                else:
                    # Remover estado expirado
                    del self.states_cache[user_id]
                    self._delete_state_file(user_id)
            
            # Intentar cargar desde archivo
            state_file = self._get_state_file_path(user_id)
            if os.path.exists(state_file):
                with open(state_file, 'rb') as f:
                    state_data = pickle.load(f)
                
                if self._is_state_valid(state_data):
                    # Cargar en cache
                    self.states_cache[user_id] = state_data
                    return state_data["state"]
                else:
                    # Remover archivo expirado
                    os.remove(state_file)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del usuario {user_id}: {str(e)}")
            return None
    
    def save_user_state(self, user_id: str, state: Any) -> bool:
        """
        Guarda el estado de un usuario
        
        Args:
            user_id: ID del usuario
            state: Estado a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            state_data = {
                "state": state,
                "timestamp": datetime.now(),
                "user_id": user_id
            }
            
            # Guardar en cache
            self.states_cache[user_id] = state_data
            
            # Guardar en archivo
            state_file = self._get_state_file_path(user_id)
            with open(state_file, 'wb') as f:
                pickle.dump(state_data, f)
            
            logger.debug(f"Estado guardado para usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando estado del usuario {user_id}: {str(e)}")
            return False
    
    def delete_user_state(self, user_id: str) -> bool:
        """
        Elimina el estado de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            # Remover del cache
            if user_id in self.states_cache:
                del self.states_cache[user_id]
            
            # Remover archivo
            self._delete_state_file(user_id)
            
            logger.info(f"Estado eliminado para usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando estado del usuario {user_id}: {str(e)}")
            return False
    
    def get_active_users_count(self) -> int:
        """
        Obtiene el número de usuarios activos
        
        Returns:
            Número de usuarios con estado válido
        """
        try:
            active_count = 0
            
            # Contar estados en cache
            for user_id, state_data in self.states_cache.items():
                if self._is_state_valid(state_data):
                    active_count += 1
            
            # Contar archivos válidos no en cache
            for state_file in Path(self.storage_path).glob("*.pkl"):
                user_id = state_file.stem
                if user_id not in self.states_cache:
                    try:
                        with open(state_file, 'rb') as f:
                            state_data = pickle.load(f)
                        if self._is_state_valid(state_data):
                            active_count += 1
                    except:
                        pass
            
            return active_count
            
        except Exception as e:
            logger.error(f"Error obteniendo conteo de usuarios activos: {str(e)}")
            return 0
    
    def cleanup_expired_states(self) -> int:
        """
        Limpia estados expirados
        
        Returns:
            Número de estados eliminados
        """
        try:
            cleaned_count = 0
            
            # Limpiar cache
            expired_users = []
            for user_id, state_data in self.states_cache.items():
                if not self._is_state_valid(state_data):
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self.states_cache[user_id]
                cleaned_count += 1
            
            # Limpiar archivos
            for state_file in Path(self.storage_path).glob("*.pkl"):
                try:
                    with open(state_file, 'rb') as f:
                        state_data = pickle.load(f)
                    
                    if not self._is_state_valid(state_data):
                        os.remove(state_file)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error procesando archivo {state_file}: {str(e)}")
                    # Remover archivo corrupto
                    try:
                        os.remove(state_file)
                        cleaned_count += 1
                    except:
                        pass
            
            logger.info(f"Limpieza completada: {cleaned_count} estados eliminados")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error en limpieza de estados: {str(e)}")
            return 0
    
    def _get_state_file_path(self, user_id: str) -> str:
        """
        Obtiene la ruta del archivo de estado para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Ruta del archivo
        """
        # Limpiar user_id para nombre de archivo seguro
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in "_-")
        return os.path.join(self.storage_path, f"{safe_user_id}.pkl")
    
    def _delete_state_file(self, user_id: str):
        """
        Elimina el archivo de estado de un usuario
        
        Args:
            user_id: ID del usuario
        """
        try:
            state_file = self._get_state_file_path(user_id)
            if os.path.exists(state_file):
                os.remove(state_file)
        except Exception as e:
            logger.warning(f"Error eliminando archivo de estado para {user_id}: {str(e)}")
    
    def _is_state_valid(self, state_data: Dict[str, Any]) -> bool:
        """
        Verifica si un estado es válido (no expirado)
        
        Args:
            state_data: Datos del estado
            
        Returns:
            True si es válido
        """
        try:
            timestamp = state_data.get("timestamp")
            if not timestamp:
                return False
            
            # Estados válidos por 24 horas
            expiry_time = timestamp + timedelta(hours=24)
            return datetime.now() < expiry_time
            
        except Exception:
            return False
    
    def _cleanup_old_states(self):
        """
        Limpieza periódica de estados antiguos
        """
        try:
            # Limpiar cada hora
            if datetime.now() - self.last_cleanup > timedelta(hours=1):
                self.cleanup_expired_states()
                self.last_cleanup = datetime.now()
        except Exception as e:
            logger.warning(f"Error en limpieza periódica: {str(e)}")

# Instancia global del gestor de estado
state_manager = StateManager()