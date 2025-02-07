import asyncio
from ai_suite.ie.agents.content_scraper_agent import ContentScraperAgent
from ai_suite.ie.agents.url_jina_discovery_agent import URLJinaAgent
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
from ai_suite.ie.models.models import ChallengeWebsiteUrls
from ai_suite.ie.utils.logging_config import setup_logging

async def main():
    # Set up logging
    logger = setup_logging()
    
    # Initialize
    llm = LLMFactory("openai")
    model_name = "gpt-4o-mini"  # or your preferred model
    token_tracker = TokenUsageTracker(model_name)
    
    # Create agents with logger
    scraper = ContentScraperAgent(
        llm_client=llm,
        model_name=model_name,
        token_tracker=token_tracker,
        output_dir="ai_suite/data",
        logger=logger
    )
    
    url_agent = URLJinaAgent(
        llm_client=llm,
        model_name=model_name,
        token_tracker=token_tracker,
        response_model=ChallengeWebsiteUrls,
        logger=logger
    )
    
    # Test URL
    test_url = "https://www.herox.com/crowdsourcing-projects"
    
    # First scrape the content
    scraper_result = await scraper.scrape_url(test_url)
    if not scraper_result or not scraper_result.success:
        print("Failed to scrape content")
        return
    
    # Then extract URLs
    url_result = await url_agent.extract_urls(scraper_result)
    
    # Print results
    print("\nURL Extraction Results:")
    print(f"Source: {url_result.source_url}")
    print("\nExtracted Challenge URLs:")
    urls = url_result.extracted_urls
    
    print("\nChallenge Listings:")
    for url in urls.challenge_listing_urls:
        print(f"- {url}")
    
    print("\nPagination/Navigation URLs:")
    for url in urls.pages_urls:
        print(f"- {url}")
    
    if not url_result.success:
        print(f"\nError: {url_result.error}")
    
    # Print token usage
    usage_stats = url_agent.get_usage_summary()
    print(f"\nToken Usage: {usage_stats['total_tokens']}")
    print(f"Cost: ${usage_stats['cost_usd']:.4f}")

if __name__ == "__main__":
    asyncio.run(main()) 