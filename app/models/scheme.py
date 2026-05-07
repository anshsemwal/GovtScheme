"""Government Scheme model"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class EligibilityCriteria(BaseModel):
    """Eligibility criteria for a scheme"""
    min_age: Optional[int] = Field(default=None, description="Minimum age requirement")
    max_age: Optional[int] = Field(default=None, description="Maximum age requirement")
    max_income: Optional[float] = Field(default=None, description="Maximum income limit")
    min_income: Optional[float] = Field(default=None, description="Minimum income requirement")
    communities: Optional[List[str]] = Field(default=None, description="Eligible communities")
    locations: Optional[List[str]] = Field(default=None, description="Eligible states/districts")
    occupations: Optional[List[str]] = Field(default=None, description="Eligible occupations")
    gender: Optional[str] = Field(default=None, description="Required gender")
    is_farmer_required: Optional[bool] = Field(default=None, description="Must be a farmer")
    is_bpl_required: Optional[bool] = Field(default=None, description="Must be BPL")
    has_land_required: Optional[bool] = Field(default=None, description="Must own land")
    max_land_area: Optional[float] = Field(default=None, description="Maximum land area")


class Scheme(BaseModel):
    """Government scheme entity"""
    scheme_id: str = Field(description="Unique scheme identifier")
    name: str = Field(description="Scheme name")
    name_tamil: Optional[str] = Field(default=None, description="Scheme name in Tamil")
    description: str = Field(description="Detailed description")
    description_tamil: Optional[str] = Field(default=None, description="Description in Tamil")
    eligibility_criteria: EligibilityCriteria = Field(default_factory=EligibilityCriteria)
    benefits: str = Field(description="Benefits provided by the scheme")
    benefits_tamil: Optional[str] = Field(default=None, description="Benefits in Tamil")
    documents_required: List[str] = Field(default_factory=list, description="Required documents")
    application_process: str = Field(default="", description="How to apply")
    source: str = Field(default="Government of India", description="Source authority")
    category: str = Field(default="General", description="Scheme category")
    is_active: bool = Field(default=True, description="Whether scheme is active")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_details(self, language: str = "en") -> Dict[str, Any]:
        """Get scheme details in specified language"""
        if language == "ta" and self.name_tamil:
            return {
                "scheme_id": self.scheme_id,
                "name": self.name_tamil,
                "description": self.description_tamil or self.description,
                "benefits": self.benefits_tamil or self.benefits,
                "documents_required": self.documents_required,
                "application_process": self.application_process,
                "source": self.source,
                "category": self.category
            }
        return {
            "scheme_id": self.scheme_id,
            "name": self.name,
            "description": self.description,
            "benefits": self.benefits,
            "documents_required": self.documents_required,
            "application_process": self.application_process,
            "source": self.source,
            "category": self.category
        }
    
    def to_embedding_text(self) -> str:
        """Convert scheme to text for embedding generation"""
        criteria = self.eligibility_criteria
        parts = [
            f"Scheme: {self.name}",
            f"Description: {self.description}",
            f"Benefits: {self.benefits}",
            f"Category: {self.category}"
        ]
        
        if criteria.max_income:
            parts.append(f"Maximum income: {criteria.max_income}")
        if criteria.communities:
            parts.append(f"Communities: {', '.join(criteria.communities)}")
        if criteria.is_farmer_required:
            parts.append("For farmers")
        if criteria.is_bpl_required:
            parts.append("For BPL families")
        if criteria.min_age or criteria.max_age:
            age_range = f"Age: {criteria.min_age or 0}-{criteria.max_age or 100}"
            parts.append(age_range)
            
        return " | ".join(parts)
