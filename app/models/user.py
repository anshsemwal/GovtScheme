from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class DBProfile(Base):
    """SQLAlchemy Profile model"""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True)
    
    age = Column(Integer, nullable=True)
    income = Column(Float, nullable=True)
    occupation = Column(String, nullable=True)
    community = Column(String, nullable=True)
    location = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    
    area_type = Column(String, nullable=True)
    family_size = Column(Integer, nullable=True)
    children_count = Column(Integer, nullable=True)
    is_bpl = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    is_widow = Column(Boolean, default=False)
    is_senior_citizen = Column(Boolean, default=False)
    has_girl_child = Column(Boolean, default=False)
    is_farmer = Column(Boolean, default=False)
    has_land = Column(Boolean, default=False)
    land_area = Column(Float, nullable=True)
    
    user = relationship("DBUser", back_populates="profile")

class DBUser(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = relationship("DBProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(BaseModel):
    """User profile Pydantic model"""
    full_name: Optional[str] = Field(default=None)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    income: Optional[float] = Field(default=None, ge=0)
    occupation: Optional[str] = Field(default=None)
    community: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    gender: Optional[str] = Field(default=None)
    
    area_type: Optional[str] = Field(default=None)
    family_size: Optional[int] = Field(default=None)
    children_count: Optional[int] = Field(default=None)
    
    is_farmer: Optional[bool] = Field(default=None)
    has_land: Optional[bool] = Field(default=None)
    land_area: Optional[float] = Field(default=None)
    is_bpl: Optional[bool] = Field(default=None)
    is_disabled: Optional[bool] = Field(default=None)
    is_widow: Optional[bool] = Field(default=None)
    is_senior_citizen: Optional[bool] = Field(default=None)
    has_girl_child: Optional[bool] = Field(default=None)
    
    def is_complete(self) -> bool:
        """Check if profile has minimum required fields"""
        required = [self.age, self.income, self.location]
        return all(field is not None for field in required)
    
    def validate_profile(self) -> dict:
        """Validate profile and return missing fields"""
        missing = []
        if self.age is None:
            missing.append("age")
        if self.income is None:
            missing.append("income")
        if self.location is None:
            missing.append("location")
        return {
            "is_valid": len(missing) == 0,
            "missing_fields": missing
        }
    
    def to_text(self) -> str:
        """Convert profile to text for embedding and LLM prompt"""
        parts = []
        if self.age is not None:
            parts.append(f"Age: {self.age} years")
        if self.income is not None:
            parts.append(f"Annual Income: ₹{self.income:,.0f}")
        if self.occupation:
            parts.append(f"Occupation: {self.occupation}")
        if self.community:
            parts.append(f"Community: {self.community}")
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.gender:
            parts.append(f"Gender: {self.gender}")
        if self.is_farmer:
            parts.append("Is a Farmer: Yes")
        if self.is_bpl:
            parts.append("BPL Status: Below Poverty Line")
        if self.has_land:
            parts.append(f"Owns Land: Yes ({self.land_area} hectares)" if self.land_area else "Owns Land: Yes")
            
        return " | ".join(parts) if parts else "No profile data provided"


class User(BaseModel):
    """User entity with profile"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile: Profile = Field(default_factory=Profile)
    language: str = Field(default="en", description="Preferred language (en/ta)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def create_profile(self, **kwargs) -> Profile:
        """Create or update user profile"""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        self.updated_at = datetime.now()
        return self.profile
    
    def update_profile(self, **kwargs) -> Profile:
        """Update existing profile with new values"""
        return self.create_profile(**kwargs)
