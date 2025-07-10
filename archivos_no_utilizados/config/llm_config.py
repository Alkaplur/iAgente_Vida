from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os
from config import settings

class LLMProvider(Enum):
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

@dataclass
class LLMConfig:
    """Configuración para un LLM específico"""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> str:
        """Obtiene la API key según el proveedor"""
        key_map = {
            LLMProvider.OPENAI: settings.openai_api_key,
            LLMProvider.GROQ: settings.groq_api_key,
            LLMProvider.ANTHROPIC: settings.anthropic_api_key,
        }
        return key_map.get(self.provider, "")

class AgentLLMConfig:
    """Configuración de LLMs por agente"""
    
    def __init__(self):
        self.configs = {
            "supervisor": LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                temperature=0.3,  # Más determinista para routing
                max_tokens=1000
            ),
            "research": LLMConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-70b-versatile",
                temperature=0.5,
                max_tokens=2000
            ),
            "quote": LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                temperature=0.1,  # Muy determinista para cálculos
                max_tokens=1500
            ),
            "presenter": LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-3-sonnet-20240229",
                temperature=0.7,  # Más creativo para ventas
                max_tokens=2000
            )
        }
    
    def get_config(self, agent_name: str) -> LLMConfig:
        """Obtiene configuración para un agente específico"""
        return self.configs.get(agent_name, self.configs["supervisor"])
    
    def update_config(self, agent_name: str, config: LLMConfig):
        """Actualiza configuración de un agente"""
        self.configs[agent_name] = config
    
    def set_global_provider(self, provider: LLMProvider, model: str):
        """Cambia todos los agentes a un proveedor específico"""
        for agent_name in self.configs:
            self.configs[agent_name].provider = provider
            self.configs[agent_name].model = model
            self.configs[agent_name].api_key = self.configs[agent_name]._get_api_key()

# Instancia global configurable
llm_config = AgentLLMConfig()