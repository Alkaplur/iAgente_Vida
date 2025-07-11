from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from typing import Optional

# Cargar .env.local primero (si existe), luego .env
import os
if os.path.exists('.env.local'):
    load_dotenv('.env.local', override=True)
else:
    load_dotenv('.env', override=True)

# Para Streamlit Cloud, cargar desde st.secrets
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        # Cargar todas las secrets como variables de entorno
        for key, value in st.secrets.items():
            os.environ[key] = str(value)
        print(f"✅ Cargadas {len(st.secrets)} secrets desde Streamlit")
except ImportError:
    # Normal cuando no se ejecuta en Streamlit
    pass
except Exception as e:
    print(f"⚠️ Error cargando secrets: {e}")

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    
    # API Keys
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Bot Configuration
    bot_name: str = "iAgente_Vida"
    
    # WhatsApp Business API Configuration (Legacy - usar Woztell)
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    
    # Woztell Configuration
    woztell_business_token: Optional[str] = None
    woztell_webhook_url: Optional[str] = None
    woztell_webhook_secret: Optional[str] = None
    
    # Chatwoot Configuration
    chatwoot_base_url: Optional[str] = None
    chatwoot_account_id: Optional[str] = None
    chatwoot_user_token: Optional[str] = None
    chatwoot_platform_token: Optional[str] = None
    chatwoot_whatsapp_inbox_id: Optional[str] = None
    
    # Webhook Configuration
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 5000
    debug: bool = False
    
    # Optional LangChain Configuration
    langchain_tracing_v2: Optional[bool] = None
    langchain_endpoint: Optional[str] = None
    langchain_api_key: Optional[str] = None
    langchain_project: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding='utf-8',
        extra='ignore'  # Ignorar variables extra del .env
    )

# Crear una instancia de Settings
settings = Settings()