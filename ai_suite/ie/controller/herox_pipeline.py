from typing import List
from ai_suite.ie.controller.pipeline_controller import PipelineController
from ai_suite.ie.agents.content_scraper_agent import ContentScraperAgent
from ai_suite.ie.agents.url_jina_discovery_agent import URLJinaAgent
from ai_suite.ie.agents.extraction_agent import ExtractionAgent
from ai_suite.ie.agents.save_extractions_agent import SaveExtractionsAgent
from ai_suite.ie.agents.format_results_agent import FormatResultsAgent
from ai_suite.ie.models.challenge_models import (
    ChallengeWebsiteUrls, 
    ChallengeDetails, 
    ChallengeDocTypeModel
)
from ai_suite.ie.models.project_models import ProjectModel

class HeroxPipeline(PipelineController):
    """Herox-specific pipeline implementation"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", base_output_dir: str = "ai_suite/data/herox"):
        super().__init__(model_name, base_output_dir)
        self.setup_pipeline()

    def get_pipeline_steps(self) -> List[str]:
        """Define the order of pipeline steps"""
        return ["scraper", "url_discovery", "scraper", "extractor", "saver", "formatter"]

    def setup_pipeline(self):
        """Configure and add Herox-specific agents"""
        # Create agents with specific configurations
        self.add_agent("scraper", self.create_agent(
            ContentScraperAgent,
            max_urls=3
        ))
        
        self.add_agent("url_discovery", self.create_agent(
            URLJinaAgent,
            response_model=ChallengeWebsiteUrls
        ))
        
        self.add_agent("extractor", self.create_agent(
            ExtractionAgent,
            project_model=ProjectModel(
                name="herox_challenge",
                doc_type_model=ChallengeDocTypeModel,
                extraction_models=["ChallengeDetails"]
            )
        ))
        
        self.add_agent("saver", self.create_agent(SaveExtractionsAgent))
        
        self.add_agent("formatter", self.create_agent(
            FormatResultsAgent,
            extraction_models=["ChallengeDetails"],
            field_mapping={
                "ChallengeDetails": [
                    "title",
                    "organizer",
                    "submission_deadline",
                    "url",
                    "key_objective",
                    "judging_criteria",
                    "classification_keywords"
                ]
            },
            truncate_lengths={
                "key_objective": 500
            },
            table_format="grid"
        ))

if __name__ == "__main__":
    import asyncio
    
    async def main():
        pipeline = HeroxPipeline()
        await pipeline.run("https://www.herox.com/crowdsourcing-projects", enable_scraping_rerun=False, enable_extraction_rerun=False)

    asyncio.run(main()) 