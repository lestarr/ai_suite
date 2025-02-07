import os
from ai_suite.ie.models.models import Topics

from ai_suite.ie.utils.scraping import get_jina_data, get_html_data

from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.json import pretty_print_json
from ai_suite.ie.utils.utils import TokenUsageTracker
from urllib.parse import urljoin, urlparse
from typing import List
from pydantic import BaseModel, Field, model_validator, ValidationInfo
import re
import logging

class ExtractSitemap(BaseModel):
    """Model for extracting URLs from sitemap-like content."""
    contains_sitemap_url: bool = Field(default=False, description="Whether the content contains an url with a sitemap xml")
    sitemap_url_list: List[str] = Field(default=[], description="The url with a sitemap xml")
    explanation: str = Field(default="", description="The explanation for the sitemap url")

    validated: bool = False

    @model_validator(mode="after")
    def validate_sitemap_url(self, info: ValidationInfo) -> "ExtractSitemap":
        self.validated = False
        if info and info.context:
            text_chunks = info.context.get("text_chunk", None)
            if text_chunks and self.sitemap_url_list:
                for url in self.sitemap_url_list:
                    if url in text_chunks and 'sitemap' in url.lower():
                        self.validated = True
                        break
                if not self.validated:
                    self.sitemap_url_list = []
        return self

class URLInfo(BaseModel):
    """Model for a url and its relevance to a given topic"""
    url: str = Field(..., description="The url to analyze")
    topic: Topics = Field(..., description="A topic, for which the url could be most relevant")
    relevance: float = Field(..., description="The relevance of the url to the info topics", ge=0, le=1)
    explanation: str = Field(..., description="The explanation for the relevance of the url to the info topics")
    validated: bool = False

    @model_validator(mode="after")
    def validate_url(self, info: ValidationInfo) -> "URLInfo":
        self.validated = False
        if info and info.context:
            text_chunks = info.context.get("text_chunk", None)
            if text_chunks and self.url:
                if self.url in text_chunks:
                    self.validated = True
        return self
    
class AnalyzeURLs(BaseModel):
    """Extract and analyze urls from the given text. Return list of relevant urls along with their relevance to a given topic"""
    urls: List[URLInfo] = Field(..., description="List of urls and their relevance to a given topic")

def analyze_urls(urls: List[str], llm: LLMFactory, model_name: str, logger: logging.Logger, token_tracker: TokenUsageTracker = None) -> List[URLInfo]:
    """Analyze URLs and group them by topic."""
    try:
        logger.info("\nAnalyzing URLs:")
        logger.info("-"*50)
            
        input_text = "\n".join(urls)
        url_analysis, usage = extract_with_response_model(input_text, AnalyzeURLs, llm_client=llm, model=model_name)
        if token_tracker:
            token_tracker.add_usage(usage)
        logger.info(f"URL analysis:")
        pretty_print_json(url_analysis.model_dump())
        # sort urls by relevance
        if url_analysis and url_analysis.urls:
            sorted_urls = sorted(url_analysis.urls, key=lambda x: x.relevance, reverse=True)
        else:
            sorted_urls = []        
        logger.info(f"Sorted URLs:\n {sorted_urls}")
        return sorted_urls
    except Exception as e:
        logger.error(f"Error in analyze_urls: {str(e)}")
        return []

def get_clean_domain(url: str) -> str:
    """Extract just the domain name (e.g., 'atomico' from 'https://www.atomico.com')."""
    # Remove protocol
    domain = url.replace('https://', '').replace('http://', '')
    # Remove www. if present
    domain = domain.replace('www.', '')
    # Get first part before any dot or slash
    domain = domain.split('.')[0].split('/')[0]
    return domain


def extract_urls_from_content(content: str, domain: str, logger: logging.Logger = None) -> List[str]:
    """Extract URLs from content matching domain."""
    try:
        url_pattern = re.compile(r'http[s]?://[^\s<>"\']+[a-z]')
        urls = url_pattern.findall(content)
        urls = [url for url in urls if domain in url]
            
        omitted_urls = [url for url in urls if domain not in url]
        logger.info(f"Omitted URLs: {omitted_urls}")
            
        return urls
    except Exception as e:
        logger.error(f"Error in extract_urls_from_content: {str(e)}")
        return []   

def check_sitemap_url(url: str, domain: str) -> List[str]:
    try:
        sitemap_content = get_html_data(url)
        if sitemap_content:                        
            url_list = extract_urls_from_content(sitemap_content, domain)
            for url in url_list:
                if 'sitemap' in url.lower():
                    return None
            return url_list
        return None
    except Exception as e:
        logging.error(f"Error in check_sitemap_url for {url}: {str(e)}")
        return None

