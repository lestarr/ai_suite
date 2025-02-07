from typing import List, Set, Dict, Optional
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.utils.url import normalize_url_light
from ai_suite.ie.agents.url_jina_discovery_agent import URLExtractionResult, WebsiteUrls
import logging


class URLManagerAgent(BaseAgent):
    """Manages URL processing state and access."""
    
    def __init__(
        self, 
        llm_client: LLMFactory, 
        model_name: str, 
        token_tracker: TokenUsageTracker = None,
        logger: logging.Logger = None
    ):
        super().__init__(llm_client, model_name, token_tracker, logger=logger)
        self.discovered_urls: Optional[WebsiteUrls] = None
        self.processed_urls: Set[str] = set()
    
    def set_discovered_urls(self, url_extraction: URLExtractionResult):
        """Store discovered URLs from URL extraction result."""
        self.discovered_urls = url_extraction.extracted_urls
    
    def _mark_as_processed(self, urls: List[str]):
        """Mark URLs as processed."""
        self.processed_urls.update(
            normalize_url_light(url) for url in urls
        )
    
    def get_unprocessed_urls(self, category: str) -> List[str]:
        """Get unprocessed URLs for a specific category."""
        if not self.discovered_urls:
            self.logger.warning("No discovered URLs!")
            return []
            
        urls = []  # Change to list to maintain order
        if category == "portfolio":
            if self.discovered_urls.portfolio_page:
                urls.append(str(self.discovered_urls.portfolio_page))
        elif category == "team":
            if self.discovered_urls.team_page:
                urls.append(str(self.discovered_urls.team_page))
        elif category == "main":
            # Keep the order from main_menu
            urls = [str(url) for url in self.discovered_urls.main_menu]
        elif category == "linkedin":
            if self.discovered_urls.linkedin_page:
                urls.append(str(self.discovered_urls.linkedin_page))
        self.logger.info(f"Found URLs for {category}: {urls}")
        
        # Remove duplicates and filter processed URLs while preserving order
        seen_normalized = set()
        unprocessed_urls = []
        for url in urls:
            normalized = normalize_url_light(url)
            if normalized not in seen_normalized and normalized not in self.processed_urls:
                seen_normalized.add(normalized)
                unprocessed_urls.append(url)
        
        self._mark_as_processed(unprocessed_urls)
        return unprocessed_urls
    
