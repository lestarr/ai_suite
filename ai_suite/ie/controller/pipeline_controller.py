from typing import Dict, Optional, List, Type
import os
import logging
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel
from ai_suite.ie.agents.agent_factory import AgentFactory

class PipelineController:
    """Base controller for managing pipeline execution and resources"""
    
    def __init__(self, model_name: str, base_output_dir: str):
        # Setup core components
        self.model_name = model_name
        self.base_output_dir = base_output_dir
        self.llm = LLMFactory("openai")
        self.token_tracker = TokenUsageTracker(model_name)
        self.agents: Dict[str, BaseAgent] = {}
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Setup directories
        os.makedirs(base_output_dir, exist_ok=True)
        
        # Create agent factory
        self.agent_factory = AgentFactory(
            llm=self.llm,
            model_name=self.model_name,
            output_dir=self.base_output_dir,
            token_tracker=self.token_tracker,
            logger=self.logger
        )

    def create_agent(self, agent_class: Type[BaseAgent], **kwargs) -> BaseAgent:
        """Create an agent using the factory"""
        return self.agent_factory.create_agent(agent_class, **kwargs)

    def add_agent(self, name: str, agent: BaseAgent):
        """Add an agent to the pipeline"""
        self.agents[name] = agent
        self.logger.info(f"Added agent: {agent.__class__.__name__}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        return self.agents.get(name)

    async def run_agent(self, name: str, info: InfoModel) -> InfoModel:
        """Run a specific agent"""
        agent = self.get_agent(name)
        if not agent:
            raise ValueError(f"Agent {name} not found")
            
        try:
            self.logger.info(f"Running agent: {name}")
            result = await agent.process(info)
            self.logger.info(f"Agent {name} completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Failed to run agent {name}: {str(e)}")
            raise

    async def run(self, start_url: str, enable_scraping_rerun: bool = False, enable_extraction_rerun: bool = False) -> InfoModel:
        """Run the pipeline with the given start URL"""
        self.logger.info(f"Starting pipeline with URL: {start_url}")
        info = InfoModel(
            urls=[start_url], 
            enable_scraping_rerun=enable_scraping_rerun,
            enable_extraction_rerun=enable_extraction_rerun
        )
        
        # Run pipeline steps
        for step in self.get_pipeline_steps():
            self.logger.info(f"\n{'='*20} Running {step} {'='*20}")
            info = await self.run_agent(step, info)
            self.logger.info(f"URLs remaining: {len(info.urls)}")
            self.logger.info(f"Texts to process: {len(info.texts)}")
        
        # Print usage statistics
        self.print_usage()
        return info

    def get_pipeline_steps(self) -> List[str]:
        """Get ordered list of pipeline steps - override in subclass"""
        raise NotImplementedError("Subclasses must implement get_pipeline_steps()")

    def setup_pipeline(self):
        """Configure and add agents - override in subclass"""
        raise NotImplementedError("Subclasses must implement setup_pipeline()")

    def print_usage(self):
        """Print token usage statistics"""
        usage = self.token_tracker.get_summary()
        print(f"\nTotal Token Usage: {usage['total_tokens']:,}")
        print(f"Total Cost: ${usage['cost_usd']:.4f}")

# class HeroxPipeline(PipelineController):
#     """Herox-specific pipeline implementation"""
    
#     def __init__(self, model_name: str = "gpt-4o-mini", base_output_dir: str = "ai_suite/data/herox"):
#         super().__init__(model_name, base_output_dir)
#         self.setup_pipeline()

#     def setup_pipeline(self):
#         """Configure and add Herox-specific agents"""
#         from ai_suite.ie.agents.content_scraper_agent import ContentScraperAgent
#         from ai_suite.ie.agents.url_jina_discovery_agent import URLJinaAgent
#         from ai_suite.ie.agents.extraction_agent import ExtractionAgent
#         from ai_suite.ie.models.challenge_models import (
#             ChallengeWebsiteUrls, 
#             ChallengeDetails, 
#             ChallengeDocTypeModel
#         )
#         from ai_suite.ie.models.project_models import ProjectModel
        
#         # Add scraper with URL limit
#         scraper = ContentScraperAgent(
#             self.llm,
#             self.model_name,
#             self.token_tracker,
#             output_dir=self.base_output_dir,
#             max_urls=3  # Limit URLs here
#         )
#         self.add_agent("scraper", scraper)

#         # Add URL discovery
#         url_agent = URLJinaAgent(
#             self.llm,
#             self.model_name,
#             self.token_tracker,
#             response_model=ChallengeWebsiteUrls
#         )
#         self.add_agent("url_discovery", url_agent)

#         # Add extractor
#         extractor = ExtractionAgent(
#             self.llm,
#             self.model_name,
#             project_model=ProjectModel(
#                 name="herox_challenge",
#                 doc_type_model=ChallengeDocTypeModel,
#                 extraction_models=["ChallengeDetails"]
#             ),
#             token_tracker=self.token_tracker,
#             output_dir=self.base_output_dir
#         )
#         self.add_agent("extractor", extractor)

#         # Add save extractions agent
#         saver = SaveExtractionsAgent(
#             output_dir=self.base_output_dir,
#             model_name=self.model_name
#         )
#         self.add_agent("saver", saver)

#         # Add format results agent
#         formatter = FormatResultsAgent(
#             output_dir=self.base_output_dir,
#             model_name=self.model_name,
#             extraction_models=["ChallengeDetails"],
#             table_format="grid"
#         )
#         self.add_agent("formatter", formatter)

#     def get_pipeline_steps(self) -> List[str]:
#         """Get ordered list of pipeline steps"""
#         return ["scraper", "url_discovery", "scraper", "extractor", "saver", "formatter"]

# if __name__ == "__main__":
#     import asyncio
    
#     async def main():
#         pipeline = HeroxPipeline()
#         await pipeline.run("https://www.herox.com/crowdsourcing-projects")

#     asyncio.run(main()) 