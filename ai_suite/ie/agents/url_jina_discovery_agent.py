from typing import Optional, List
from pydantic import BaseModel
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel
from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
import logging

URL_EXTRACTION_PROMPT = """
Analyze the webpage content and extract the URLs defined in the response model.
Make sure to extract all the URLs defined in the response model.
In case of multiple URLs for multiple listings, extract all of them.
"""

class URLJinaAgent(BaseAgent):
    def __init__(
        self, 
        llm_client: LLMFactory, 
        model_name: str, 
        token_tracker: TokenUsageTracker = None,
        logger: logging.Logger = None,
        response_model: type[BaseModel] = None,
        output_dir: str = None
    ):
        super().__init__(llm_client, model_name, token_tracker, logger=logger, output_dir=output_dir)
        self.response_model = response_model

    async def process(self, info: InfoModel) -> InfoModel:
        """Discover URLs from scraped content"""
        self.log_section("URL Discovery")
        
        discovered_urls = []
        for text in info.texts:
            try:
                self.log_subsection(f"Processing text from: {text.source_url}")
                result, usage = extract_with_response_model(
                    text.content,
                    response_model=self.response_model,
                    llm_client=self.llm_client,
                    model=self.model_name
                )
                self.track_usage(usage)
                
                if result and hasattr(result, 'urls'):
                    # Convert HttpUrl to string when adding to discovered_urls
                    urls = [str(url.url) for url in result.urls]
                    discovered_urls.extend(urls)
                    self.logger.info(f"Discovered URLs: {urls}")
            except Exception as e:
                self.add_error(f"URLJinaAgent.process:{text.source_url}", str(e))
                self.logger.error(f"Error processing {text.source_url}: {str(e)}")
        
        # Add new URLs to info model
        info.urls.extend([url for url in discovered_urls])
        info.texts.clear()
        self.logger.info(f"Total URLs discovered: {len(discovered_urls)}")
        return info

# Example usage
if __name__ == "__main__":
    import asyncio
    from ai_suite.ie.llm.llm_factory import LLMFactory
    from ai_suite.ie.utils.utils import TokenUsageTracker
    from ai_suite.ie.agents.content_scraper_agent import ContentScraperAgent
    from ai_suite.ie.models.challenge_models import ChallengeWebsiteUrls
    from ai_suite.ie.utils.logging import setup_logging
    async def main():
        # Initialize
        llm = LLMFactory("openai")
        model_name = "gpt-4o-mini"
        token_tracker = TokenUsageTracker(model_name)
        
        logger = setup_logging()
        # Create agents
        scraper = ContentScraperAgent(llm, model_name, token_tracker, logger=logger)
        url_agent = URLJinaAgent(llm, model_name, token_tracker, response_model=ChallengeWebsiteUrls, logger=logger)

        # Test URL
        test_url = "aenu.com"
        test_url = "https://www.herox.com/crowdsourcing-projects"
        # First scrape the content
        scraper_result = await scraper.scrape_url(test_url)
        if not scraper_result:
            print("Failed to scrape content")
            return
            
        # Then extract URLs
        url_result = await url_agent.process(scraper_result)
        
        # Print results
        print("\nURL Extraction Results:")
        print(f"Source: {scraper_result.source}")
        print("\nExtracted URLs:")
        urls = url_result.urls
        print(urls)
        
        
        if not url_result.success:
            print(f"\nError: {url_result.error}")
        
        # Print token usage
        usage_stats = url_agent.get_usage_summary()
        print(f"\nToken Usage: {usage_stats['total_tokens']}")
        print(f"Cost: ${usage_stats['cost_usd']:.4f}")
    
    asyncio.run(main())