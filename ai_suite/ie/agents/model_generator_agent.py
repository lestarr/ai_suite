from typing import Type, Union, Optional
from pydantic import BaseModel, Field, create_model
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel
from ai_suite.ie.models.models import DocTypeModel

class ModelResponse(BaseModel):
    """Validation model for LLM responses"""
    model_type: str = Field(..., description="Type of model: 'doc_type' or 'extraction'")
    fields: dict = Field(..., description="Dictionary of field definitions")
    model_name: str = Field(..., description="Name for the generated model")
    description: str = Field(..., description="Description of what the model represents")

class ModelGeneratorAgent(BaseAgent):
    """Agent for generating Pydantic models using LLM"""
    
    DOC_TYPE_PROMPT = """
    Create a document type model for validating content.
    Example DocTypeModel has these fields:
    - doc_type: str (required) - Type of document being processed
    - confidence: float (optional) - Confidence score of classification
    
    Based on this description: {description}
    Return a JSON with:
    {
        "model_type": "doc_type",
        "model_name": "name of model",
        "description": "what this model validates",
        "fields": {
            "field_name": ["type", "required/optional", "description"]
        }
    }
    """

    EXTRACTION_PROMPT = """
    Create an information extraction model for this content: {description}
    
    Extract these features: {features}
    
    Return a JSON with:
    {
        "model_type": "extraction",
        "model_name": "name of model",
        "description": "what this model extracts",
        "fields": {
            "field_name": ["type", "required/optional", "description"]
        }
    }
    Keep fields focused on essential information.
    """

    def __init__(self, llm_client, model_name: str):
        super().__init__(llm_client, model_name)

    def _convert_llm_fields_to_pydantic(self, fields_dict: dict) -> dict:
        """Convert LLM field definitions to Pydantic field tuples"""
        pydantic_fields = {}
        for field_name, specs in fields_dict.items():
            field_type = eval(specs[0])  # Convert "str" to str, etc.
            is_required = specs[1].lower() == "required"
            description = specs[2]
            
            pydantic_fields[field_name] = (
                field_type,
                Field(
                    ... if is_required else None,
                    description=description
                )
            )
        return pydantic_fields

    def _create_model(self, response: ModelResponse) -> Type[BaseModel]:
        """Create Pydantic model from validated response"""
        fields = self._convert_llm_fields_to_pydantic(response.fields)
        return create_model(
            response.model_name,
            **fields
        )

    async def process(self, info: InfoModel) -> Union[Type[BaseModel], DocTypeModel]:
        """
        Generate appropriate model based on input description
        
        Args:
            info: InfoModel containing either:
                - description and features list for extraction model
                - description for doc type model
        Returns:
            Generated Pydantic model
        """
        description = info.texts[0].content
        features = info.texts[0].metadata.get("features", [])
        
        # Choose prompt based on whether features are provided
        prompt = (
            self.EXTRACTION_PROMPT.format(description=description, features=features)
            if features
            else self.DOC_TYPE_PROMPT.format(description=description)
        )

        # Get model definition from LLM
        response_json, usage = await self.llm_client.generate(
            prompt,
            response_model=ModelResponse
        )
        self.track_usage(usage)
        
        if not response_json:
            self.add_error("ModelGeneratorAgent", "Failed to generate model definition")
            return None

        # Create and return appropriate model type
        model = self._create_model(response_json)
        
        if response_json.model_type == "doc_type":
            return DocTypeModel(
                name=response_json.model_name,
                description=response_json.description,
                model=model
            )
        return model

if __name__ == "__main__":
    import asyncio
    from ai_suite.ie.llm.llm_factory import LLMFactory
    
    async def test():
        llm = LLMFactory("openai")
        agent = ModelGeneratorAgent(llm, "gpt-4o-mini")
        
        # Test doc type model generation
        info = InfoModel(texts=[
            TextInfo(content="Validate if text contains club contact information")
        ])
        doc_model = await agent.process(info)
        print("Doc Type Model:", doc_model)
        
        # Test extraction model generation
        info = InfoModel(
            texts=[TextInfo(
                content="Extract contact information from football club websites",
                metadata={"features": ["club_name", "contact_person", "email", "phone"]}
            )]
        )
        extract_model = await agent.process(info)
        print("Extraction Model:", extract_model)

    asyncio.run(test()) 