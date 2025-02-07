from typing import List, Optional, Type, Enum
from pydantic import BaseModel, Field

class DocTypeModel(BaseModel):
    doc_type: Enum
    expalantion: str

class ProjectModel(BaseModel):
    """Project-specific model configuration"""
    name: str
    doc_type_model: Optional[Type[DocTypeModel]] = None  # If None, no validation needed
    extraction_models: dict[str, str]  # this has to be dict of doc_type to model name
