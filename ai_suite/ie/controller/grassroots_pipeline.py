from typing import List
from ai_suite.ie.controller.pipeline_controller import PipelineController
from ai_suite.ie.agents.content_scraper_agent import ContentScraperAgent
from ai_suite.ie.agents.url_jina_discovery_agent import URLJinaAgent
from ai_suite.ie.agents.extraction_agent import ExtractionAgent
from ai_suite.ie.agents.save_extractions_agent import SaveExtractionsAgent
from ai_suite.ie.agents.format_results_agent import FormatResultsAgent
from ai_suite.ie.models.grassroot_models import (
    ClubURLDiscovery, 
    ClubContact, ClubContactList, ClubContactDocType
)
from ai_suite.ie.models.project_models import ProjectModel

class GrassrootsPipeline(PipelineController):
    """Grassroots-specific pipeline implementation"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", base_output_dir: str = "ai_suite/data/grassroots"):
        super().__init__(model_name, base_output_dir)
        self.setup_pipeline()

    def get_pipeline_steps(self) -> List[str]:
        """Define the order of pipeline steps"""
        return ["scraper",  "extractor", "saver", "formatter"]

    def setup_pipeline(self):
        """Configure and add Grassroots-specific agents"""
        # Create agents with specific configurations
        self.add_agent("scraper", self.create_agent(
            ContentScraperAgent,
            max_urls=5  # Increased from Herox's 3 since Grassroots might have more relevant content per page
        ))
        
        self.add_agent("url_discovery", self.create_agent(
            URLJinaAgent,
            response_model=ClubURLDiscovery
        ))        
        
        
        self.add_agent("extractor", self.create_agent(
            ExtractionAgent,
            project_model=ProjectModel(
                name="grassroots_club_contacts",
                doc_type_model=ClubContactDocType,
                extraction_models={"ClubContact": "ClubContactList"}
            )
        ))
        
        self.add_agent("saver", self.create_agent(SaveExtractionsAgent))
        
        self.add_agent("formatter", self.create_agent(
            FormatResultsAgent,
            extraction_models=["ClubContact"],
            field_mapping={
                "ClubContact": [
                    "club_name",
                    "official_designation",
                    "contact_name",
                    "email",
                    "phone_number",
                    "location",
                    "level_of_play",
                    "membership_size",
                    "website",
                    "affiliated_fa"
                ]
            },
            table_format="grid"
        ))

if __name__ == "__main__":
    import asyncio
    
    async def main():
        pipeline = GrassrootsPipeline()
        await pipeline.run("https://www.teamgrassroots.co.uk/fa-links/", 
                         enable_scraping_rerun=False, 
                         enable_extraction_rerun=False)

    asyncio.run(main())
