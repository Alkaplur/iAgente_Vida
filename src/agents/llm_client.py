"""
Cliente universal para LLMs - soporta OpenAI solamente
"""
from typing import List, Dict, Optional
try:
    from ..config import settings
except ImportError:
    from config import settings
import os
from openai import OpenAI

class LLMClient:
    def __init__(self):
        self.provider = "openai"  # Solo OpenAI
        self.model = settings.llm_model
        self.client = OpenAI(api_key=settings.openai_api_key)
        print(f"Configurando cliente LLM para OpenAI con modelo: {self.model}")
    
    async def get_completion(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """Obtiene una respuesta del LLM usando OpenAI API"""
        try:
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