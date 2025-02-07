from pydantic import BaseModel
import logging
from ai_suite.ie.llm.llm_factory import LLMFactory, SYSTEM_PROMPT_EXTRACT, SYSTEM_PROMPT_GENERAL
from typing import Type, Tuple, Dict

class ExtractionError(Exception):
    """Custom exception for extraction-related errors."""
    pass

logger = logging.getLogger(__name__)


def process_with_llm(content: str, response_model: Type[BaseModel], llm_client: LLMFactory, model: str) -> Tuple[BaseModel, Dict[str, int]]:
    validation_context = {"text_chunk": content}  

    messages = llm_client.get_messages(content, system_prompt=SYSTEM_PROMPT_GENERAL)
    completion, usage = llm_client.create_completion(
        response_model=response_model,
        messages=messages,  
        model=model,
        validation_context=validation_context
    )
    return completion, usage    

def extract_with_response_model(
    content: str,
    response_model: Type[BaseModel],
    llm_client: LLMFactory,
    model: str,
    system_prompt: str = SYSTEM_PROMPT_EXTRACT
) -> Tuple[BaseModel, Dict[str, int]]:
    """Extract structured information using an LLM and a response model."""
    try:
        # Create validation context inside the function
        validation_context = {"text_chunk": content}

        messages = llm_client.get_messages(content, system_prompt=system_prompt)
        
        result, usage = llm_client.create_completion(
            response_model=response_model,
            messages=messages,
            model=model,
            validation_context=validation_context
        )    
        return result, usage
        
    except Exception as e:
        raise ExtractionError(f"Failed to extract with {response_model.__name__}: {str(e)}")






