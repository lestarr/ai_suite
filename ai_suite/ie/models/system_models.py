from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExplorationStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    EVALUATING = "evaluating" 
    EXTRACTING = "extracting"
    EXPLORING = "exploring"
    MERGING = "merging"
    COMPLETE = "complete"
    FAILED = "failed"

class ExplorationState(BaseModel):
    depth: int = 0
    parent_url: Optional[str] = None
    root_url: Optional[str] = None
    status: ExplorationStatus = ExplorationStatus.PENDING
    processed_operations: List[str] = []
    missing_fields: List[str] = []
    completeness_score: float = 0.0

class TextInfo(BaseModel):
    """Container for text content and metadata"""
    content: str
    source_url: Optional[str] = None
    path: Optional[str] = None
    extractions: List[BaseModel] = []

class InfoModel(BaseModel):
    """Container for pipeline information with exploration state"""
    urls: List[str] = []
    texts: List[TextInfo] = []
    seen_urls: List[str] = []
    enable_scraping_rerun: bool = False
    enable_extraction_rerun: bool = False
    
    # New fields for exploration
    state: ExplorationState = Field(default_factory=ExplorationState)
    sub_models: Dict[str, 'InfoModel'] = {}  # URL -> InfoModel mapping
    merged_results: Dict[str, List[BaseModel]] = Field(default_factory=dict)  # Type -> List[Extraction] mapping

