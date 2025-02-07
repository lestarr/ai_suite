from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from enum import Enum
class Topics(Enum):
    Challenge_list = "Challenge_list" 

n_sites = 5
class WebsiteUrls(BaseModel):
    """Model for extracted website navigation URLs."""
    main_menu: List[HttpUrl] = Field(
        default=[],
        description=f"Up to {n_sites} most important URLs from the main navigation menu",
        max_length=n_sites
    )
    linkedin_page: Optional[HttpUrl] = Field(
        default=None,
        description="URL to the company's LinkedIn profile"
    )
    team_page: Optional[HttpUrl] = Field(
        default=None,
        description="URL to the team/people page"
    )
    portfolio_page: Optional[HttpUrl] = Field(
        default=None,
        description="URL to the portfolio/investments page"
    )
    
class ChallengeWebsiteUrls(BaseModel):
    """Model for extracting challenge URLs from listing pages"""
    
    challenge_listing_urls: List[HttpUrl] = Field(
        default=[],
        description="URLs to individual challenge pages that are currently active/open. These are the direct links to specific challenge details."
    )
    
    pages_urls: List[HttpUrl] = Field(
        default=[],
        description="URLs to additional listing pages (pagination/navigation). For example, if there's a 'Next Page' or 'Page 2' link that contains more challenge listings."
    )

class ChallengeDetails(BaseModel):
    title: str = Field(..., description="The name of the challenge")
    url: HttpUrl = Field(..., description="Link to the challenge webpage")
    organizer: str = Field(..., description="The organization running the challenge")
    prize_pool: Optional[float] = Field(None, description="Total monetary prize available")
    submission_deadline: str = Field(..., description="Submission deadline in YYYY-MM-DD format")
    key_objective: str = Field(..., description="Brief summary of the challenge’s goal")
    judging_criteria: Optional[List[str]] = Field(None, description="List of judging criteria")
    tags: Optional[List[str]] = Field(None, description="Tags related to the challenge, e.g., innovation, space, safety")
    topics: Optional[List[str]] = Field(None, description="Specific topics the challenge addresses, e.g., astronaut safety, lunar exploration")
