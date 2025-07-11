"""
Cliente universal para LLMs - soporta OpenAI, Groq, Anthropic, etc.
"""
from typing import List, Dict, Optional
try:
    from ..config import settings
except ImportError:
    from config import settings
import os
from openai import OpenAI
from groq import Groq
from anthropic import Anthropic

class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower().strip()
        self.model = settings.llm_model
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Configura el cliente LLM según el proveedor seleccionado"""
        print(f"Configurando cliente LLM para proveedor: {self.provider}")
        
        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "groq":
            self.client = Groq(api_key=settings.groq_api_key)
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(
                f"Proveedor no soportado: {self.provider}\n"
                "Proveedores válidos: openai, groq, anthropic"
            )
    
    async def get_completion(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """Obtiene una respuesta del LLM usando las APIs correctas"""
        try:
            if self.provider == "openai":
                # Determinar si usar Chat Completions o Completions
                if self.model.startswith("gpt-"):
                    # Para modelos GPT usar Chat Completions API
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})
                    
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        stream=stream
                    )
                    
                    if stream:
                        # Para streaming
                        collected_chunks = []
                        for chunk in response:
                            if chunk.choices[0].delta.content is not None:
                                content = chunk.choices[0].delta.content
                                collected_chunks.append(content)
                                print(content, end="", flush=True)
                        return "".join(collected_chunks)
                    else:
                        # Para respuesta normal
                        return response.choices[0].message.content
                else:
                    # Para otros modelos usar Completions API
                    prompt_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                    
                    response = self.client.completions.create(
                        model=self.model,
                        prompt=prompt_text,
                        stream=stream,
                        max_tokens=1024,
                        temperature=0.7
                    )
                    
                    if stream:
                        # Para streaming
                        collected_chunks = []
                        for chunk in response:
                            if chunk.choices[0].text is not None:
                                content = chunk.choices[0].text
                                collected_chunks.append(content)
                                print(content, end="", flush=True)
                        return "".join(collected_chunks)
                    else:
                        # Para respuesta normal
                        return response.choices[0].text

            elif self.provider == "groq":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                if system_prompt:
                    # Para Anthropic, el system prompt va separado
                    response = self.client.messages.create(
                        model=self.model,
                        system=system_prompt,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1024
                    )
                else:
                    response = self.client.messages.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1024
                    )
                return response.content[0].text

        except Exception as e:
            print(f"Error detallado: {str(e)}")  # Debug
            raise Exception(f"Error al obtener respuesta del LLM: {str(e)}")

# Instancia global del cliente
llm = LLMClient()

# Función helper para obtener respuestas
def get_llm_response(prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
    """Función helper para obtener respuestas del LLM de forma síncrona"""
    import asyncio
    return asyncio.run(llm.get_completion(prompt, system_prompt, stream))

# Función helper para debug
def test_llm(stream: bool = False):
    """Prueba rápida del LLM configurado"""
    print(f"🧪 Probando {llm.provider} con modelo {llm.model}...")
    response = get_llm_response(
        "Responde solo con: 'Funcionando correctamente'",
        stream=stream
    )
    if not stream:
        print(f"✅ Respuesta: {response}")
    return response