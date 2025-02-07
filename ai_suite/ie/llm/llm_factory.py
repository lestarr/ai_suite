from typing import Any, Dict, List, Type, Tuple
import instructor
from anthropic import Anthropic
import google.generativeai as genai
import sys
sys.path.append("..")
from ai_suite.ie.llm.llm_settings import get_settings
from openai import OpenAI
from pydantic import BaseModel, Field
import os

SYSTEM_PROMPT_GENERAL = """
    You are a helpful information processing AI assistant. Do the task defined in the response model.
"""

SYSTEM_PROMPT_EXTRACT = """
    # Role and Purpose
    You are an AI assistant for information extraction and text classification. Your task is to extract information from the given website text. 

    # Guidelines:
    1. Extract informations defined in the Response Model.
    2. Use only the information from the given website text.
    3. Some information might be missing or irrelevant, do NOT extract fields where information is missing
    4. Be transparent when there is insufficient information to be extracted.
    5. Do not make up or infer information not present in the provided website text. Return None for empty string and [] for empty array or list.
    6.THE CITATION STRINGS SHOULD BE PRESENT EXACTLY AS THEY ARE IN THE CONTEXT DOCUMENT. NO PARAPHRASING ALLOWED.
    
    Review the website text: 
    """

class LLMFactory:
    def __init__(self, provider: str):
        self.provider = provider
        settings = get_settings()
        self.settings = getattr(settings, provider, None)
        
        if not self.settings:
            raise ValueError(f"Settings for provider '{provider}' not found")
        
        if provider == "google":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
        
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        client_initializers = {
            "openai": lambda s: instructor.from_openai(OpenAI(api_key=s.api_key)) if s and s.api_key else None,
            #"anthropic": lambda s: instructor.from_anthropic(Anthropic(api_key=s.api_key)) if s and s.api_key else None,
            "google": lambda s: instructor.from_gemini(
                client=genai.GenerativeModel(model_name=s.default_model),
                mode=instructor.Mode.GEMINI_JSON
            ) if s else None
        }

        initializer = client_initializers.get(self.provider)
        if not initializer:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        client = initializer(self.settings)
        if not client:
            raise ValueError(f"Failed to initialize client for {self.provider}. API key may be missing.")

        return client

    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Tuple[BaseModel, Dict[str, int]]:
        usage = None
        completion_params = {
            "model": kwargs.get("model", self.settings.default_model),
            "temperature": kwargs.get("temperature", self.settings.temperature),
            "max_retries": kwargs.get("max_retries", self.settings.max_retries),
            "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
            "response_model": response_model,
            "validation_context": kwargs.get("validation_context", None),
            "messages": messages,
        }
        
        if self.provider == "openai":
            completion_params["seed"] = kwargs.get("seed", 2)
            response, usage = self.client.chat.completions.create_with_completion(**completion_params)
        elif self.provider == "anthropic":
            response = self.client.messages.create(**completion_params)
            if hasattr(response, 'usage'):
                usage = {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                }
        elif self.provider == "google":
            response = self.client.chat.completions.create(
                messages=messages,
                response_model=response_model,
            )
        
        return response, usage

    def get_messages(self, data, system_prompt: str = SYSTEM_PROMPT_GENERAL):
        system_prompt = {"role": "system", "content": system_prompt}
        messages = [system_prompt]
        messages.append({"role": "user", "content": data})
        return messages

if __name__ == "__main__":
    class CompletionModel(BaseModel):
        reasoning: str = Field(description="Explain your reasoning for the response.")
        response: str = Field(description="Your response to the user.")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "If it takes 2 hours to dry 1 shirt out in the sun, how long will it take to dry 5 shirts?",
        },
    ]

    #llm = LLMFactory("openai")
    #llm = LLMFactory("anthropic")
    llm = LLMFactory("google")
    completion, usage = llm.create_completion(
        response_model=CompletionModel,
        messages=messages,
    )

    print(f"Completion: {completion}")
    if hasattr(completion, 'response'):
        print(f"Response: {completion.response}\n")
        print(f"Reasoning: {completion.reasoning}")
    if usage:  # Only print usage for OpenAI and Anthropic
        print("\nUsage Statistics:")
        print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
        print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
        print(f"Total tokens: {usage.get('total_tokens', 'N/A')}")
