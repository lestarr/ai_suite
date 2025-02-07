from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List
from enum import Enum
from ai_suite.ie.models.project_models import DocTypeModel

class ClubURLDiscovery(BaseModel):
    url: HttpUrl = Field(..., description="URL to the club's website")
    club_name: str

class ClubContact(BaseModel):
    club_name: str
    official_designation: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    level_of_play: Optional[str] = None
    membership_size: Optional[int] = None
    website: Optional[str] = None
    affiliated_fa: Optional[str] = None

class ClubContactList(BaseModel):
    contacts: List[ClubContact] = Field(..., description="List of clubs with their contacts")

class ClubContactEnum(str, Enum):
    CLUB_CONTACT = "ClubContact"
    OTHER = "Other"

class ClubContactDocType(DocTypeModel):
    doc_type: ClubContactEnum