def get_url_list(initial_url: str, max_urls: int = 20, llm: LLMFactory = None, model_name: str = None) -> List[str]:
    """Get list of URLs from a website using sitemap files or page scraping."""
    logger = logging.getLogger(__name__)
    errors = []
    
    try:
        logger.info("\n" + "="*80)
        logger.info("Starting URL Discovery Process")
        logger.info(f"Maximum URLs to collect: {max_urls}")
        logger.info("="*80)
        
        all_urls = []
        all_urls.append(initial_url)
        
        parsed_url = urlparse(initial_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        domain = get_clean_domain(base_url)
        
        logger.info("\nInitial Setup:")
        logger.info(f"Initial URL: {initial_url}")
        logger.info(f"Base URL: {base_url}")
        logger.info(f"Domain: {domain}")
        
        sitemap_paths = [        
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/robots.txt',
        ]
        
        logger.info("\nSitemap Locations to Check:")
        for path in sitemap_paths:
            logger.info(f"- {urljoin(base_url, path)}")
        
        for path in sitemap_paths:
            try:
                url = urljoin(base_url, path)
                logger.info("\n" + "-"*50)
                logger.info(f"Checking potential sitemap at: {url}")
                
                # Direct sitemap check
                try:
                    all_urls = check_sitemap_url(url, domain)
                except Exception as e:
                    errors.append({
                        "location": f"check_sitemap_url:{url}",
                        "error": str(e)
                    })
                    continue
                
                if all_urls is None:
                    logger.info("Found sitemap redirect - skipping")
                elif all_urls and len(all_urls) > 1:
                    logger.info(f"Success! Found {len(all_urls)} URLs in sitemap")
                    # if len(all_urls) > max_urls:
                    #     logger.info(f"Truncating to {max_urls} URLs due to limit")
                    #     all_urls = all_urls[:max_urls]
                    logger.info("URLs found:")
                    for found_url in all_urls:
                        logger.info(f"- {found_url}")
                    break
                else:
                    logger.info("No direct URLs found, trying content analysis...")
                
                # Content analysis for sitemap references
                try:
                    content = get_jina_data(url, delete_url_title_header=True)
                except Exception as e:
                    errors.append({
                        "location": f"get_jina_data:{url}",
                        "error": str(e)
                    })
                    continue
                
                if not content:
                    logger.info(f"No parseable content found at {url}")
                    continue            
                
                try:
                    sitemap_json, usage = extract_with_response_model(
                        content, 
                        response_model=ExtractSitemap, 
                        llm_client=llm, 
                        model=model_name
                    )
                except Exception as e:
                    errors.append({
                        "location": f"extract_sitemap:{url}",
                        "error": str(e)
                    })
                    continue
                
                if sitemap_json and sitemap_json.sitemap_url_list:
                    logger.info("\nFound potential sitemap references:")
                    for sitemap_url in sitemap_json.sitemap_url_list:
                        sitemap_url = sitemap_url.replace('\\', '')
                        logger.info(f"\nChecking referenced sitemap: {sitemap_url}")
                        
                        all_urls = check_sitemap_url(sitemap_url, domain)
                        if all_urls is None:
                            logger.info("Found sitemap redirect - skipping")
                        elif all_urls and len(all_urls) > 1:
                            logger.info(f"Success! Found {len(all_urls)} URLs in referenced sitemap")
                            logger.info("URLs found:")
                            for found_url in all_urls:
                                logger.info(f"- {found_url}")
                            break
                        else:
                            logger.info("No valid URLs found in referenced sitemap")
                        
                    if len(all_urls or []) > 0:
                        break
                else:
                    logger.info(f"No sitemap references found in {url}")
                    
            except Exception as e:
                errors.append({
                    "location": f"process_sitemap:{url}",
                    "error": str(e)
                })
                continue
        
        final_urls = maintain_order_remove_duplicates(all_urls or [])
        if len(final_urls) > 100:
            final_urls = final_urls[:100]
        
        # Add errors to the logger
        if errors:
            logger.error("\nErrors encountered during URL discovery:")
            for error in errors:
                logger.error(f"Error in {error['location']}: {error['error']}")
        
        logger.info("\n" + "="*80)
        logger.info("URL Discovery Complete")
        logger.info(f"Total unique URLs found: {len(final_urls)}")
        logger.info("\nFinal URL List:")
        for url in final_urls:
            logger.info(f"- {url}")
        logger.info("="*80)
        
        return final_urls
        
    except Exception as e:
        errors.append({
            "location": "get_url_list",
            "error": str(e)
        })
        logger.error(f"Fatal error in get_url_list: {str(e)}")
        return []

def maintain_order_remove_duplicates(urls: List[str]) -> List[str]:
    """Remove duplicates while maintaining the order of first appearance."""
    seen = set()
    return [x for x in urls if not (x in seen or seen.add(x))]
def normalize_url_light(url: str) -> str:
    # Remove protocol (http:// or https://)
    url = re.sub(r'^https?://', '', url)
    
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')
       
    # Convert to lowercase for case-insensitive comparison
    url = url.lower()
    return url

def normalize_url(url: str) -> str:
    """Normalize URLs to prevent duplicates with different formats."""
    # Remove protocol (http:// or https://)
    url = re.sub(r'^https?://', '', url)
    
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')   
    
    # Convert to lowercase for case-insensitive comparison
    url = url.lower()
    # replace slashes with underscores
    url = url.replace('/', '_')
    # Remove any special characters except alphanumeric, dots
    # (keeping dots for domain extensions )
    url = re.sub(r'[^\w\.]', '', url)
    return url

def save_url_content(url: str, content: str, output_dir: str, logger: logging.Logger):
        """Save merged content with URL list to a file."""
        # Create directory if it doesn't exist
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create the output file
        output_file = f'{output_dir}/{normalize_url(url)}_scrapped.txt'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write URLs section
            f.write("="*80 + "\n")
            f.write("URLs used for content extraction:\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"URL: {url}\n")
                
            # Write content section
            f.write("="*80 + "\n")
            f.write("Scrapped Content:\n")
            f.write("="*80 + "\n\n")
            f.write(content)
            
        logger.info(f"Saved scrapped content for url {url} to {output_file}")