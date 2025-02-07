import aiohttp
import logging
import requests
from typing import Optional
from ai_suite.ie.utils.utils import clean_markdown

async def get_jina_data_markdown(url: str, logger: logging.Logger) -> str:
    """
    Fetch webpage content through Jina API in markdown format asynchronously.
    
    Args:
        url: URL to fetch content from
        logger: Logger instance for logging
        api_key: Jina API key
        
    Returns:
        str: Markdown formatted content
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            #"Authorization": f"Bearer {api_key}",
            "X-Return-Format": "markdown",
            #"X-Retain-Images": "none"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(jina_url, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
                
    except aiohttp.ClientError as e:
        logger.error(f"Jina API request failed for {url}: {str(e)}")
        return ""
    except Exception as e:
        logger.error(f"Error fetching Jina data for {url}: {str(e)}")
        return ""

async def get_jina_data(url_to_scrape: str, leave_markdown: bool = False, delete_url_title_header: bool = False) -> Optional[str]:
    """
    Fetch and clean webpage content using Jina AI API.
    """
    url = f"https://r.jina.ai/{url_to_scrape}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
        
        if "404: Not Found" in response_text or "Target URL returned error 404" in response_text:
            logging.error(f"404 Not Found error for {url}")
            return None
            
        if not leave_markdown:
            try:
                response_text = clean_markdown(response_text)
            except Exception as e:
                logging.error(f"Error cleaning markdown for {url}: {str(e)}")
                return response_text  # Return uncleaned text as fallback
            
        if delete_url_title_header and "Markdown Content:" in response_text:
            response_text = response_text.split("Markdown Content:")[1]
            
        return response_text
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching {url}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing {url}: {str(e)}")
        return None

async def get_html_data(url_to_scrape: str) -> Optional[str]:
    """
    Get raw HTML content for sitemap processing.
    
    Args:
        url_to_scrape: The URL to fetch
        
    Returns:
        Raw HTML content or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_to_scrape) as response:
                if response.status == 404:
                    logging.error(f"404 Not Found error for {url_to_scrape}")
                    return None
                return await response.text()
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching HTML from {url_to_scrape}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching HTML from {url_to_scrape}: {str(e)}")
        return None


