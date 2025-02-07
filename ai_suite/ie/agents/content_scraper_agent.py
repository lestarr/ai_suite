from typing import Optional, List
from pydantic import BaseModel, Field
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel, TextInfo
from ai_suite.ie.utils.scraping import get_jina_data_markdown
from ai_suite.ie.utils.url import get_clean_domain, normalize_url
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker, clean_markdown

import os
import logging

class ScraperResult(BaseModel):
    """Container for scraped content."""
    source: str
    content: str
    doc_type: str = None
    content_length: int
    success: bool = True

class ContentScraperAgent(BaseAgent):
    """Agent for scraping web content."""
    
    def __init__(
        self,
        llm_client: LLMFactory,
        model_name: str,
        token_tracker: TokenUsageTracker = None,
        output_dir: str = "ai_suite/data",
        max_urls: int = None,
        logger: logging.Logger = None
    ):
        """Initialize scraper with output directory."""
        super().__init__(llm_client, model_name, token_tracker, logger=logger)
        self.output_dir = output_dir
        self.max_urls = max_urls

    async def process(self, info: InfoModel) -> InfoModel:
        """Scrape content from URLs that haven't been seen yet."""
        self.log_section("Content Scraping")
        
        # Apply URL limit if set
        if self.max_urls:
            info.urls = info.urls[:self.max_urls]
            
        # Get unprocessed URLs
        urls_to_scrape = [url for url in info.urls if url not in info.seen_urls]
        if not urls_to_scrape and not info.enable_scraping_rerun:
            self.logger.info("No new URLs to scrape")
            return info
            
        for url in urls_to_scrape:
            try:
                self.log_subsection(f"Scraping URL: {url}")
                
                # Check if content already exists
                normalized_url = normalize_url(url)
                scraping_dir = os.path.join(self.output_dir, "scraping")
                existing_file = f"{scraping_dir}/{normalized_url}_scrapped.txt"
                
                if os.path.exists(existing_file) and not info.enable_scraping_rerun:
                    self.logger.info(f"Content already exists at: {existing_file}")
                    with open(existing_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    # Scrape content
                    content = await get_jina_data_markdown(url, self.logger)
                    content = clean_markdown(content)
                    if not content:
                        self.add_error(f"ContentScraperAgent.process:{url}", "Failed to fetch content")
                        continue
                    
                    # Save content
                    os.makedirs(scraping_dir, exist_ok=True)
                    with open(existing_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"Content saved to: {existing_file}")
                
                # change input InfoModel
                text_info = TextInfo(
                    content=content,
                    source_url=url,
                    path=existing_file
                )
                info.texts.append(text_info)
                info.seen_urls.append(url)
                info.urls.remove(url)
                
            except Exception as e:
                self.add_error(f"ContentScraperAgent.process:{url}", str(e))
        
        return info

   

# Example usage
if __name__ == "__main__":
    import asyncio
    from ai_suite.ie.llm.llm_factory import LLMFactory
    from ai_suite.ie.utils.utils import TokenUsageTracker
    
    async def main():
        # Initialize
        llm = LLMFactory("openai")
        model_name = "gpt-4o-mini"
        token_tracker = TokenUsageTracker(model_name)
        agent = ContentScraperAgent(llm, model_name, token_tracker)
        
        # Test URL
        result = await agent.scrape_url("https://www.herox.com/crowdsourcing-projects")
        
        # Print results
        if result:
            print("\nScraping Result:")
            print(f"URL or source: {result.source}")
            print(f"Content length: {result.content_length}")
        
        if agent.get_errors():
            print("\nErrors encountered:")
            for error in agent.get_errors():
                print(f"- {error['location']}: {error['error']}")
        
        # Print token usage
        usage_stats = agent.get_usage_summary()
        print(f"\nToken Usage: {usage_stats['total_tokens']}")
        print(f"Cost: ${usage_stats['cost_usd']:.4f}")
    
    asyncio.run(main()) 