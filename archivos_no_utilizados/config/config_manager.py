from typing import Dict, Any, Optional
from llm_config import llm_config, LLMProvider, LLMConfig
from universal_llm_client import universal_llm
import json

class ConfigManager:
    """
    Gestor de configuración para cambiar fácilmente entre diferentes LLMs
    """
    
    def __init__(self):
        self.config_file = "llm_agent_config.json"
        self.load_config()
    
    def load_config(self):
        """Carga configuración desde archivo"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                self.apply_config(config_data)
        except FileNotFoundError:
            print("No se encontró archivo de configuración, usando valores por defecto")
            self.create_default_config()
    
    def create_default_config(self):
        """Crea configuración por defecto"""
        default_config = {
            "global_provider": "openai",
            "global_model": "gpt-4o-mini",
            "agent_specific": {
                "supervisor": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                "research_agent": {
                    "provider": "groq",
                    "model": "llama-3.1-70b-versatile",
                    "temperature": 0.5,
                    "max_tokens": 2000
                },
                "quote_agent": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 1500
                },
                "presenter_agent": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }
        self.save_config(default_config)
    
    def apply_config(self, config_data: Dict[str, Any]):
        """Aplica configuración a los agentes"""
        
        # Configuración específica por agente
        agent_configs = config_data.get("agent_specific", {})
        
        for agent_name, agent_config in agent_configs.items():
            provider = LLMProvider(agent_config["provider"])
            
            llm_config.update_config(
                agent_name,
                LLMConfig(
                    provider=provider,
                    model=agent_config["model"],
                    temperature=agent_config.get("temperature", 0.7),
                    max_tokens=agent_config.get("max_tokens", 2000)
                )
            )
    
    def save_config(self, config_data: Dict[str, Any]):
        """Guarda configuración en archivo"""
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def set_global_provider(self, provider: str, model: str):
        """Cambia todos los agentes a un proveedor específico"""
        
        provider_enum = LLMProvider(provider)
        llm_config.set_global_provider(provider_enum, model)
        
        # Actualizar archivo de configuración
        config_data = self.load_config_file()
        config_data["global_provider"] = provider
        config_data["global_model"] = model
        
        # Actualizar configuración específica
        for agent_name in config_data["agent_specific"]:
            config_data["agent_specific"][agent_name]["provider"] = provider
            config_data["agent_specific"][agent_name]["model"] = model
        
        self.save_config(config_data)
        print(f"✅ Todos los agentes cambiados a {provider} con modelo {model}")
    
    def set_agent_config(self, agent_name: str, provider: str, model: str, **kwargs):
        """Cambia configuración de un agente específico"""
        
        provider_enum = LLMProvider(provider)
        
        config = LLMConfig(
            provider=provider_enum,
            model=model,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000)
        )
        
        llm_config.update_config(agent_name, config)
        
        # Actualizar archivo
        config_data = self.load_config_file()
        if agent_name not in config_data["agent_specific"]:
            config_data["agent_specific"][agent_name] = {}
        
        config_data["agent_specific"][agent_name].update({
            "provider": provider,
            "model": model,
            **kwargs
        })
        
        self.save_config(config_data)
        print(f"✅ Agente {agent_name} configurado con {provider} - {model}")
    
    def load_config_file(self) -> Dict[str, Any]:
        """Carga datos del archivo de configuración"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.create_default_config()
            return self.load_config_file()
    
    def show_current_config(self):
        """Muestra configuración actual"""
        print("\n🔧 CONFIGURACIÓN ACTUAL DE LLMs:")
        print("=" * 50)
        
        for agent_name, config in llm_config.configs.items():
            print(f"🤖 {agent_name.upper()}:")
            print(f"   Provider: {config.provider.value}")
            print(f"   Model: {config.model}")
            print(f"   Temperature: {config.temperature}")
            print(f"   Max Tokens: {config.max_tokens}")
            print()
    
    def quick_setups(self):
        """Configuraciones rápidas predefinidas"""
        
        setups = {
            "openai_only": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "description": "Solo OpenAI GPT-4o-mini para todos los agentes"
            },
            "groq_only": {
                "provider": "groq",
                "model": "llama-3.1-70b-versatile",
                "description": "Solo Groq Llama para todos los agentes"
            },
            "anthropic_only": {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "description": "Solo Anthropic Claude para todos los agentes"
            },
            "mixed_optimal": {
                "description": "Configuración mixta optimizada",
                "config": {
                    "supervisor": ("openai", "gpt-4o-mini"),
                    "research_agent": ("groq", "llama-3.1-70b-versatile"),
                    "quote_agent": ("openai", "gpt-4o-mini"),
                    "presenter_agent": ("anthropic", "claude-3-sonnet-20240229")
                }
            }
        }
        
        return setups
    
    def apply_quick_setup(self, setup_name: str):
        """Aplica una configuración rápida"""
        
        setups = self.quick_setups()
        
        if setup_name not in setups:
            print(f"❌ Setup '{setup_name}' no encontrado")
            return
        
        setup = setups[setup_name]
        
        if "provider" in setup:
            # Setup global
            self.set_global_provider(setup["provider"], setup["model"])
        
        elif "config" in setup:
            # Setup mixto
            for agent_name, (provider, model) in setup["config"].items():
                self.set_agent_config(agent_name, provider, model)
        
        print(f"✅ Configuración '{setup_name}' aplicada")
        print(f"📝 {setup['description']}")

# Instancia global
config_manager = ConfigManager()

# Función de ayuda para uso rápido
def quick_config():
    """Función de ayuda para configuración rápida"""
    
    print("\n🚀 CONFIGURACIÓN RÁPIDA DE LLMs")
    print("=" * 40)
    
    setups = config_manager.quick_setups()
    
    for i, (setup_name, setup_data) in enumerate(setups.items(), 1):
        print(f"{i}. {setup_name}")
        print(f"   {setup_data['description']}")
        print()
    
    print("Comandos disponibles:")
    print("- config_manager.apply_quick_setup('openai_only')")
    print("- config_manager.set_global_provider('openai', 'gpt-4o-mini')")
    print("- config_manager.set_agent_config('supervisor', 'anthropic', 'claude-3-sonnet-20240229')")
    print("- config_manager.show_current_config()")

if __name__ == "__main__":
    quick_config()