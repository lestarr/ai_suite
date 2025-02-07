from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from enum import Enum
from ai_suite.ie.models.project_models import DocTypeModel
class ChallengeStage(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    COMPLETED = "completed"
    WON = "won"

class ChallengeURLDetails(BaseModel):
    url: HttpUrl = Field(..., description="Link to the challenge webpage")
    stage: ChallengeStage = Field(..., description="The stage of the challenge")

class ChallengeWebsiteUrls(BaseModel):
    """Model for extracting challenge URLs from listing pages"""
    
    urls: List[ChallengeURLDetails] = Field(
        default=[],
        description="URLs to individual challenge pages that are currently active/open. These are the direct links to specific challenge details."
    )
  
    pages_urls: List[HttpUrl] = Field(
        default=[],
        description="URLs to additional listing pages (pagination/navigation). For example, if there's a 'Next Page' or 'Page 2' link that contains more challenge listings."
    )

class PrizePool(BaseModel):
    prize_pool: Optional[float] = Field(None, description="Total monetary prize available")
    prize_pool_currency: Optional[str] = Field(None, description="Currency of the prize pool")
    minimum_individual_prize: Optional[float] = Field(None, description="Minimum prize available for an individual")
    maximum_individual_prize: Optional[float] = Field(None, description="Maximum prize available for an individual")

class ChallengeDetails(BaseModel):
    title: str = Field(..., description="The name of the challenge")
    url: HttpUrl = Field(..., description="Link to the challenge webpage")
    organizer: str = Field(..., description="The organization running the challenge")
    prize_pool: Optional[PrizePool] = Field(None, description="Monetary prize available")
    submission_deadline: str = Field(..., description="Submission deadline in YYYY-MM-DD format")
    key_objective: str = Field(..., description="Brief summary of the challenge's goal")
    judging_criteria: Optional[List[str]] = Field(None, description="List of judging criteria")
    classification_keywords: Optional[List[str]] = Field(None, description="Define keywords, which describe the challenge's topic, industry, or sector. These are used to classify the challenge into a topic or industry category, and are used to search for similar challenges.")

class ChallengeDocTypeEnum(str, Enum):
    CHALLENGE_DETAILS = "ChallengeDetails"
    SUBMISSION_DETAILS = "SubmissionDetails"
    JUDGING_CRITERIA = "JudgingCriteria"
    OTHER = "Other"

class ChallengeDocTypeModel(DocTypeModel):
    doc_type: ChallengeDocTypeEnum = Field(..., description="Document type, describing what the document is about")



