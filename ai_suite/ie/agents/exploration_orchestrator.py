from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.agents.url_jina_discovery_agent import URLJinaAgent
from ai_suite.ie.agents.content_scraper_agent import ContentScraperAgent
from ai_suite.ie.agents.extraction_agent import ExtractionAgent
from ai_suite.ie.models.system_models import InfoModel, ExplorationStatus
from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker

class OrchestratorDecision(BaseModel):
    next_action: str
    reasoning: str
    specific_instructions: Dict[str, Any] = {}

class ExplorationOrchestrator(BaseAgent):
    SYSTEM_PROMPT = """You are an AI orchestrator managing information exploration and extraction.
    Analyze the current state and results to decide the next best action.
    
    Possible actions:
    1. EXPLORE - Search for new relevant URLs in content
    2. SCRAPE - Fetch content from URLs
    3. EXTRACT - Extract structured information from content
    4. EVALUATE - Check completeness of extracted information
    5. MERGE - Combine extracted information from sub-models
    6. COMPLETE - Mark exploration as complete
    
    Consider:
    - Current depth of exploration (max depth is 3)
    - Status of extractions
    - Missing information
    - Quality and relevance of content
    """

    def __init__(
        self,
        llm_client: LLMFactory,
        model_name: str,
        project_model: Optional[BaseModel] = None,
        token_tracker: Optional[TokenUsageTracker] = None,
        output_dir: str = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(llm_client, model_name, token_tracker, output_dir, logger)
        self.project_model = project_model
        
        # Initialize sub-agents
        self.url_agent = URLJinaAgent(llm_client, model_name, token_tracker, logger)
        self.scraper = ContentScraperAgent(llm_client, model_name, token_tracker, output_dir, logger=logger)
        self.extractor = ExtractionAgent(llm_client, model_name, project_model, token_tracker, output_dir, logger)

    async def decide_next_action(self, info: InfoModel) -> OrchestratorDecision:
        """Use LLM to analyze current state and decide next action"""
        context = self._build_state_context(info)
        
        result, usage = await extract_with_response_model(
            context,
            response_model=OrchestratorDecision,
            llm_client=self.llm_client,
            model=self.model_name,
            system_prompt=self.SYSTEM_PROMPT
        )
        self.track_usage(usage)
        return result

    async def process(self, info: InfoModel) -> InfoModel:
        """Main orchestration loop"""
        # Initialize root URL if not set
        if not info.state.root_url and info.urls:
            info.state.root_url = info.urls[0]
            
        while info.state.status != ExplorationStatus.COMPLETE:
            decision = await self.decide_next_action(info)
            self.logger.info(f"Decision: {decision.next_action} - {decision.reasoning}")
            
            try:
                if decision.next_action == "EXPLORE":
                    info = await self._handle_exploration(info, decision)
                elif decision.next_action == "SCRAPE":
                    info = await self._handle_scraping(info, decision)
                elif decision.next_action == "EXTRACT":
                    info = await self._handle_extraction(info, decision)
                elif decision.next_action == "EVALUATE":
                    info = await self._evaluate_completeness(info, decision)
                elif decision.next_action == "MERGE":
                    info = await self._merge_results(info, decision)
                elif decision.next_action == "COMPLETE":
                    info.state.status = ExplorationStatus.COMPLETE
                    
            except Exception as e:
                self.add_error(f"ExplorationOrchestrator.process:{decision.next_action}", str(e))
                info.state.status = ExplorationStatus.FAILED
                break
                
        return info

    def _build_state_context(self, info: InfoModel) -> str:
        """Build context string describing current state for LLM"""
        context = [
            f"Current depth: {info.state.depth}",
            f"Current status: {info.state.status}",
            f"Number of URLs to process: {len(info.urls)}",
            f"Number of processed texts: {len(info.texts)}",
            f"Number of sub-models: {len(info.sub_models)}",
            f"Extracted information types: {list(info.merged_results.keys())}",
            f"Missing fields: {info.state.missing_fields}",
            f"Completeness score: {info.state.completeness_score}"
        ]
        return "\n".join(context)

    async def _handle_exploration(self, info: InfoModel, decision: OrchestratorDecision) -> InfoModel:
        """Handle URL exploration and create new InfoModels for discovered URLs"""
        if info.state.depth >= 3:
            self.logger.info("Maximum depth reached, skipping exploration")
            return info
            
        info.state.status = ExplorationStatus.EXPLORING
        
        # Explore URLs in current content
        explored_info = await self.url_agent.process(info)
        
        # Create new InfoModels for newly discovered URLs
        for url in explored_info.urls:
            if url not in info.seen_urls and url not in info.sub_models:
                new_info = InfoModel(
                    urls=[url],
                    state=ExplorationState(
                        depth=info.state.depth + 1,
                        parent_url=info.state.root_url,
                        root_url=url
                    )
                )
                info.sub_models[url] = new_info
                info.seen_urls.append(url)
        
        return info

    async def _handle_scraping(self, info: InfoModel, decision: OrchestratorDecision) -> InfoModel:
        """Handle content scraping"""
        info.state.status = ExplorationStatus.SCRAPING
        return await self.scraper.process(info)

    async def _handle_extraction(self, info: InfoModel, decision: OrchestratorDecision) -> InfoModel:
        """Handle information extraction"""
        info.state.status = ExplorationStatus.EXTRACTING
        return await self.extractor.process(info)

    async def _evaluate_completeness(self, info: InfoModel, decision: OrchestratorDecision) -> InfoModel:
        """Evaluate completeness of extracted information"""
        info.state.status = ExplorationStatus.EVALUATING
        
        # Analyze extractions and update missing fields
        info.state.missing_fields = []
        info.state.completeness_score = 0.0
        
        # Implementation of completeness evaluation logic
        # This could be another LLM call to analyze the extractions
        
        return info

    async def _merge_results(self, info: InfoModel, decision: OrchestratorDecision) -> InfoModel:
        """Merge results from sub-models into parent model"""
        info.state.status = ExplorationStatus.MERGING
        
        # Process completed sub-models
        for url, sub_model in info.sub_models.items():
            if sub_model.state.status == ExplorationStatus.COMPLETE:
                for text_info in sub_model.texts:
                    for extraction in text_info.extractions:
                        model_type = extraction.__class__.__name__
                        if model_type not in info.merged_results:
                            info.merged_results[model_type] = []
                        info.merged_results[model_type].append(extraction)
        
        return info 