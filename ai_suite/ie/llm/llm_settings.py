from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()

class JinaSettings(BaseSettings):
    api_key: str = os.getenv("JINA_API_KEY")

class LLMProviderSettings(BaseSettings):
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    max_retries: int = 2


class OpenAISettings(LLMProviderSettings):
    api_key: str = os.getenv("OPENAI_API_KEY")
    default_model: str = "gpt-4o"
    available_models: List[str] = ["gpt-4o", "gpt-4o-mini"]

# class AnthropicSettings(LLMProviderSettings):
#     api_key: str = os.getenv("ANTHROPIC_API_KEY")
#     default_model: str = "claude-3-5-sonnet-20240620"
#     max_tokens: int = 4024
#     available_models: List[str] = ["claude-3-5-sonnet-20240620"]

class LlamaSettings(LLMProviderSettings):
    api_key: str = "key"  # required, but not used
    default_model: str = "llama3"
    base_url: str = "http://localhost:11434/v1"
    available_models: List[str] = ["llama3"]

class GoogleSettings(LLMProviderSettings):
    default_model: str = "models/gemini-1.5-flash-latest"
    temperature: float = 0.0
    max_retries: int = 2
    available_models: List[str] = [
        "models/gemini-1.5-pro-latest",
        "models/gemini-1.5-flash-latest"
    ]


class Settings(BaseSettings):
    app_name: str = "GenAI Project Template"
    openai: OpenAISettings = OpenAISettings()
    #anthropic: AnthropicSettings = AnthropicSettings()
    llama: LlamaSettings = LlamaSettings()
    google: GoogleSettings = GoogleSettings()
    
@lru_cache
def get_settings():
    return Settings()
