"""Pydantic schemas for API requests and responses"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(description="User message text")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")
    language: Optional[str] = Field(default="en", description="Preferred language (en/ta)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="User context (profile data)")


class ChatResponse(BaseModel):
    """Chat response"""
    response: str = Field(description="Bot response text")
    session_id: str = Field(description="Session ID")
    language: str = Field(description="Response language")
    detected_intent: Optional[str] = Field(default=None, description="Detected user intent")
    extracted_entities: Optional[Dict[str, Any]] = Field(default=None, description="Extracted entities")
    recommendations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Recommended schemes structured data")


class ProfileRequest(BaseModel):
    """User profile update request"""
    session_id: str = Field(description="Session ID")
    full_name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=120)
    gender: Optional[str] = None
    community: Optional[str] = None
    location: Optional[str] = None
    area_type: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    family_size: Optional[int] = None
    children_count: Optional[int] = None
    is_bpl: Optional[bool] = None
    is_disabled: Optional[bool] = None
    is_widow: Optional[bool] = None
    is_senior_citizen: Optional[bool] = None
    has_girl_child: Optional[bool] = None
    language: Optional[str] = Field(default="en")


class ProfileResponse(BaseModel):
    """User profile response"""
    session_id: str
    profile: Dict[str, Any]
    is_complete: bool
    missing_fields: List[str]


class SchemeInfo(BaseModel):
    """Scheme information"""
    scheme_id: str
    name: str
    description: str
    benefits: str
    category: str
    documents_required: List[str]
    application_process: str
    source: str


class SchemeResponse(BaseModel):
    """Scheme recommendation response"""
    schemes: List[SchemeInfo]
    total_count: int


class EligibilityRequest(BaseModel):
    """Eligibility check request"""
    session_id: str = Field(description="Session ID for user profile")
    scheme_id: Optional[str] = Field(default=None, description="Specific scheme ID to check")


class EligibilityResult(BaseModel):
    """Single scheme eligibility result"""
    scheme_id: str
    scheme_name: str
    is_eligible: bool
    score: float
    met_criteria: List[str]
    unmet_criteria: List[str]


class EligibilityResponse(BaseModel):
    """Eligibility check response"""
    session_id: str
    results: List[EligibilityResult]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    schemes_count: int
    active_sessions: int
