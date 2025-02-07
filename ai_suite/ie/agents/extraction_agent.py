from typing import List, Dict, Any, Type, Optional
from pydantic import BaseModel, Field
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel, TextInfo
from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
from ai_suite.ie.models.project_models import ProjectModel
from ai_suite.ie.models.challenge_models import *  # To get all available models
from ai_suite.ie.models.grassroot_models import *  # Import grassroot models
import logging
import os
from ai_suite.ie.utils.url import normalize_url

SYSTEM_PROMPT_DOCTYPE_EXTRACTION = """
    You are an AI assistant for information extraction and text classification. Your task is to read the text and determine if this text contains information about one of the given document types. Consider given document types as topics which can be found in the text.
    If you can find the relevant information in the text, return the document type. If not, return "Other". Always give a detailed explanation of your decision.
"""

class ExtractionAgent(BaseAgent):
    def __init__(
        self,
        llm_client: LLMFactory,
        model_name: str,
        project_model: ProjectModel,
        token_tracker: TokenUsageTracker = None,
        output_dir: str = None,
        logger: logging.Logger = None,
    ):
        super().__init__(llm_client, model_name, token_tracker, logger=logger)
        self.project_model = project_model
        self.extractions_dir = os.path.join(output_dir, "extractions", model_name) if output_dir else None

    def _has_cached_extraction(self, url: str, model_name: str) -> bool:
        """Check if extraction exists in cache"""
        if not self.extractions_dir or not url:
            return False
        path = os.path.join(self.extractions_dir, f"{normalize_url(url)}_{model_name}.json")
        return os.path.exists(path)

    async def _check_doc_type(self, text: str, doc_type: str) -> bool:
        """Check if text matches document type"""
        if not self.project_model.doc_type_model:
            return True
            
        try:
            result, usage = extract_with_response_model(
                text,
                response_model=self.project_model.doc_type_model,
                llm_client=self.llm_client,
                model=self.model_name,
                system_prompt=SYSTEM_PROMPT_DOCTYPE_EXTRACTION
            )
            self.track_usage(usage)
            doc_type_extracted = result.doc_type if hasattr(result, 'doc_type') else None
            self.logger.info(f"Document type: {doc_type_extracted}")
            if doc_type_extracted and doc_type_extracted == doc_type:
                self.logger.info(f"Document type matches model name: {doc_type_extracted} == {doc_type}")
                return True
            else:
                self.add_error("ExtractionAgent._check_doc_type", f"Document type {doc_type_extracted} does not match {doc_type}")
                return False
        except Exception as e:
            self.add_error("ExtractionAgent._check_doc_type", str(e))
            return False

    async def process(self, info: InfoModel) -> InfoModel:
        """Extract information using project model configuration."""
        self.log_section(f"Information Extraction: {self.project_model.name}")
        
        for text in info.texts:
            try:
                self.log_subsection(f"Processing text from: {text.source_url or text.path}")
                
                for doc_type, model_name in self.project_model.extraction_models.items():
                    # Skip if cached and rerun not enabled
                    if not info.enable_extraction_rerun and self._has_cached_extraction(text.source_url, model_name=model_name):
                        self.logger.info(f"Skipping {model_name} - cached extraction exists")
                        continue

                    # Check doc type matches model name
                    if not await self._check_doc_type(text.content, doc_type):
                        continue
                    
                    # Get model class and extract
                    try:
                        model_class = globals()[model_name]
                        self.logger.info(f"Available models: {', '.join(globals().keys())}")
                        self.logger.info(f"Attempting to extract with model: {model_name}")
                    except KeyError:
                        error_msg = f"Model '{model_name}' not found in available models. Please ensure the model is imported."
                        self.logger.error(error_msg)
                        self.add_error(f"ExtractionAgent.process:model_lookup", error_msg)
                        continue
                    
                    try:
                        extraction_result, usage = extract_with_response_model(
                            text.content,
                            response_model=model_class,
                            llm_client=self.llm_client,
                            model=self.model_name
                        )
                        self.track_usage(usage)
                        
                        if extraction_result:
                            text.extractions.append(extraction_result)
                            self.logger.info(f"Successfully extracted {model_name}: {extraction_result}")
                        else:
                            self.logger.warning(f"No extraction result for {model_name}")
                    
                    except Exception as e:
                        self.add_error(f"ExtractionAgent.extract:{model_name}", f"Extraction failed: {str(e)}")
                        self.logger.error(f"Extraction error for {model_name}: {str(e)}", exc_info=True)
                
            except Exception as e:
                error_msg = f"Processing failed: {str(e)}"
                self.add_error(f"ExtractionAgent.process:{text.source_url}", error_msg)
                self.logger.error(error_msg, exc_info=True)
                
        return info

if __name__ == "__main__":
    import asyncio
    from ai_suite.ie.utils.logging import setup_logger
    from ai_suite.ie.models.challenge_models import ChallengeDetails, ChallengeDocTypeModel

    async def main():
        # Setup
        llm = LLMFactory("openai")
        model_name = "gpt-4o-mini"
        logger = setup_logger("extraction_test")
        token_tracker = TokenUsageTracker(model_name)

        # Create project model with model names
        project_model = ProjectModel(
            name="herox_challenge",
            doc_type_model=ChallengeDocTypeModel,
            extraction_models={"ChallengeDetails": "ChallengeDetails"}  # Just model names as strings
        )

        # Initialize agent
        agent = ExtractionAgent(
            llm_client=llm,
            model_name=model_name,
            project_model=project_model,
            token_tracker=token_tracker,
            logger=logger
        )

        # Create test data
        test_text = """
        Title: The Good Jobs Prize
        URL: https://example.com/challenge/good-jobs
        Organizer: Innovation Works Foundation
        
        Prize: $100,000
        
        Key Objective:
        The Good Jobs Prize challenges teams to develop innovative solutions 
        for connecting job seekers with meaningful employment opportunities.
        
        Timeline:
        - Submission Deadline: 2024-12-01
        - Winners Announced: 2025-01-15
        
        Requirements:
        - Open to teams worldwide
        - Must include working prototype
        - Solution must be scalable
        """

        info = InfoModel(texts=[
            TextInfo(
                content=test_text,
                source_url="https://example.com/challenge",
                path="/tmp/test.txt"
            )
        ])

        # Process
        result = await agent.process(info)

        # Print results
        print("\nProcessing Results:")
        print("-" * 40)
        for text in result.texts:
            print(f"Source: {text.source_url or text.path}")
            print("\nExtractions:")
            for extraction in text.extractions:
                print(f"\nModel: {extraction.__class__.__name__}")
                print(extraction.model_dump_json(indent=2))

        # Print errors if any
        if agent.get_errors():
            print("\nErrors:")
            for error in agent.get_errors():
                print(f"- {error['location']}: {error['error']}")

        # Print token usage
        usage = agent.get_usage_summary()
        print(f"\nToken Usage: {usage['total_tokens']:,}")
        print(f"Cost: ${usage['cost_usd']:.4f}")

    asyncio.run(main())
