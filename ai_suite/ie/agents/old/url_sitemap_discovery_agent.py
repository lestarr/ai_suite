from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.utils.utils import TokenUsageTracker
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.scraping import get_html_data, get_jina_data
from urllib.parse import urljoin, urlparse
import re

class SitemapInfo(BaseModel):
    """Model for sitemap URL extraction."""
    contains_sitemap_url: bool = Field(
        default=False,
        description="Whether the content contains a sitemap XML URL"
    )
    sitemap_url_list: List[str] = Field(
        default=[],
        description="List of sitemap URLs found"
    )
    explanation: str = Field(
        default="",
        description="Explanation of the sitemap findings"
    )

class URLDiscoveryResult(BaseModel):
    """Container for URL discovery results."""
    initial_url: str
    discovered_urls: List[str]
    domain: str
    errors: List[Dict] = []

class URLDiscoveryAgent(BaseAgent):
    def __init__(self, llm_client: LLMFactory, model_name: str, token_tracker: TokenUsageTracker = None):
        super().__init__(llm_client, model_name, token_tracker)
        self.seen_urls = set()

    def get_clean_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        domain = url.replace('https://', '').replace('http://', '')
        domain = domain.replace('www.', '')
        domain = domain.split('.')[0].split('/')[0]
        return domain

    

    async def check_sitemap_url(self, url: str, domain: str) -> Optional[List[str]]:
        """Check URL for sitemap content."""
        try:
            # Try sitemap first
            sitemap_content = await get_html_data(url)
            
            # Check for common error responses
            error_indicators = [
                ("<title>403 Forbidden</title>", "Access forbidden"),
                ("<title>404 Not Found</title>", "Page not found"),
                ("<title>500 Internal Server Error</title>", "Server error"),
            ]
            
            # If we got an error response, try jina instead
            for error_text, error_desc in error_indicators:
                if error_text in sitemap_content:
                    self.logger.warning(f"Sitemap access error at {url}: {error_desc}")
                    self.add_error(f"URLDiscoveryAgent.check_sitemap_url:{url}", f"Sitemap access error: {error_desc}")
                    
                    # Fall back to jina
                    self.logger.info(f"Falling back to direct scraping for {url}")
                    sitemap_content = await get_jina_data(url, delete_url_title_header=True)
                    self.logger.info(f"Jina content: {sitemap_content}")
                    

            # If no error, process sitemap content normally
            if not sitemap_content:
                return None
                        
            url_list = self.extract_urls_from_content(sitemap_content, domain)
            self.logger.info(f"URL list: {url_list} from content {sitemap_content}")
            # Check if this is a redirect to another sitemap
            for found_url in url_list:
                if 'sitemap' in found_url.lower():
                    return None
                    
            return url_list
            
        except Exception as e:
            self.add_error(f"URLDiscoveryAgent.check_sitemap_url:{url}", str(e))
            # Try jina as last resort
            try:
                self.logger.info(f"Trying direct scraping after error for {url}")
                content = await get_jina_data(url, delete_url_title_header=True)
                if content:
                    url_list = self.extract_urls_from_content(content, domain)
                    if url_list:
                        self.logger.info(f"Found {len(url_list)} URLs through direct scraping")
                        return url_list
            except Exception as jina_error:
                self.add_error(f"URLDiscoveryAgent.check_sitemap_url.jina:{url}", str(jina_error))
            return None

    async def _discover_from_sitemap(self, base_url: str, domain: str) -> List[str]:
        """Discover URLs from sitemap files."""
        try:
            sitemap_paths = [
                '/sitemap.xml',
                '/sitemap_index.xml',
                '/robots.txt',
            ]
            
            self.log_subsection("Checking Sitemap Locations")
            for path in sitemap_paths:
                sitemap_url = urljoin(base_url, path)
                self.logger.info(f"Checking: {sitemap_url}")
                
                # Direct sitemap check
                urls = await self.check_sitemap_url(sitemap_url, domain)
                if urls:
                    self.logger.info(f"Found {len(urls)} URLs in sitemap")
                    return urls
                
                # Try content analysis for sitemap references
                content = await get_html_data(sitemap_url)
                self.logger.info(f"Sitemap content: {content}")
                if "error" in content.lower() or "forbidden" in content.lower():
                    content = await get_jina_data(sitemap_url, delete_url_title_header=True)
                    self.logger.info(f"Jina content: {content}")
                    if not content:
                        continue
                
                sitemap_info, usage = extract_with_response_model(
                    content,
                    response_model=SitemapInfo,
                    llm_client=self.llm_client,
                    model=self.model_name
                )
                self.logger.info(f"Sitemap info: {sitemap_info}")
                self.track_usage(usage)
                if sitemap_info.sitemap_url_list:
                    for sitemap_url in sitemap_info.sitemap_url_list:
                        urls = await self.check_sitemap_url(sitemap_url, domain)
                        if urls:
                            self.logger.info(f"Found {len(urls)} URLs in referenced sitemap")
                            return urls
            
            return []
            
        except Exception as e:
            self.add_error("URLDiscoveryAgent._discover_from_sitemap", str(e))
            return []

    async def discover_urls(self, initial_url: str, max_urls: int = 100) -> URLDiscoveryResult:
        """
        Discover URLs from initial URL.
        
        Args:
            initial_url: Starting URL
            max_urls: Maximum number of URLs to discover
            
        Returns:
            URLDiscoveryResult containing discovered URLs
        """
        try:
            self.log_section(f"Starting URL Discovery for {initial_url}")
            
            domain = self.get_clean_domain(initial_url)
            base_url = f"{urlparse(initial_url).scheme}://{urlparse(initial_url).netloc}"
            
            # Initial discovery from sitemap
            discovered_urls = await self._discover_from_sitemap(base_url, domain)
            
            # Ensure initial URL is included
            if initial_url not in discovered_urls:
                discovered_urls.insert(0, initial_url)
            
            # Remove duplicates while maintaining order
            discovered_urls = list(dict.fromkeys(discovered_urls))
            
            # Limit number of URLs
            if len(discovered_urls) > max_urls:
                self.logger.info(f"Limiting URLs to {max_urls}")
                discovered_urls = discovered_urls[:max_urls]
            
            return URLDiscoveryResult(
                initial_url=initial_url,
                discovered_urls=discovered_urls,
                domain=domain,
                errors=self.get_errors()
            )
            
        except Exception as e:
            self.add_error("URLDiscoveryAgent.discover_urls", str(e))
            return URLDiscoveryResult(
                initial_url=initial_url,
                discovered_urls=[initial_url],
                domain=self.get_clean_domain(initial_url),
                errors=self.get_errors()
            )

# Example usage
if __name__ == "__main__":
    import asyncio
    from webextract.extractor.llm_factory import LLMFactory
    from webextract.utils.utils import TokenUsageTracker
    
    async def main():
        # Initialize
        llm = LLMFactory("openai")
        model_name = "gpt-4o-mini"
        token_tracker = TokenUsageTracker(model_name)
        agent = URLDiscoveryAgent(llm, model_name, token_tracker)

        # Test URL discovery
        result = await agent.discover_urls("https://www.atomico.com")
        
        # Print results
        print("\nDiscovered URLs:")
        for url in result.discovered_urls:
            print(f"- {url}")
        
        if result.errors:
            print("\nErrors encountered:")
            for error in result.errors:
                print(f"- {error['location']}: {error['error']}")
        
        # Print token usage
        usage_stats = agent.get_usage_summary()
        print(f"\nToken Usage: {usage_stats['total_tokens']}")
        print(f"Cost: ${usage_stats['cost_usd']:.4f}")
    
    asyncio.run(main())