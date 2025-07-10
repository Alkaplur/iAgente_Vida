from typing import Dict, Any, Optional, List
from llm_config import LLMConfig, LLMProvider
import asyncio
from dataclasses import asdict

class UniversalLLMClient:
    """Cliente universal para múltiples proveedores LLM"""
    
    def __init__(self):
        self._clients = {}
    
    def _get_client(self, config: LLMConfig):
        """Obtiene cliente específico según el proveedor"""
        provider = config.provider
        
        if provider not in self._clients:
            if provider == LLMProvider.OPENAI:
                from openai import OpenAI
                self._clients[provider] = OpenAI(api_key=config.api_key)
            
            elif provider == LLMProvider.GROQ:
                from groq import Groq
                self._clients[provider] = Groq(api_key=config.api_key)
            
            elif provider == LLMProvider.ANTHROPIC:
                import anthropic
                self._clients[provider] = anthropic.Anthropic(api_key=config.api_key)
            
            else:
                raise ValueError(f"Proveedor {provider} no soportado")
        
        return self._clients[provider]
    
    def generate_response(
        self,
        config: LLMConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> str:
        """Genera respuesta usando el proveedor configurado"""
        
        client = self._get_client(config)
        
        # Preparar mensajes
        formatted_messages = self._format_messages(messages, system_prompt, config.provider)
        
        try:
            if config.provider == LLMProvider.OPENAI:
                response = client.chat.completions.create(
                    model=config.model,
                    messages=formatted_messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    tools=tools
                )
                return response.choices[0].message.content
            
            elif config.provider == LLMProvider.GROQ:
                response = client.chat.completions.create(
                    model=config.model,
                    messages=formatted_messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
                return response.choices[0].message.content
            
            elif config.provider == LLMProvider.ANTHROPIC:
                # Anthropic tiene formato diferente
                system_msg = None
                user_messages = []
                
                for msg in formatted_messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        user_messages.append(msg)
                
                response = client.messages.create(
                    model=config.model,
                    system=system_msg,
                    messages=user_messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens or 1000
                )
                return response.content[0].text
            
        except Exception as e:
            print(f"Error con {config.provider}: {e}")
            raise
    
    def _format_messages(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str],
        provider: LLMProvider
    ) -> List[Dict[str, str]]:
        """Formatea mensajes según el proveedor"""
        
        formatted = []
        
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        
        formatted.extend(messages)
        return formatted
    
    async def generate_response_async(
        self,
        config: LLMConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> str:
        """Versión asíncrona para llamadas paralelas"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_response,
            config,
            messages,
            system_prompt,
            tools
        )

# Instancia global
universal_llm = UniversalLLMClient()