from typing import Dict, Any, Optional
from app.models.user import User, Profile, DBUser, DBProfile
import uuid
from app.database import SessionLocal
from sqlalchemy.orm import Session

class UserProfileService:
    """Service for managing user profiles with database persistence"""
    
    def __init__(self):
        pass

    def _get_db(self) -> Session:
        return SessionLocal()
    def create_profile(self, user_id: Optional[str] = None, **kwargs) -> User:
        """
        Create a new user with profile in database
        """
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        db = self._get_db()
        try:
            db_user = DBUser(user_id=user_id)
            db_profile = DBProfile(user_id=user_id)
            
            # Special handling for full_name which is on the user model
            if "full_name" in kwargs:
                db_user.full_name = kwargs.pop("full_name")
            
            # Map annual_income to income if provided
            if "annual_income" in kwargs:
                kwargs["income"] = kwargs.pop("annual_income")
            
            # Map kwargs to profile
            for key, value in kwargs.items():
                if hasattr(db_profile, key) and value is not None:
                    setattr(db_profile, key, value)
            
            db_user.profile = db_profile
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return self._to_pydantic(db_user)
        finally:
            db.close()
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID from database"""
        db = self._get_db()
        try:
            db_user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if db_user:
                return self._to_pydantic(db_user)
            return None
        finally:
            db.close()
    
    def update_profile(self, user_id: str, **kwargs) -> Optional[User]:
        """
        Update existing user profile in database
        """
        db = self._get_db()
        try:
            db_user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if db_user is None:
                return None
            
            if db_user.profile is None:
                db_user.profile = DBProfile(user_id=user_id)
            
            # Special handling for full_name which is on the user model
            if "full_name" in kwargs:
                db_user.full_name = kwargs.pop("full_name")
            
            # Map annual_income to income if provided
            if "annual_income" in kwargs:
                kwargs["income"] = kwargs.pop("annual_income")
                
            for key, value in kwargs.items():
                if hasattr(db_user.profile, key):
                    setattr(db_user.profile, key, value)
            
            db.commit()
            db.refresh(db_user)
            return self._to_pydantic(db_user)
        finally:
            db.close()
    
    def get_or_create_user(self, user_id: str) -> User:
        """Get existing user or create new one in database"""
        user = self.get_user(user_id)
        if user:
            return user
        return self.create_profile(user_id)
    
    def update_from_entities(self, user_id: str, entities: Dict[str, Any]) -> User:
        """Update user profile from extracted NLP entities in database"""
        user = self.get_or_create_user(user_id)
        
        # Map entity names to profile fields
        field_mapping = {
            "age": "age",
            "income": "income",
            "occupation": "occupation",
            "location": "location",
            "community": "community",
            "gender": "gender",
            "is_farmer": "is_farmer",
            "is_bpl": "is_bpl",
            "has_land": "has_land",
            "land_area": "land_area",
            "area_type": "area_type",
            "family_size": "family_size"
        }
        
        updates = {}
        for entity_name, field_name in field_mapping.items():
            if entity_name in entities:
                updates[field_name] = entities[entity_name]
        
        if updates:
            return self.update_profile(user_id, **updates)
        return user
    
    def set_language(self, user_id: str, language: str) -> Optional[User]:
        """Set user's preferred language in database"""
        db = self._get_db()
        try:
            db_user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if db_user:
                db_user.language = language
                db.commit()
                return self._to_pydantic(db_user)
            return None
        finally:
            db.close()

    def _to_pydantic(self, db_user: DBUser) -> User:
        """Convert SQLAlchemy object to Pydantic object"""
        profile_data = {}
        if db_user.profile:
            p = db_user.profile
            profile_data = {
                "age": p.age,
                "income": p.income,
                "occupation": p.occupation,
                "community": p.community,
                "location": p.location,
                "gender": p.gender,
                "is_farmer": p.is_farmer,
                "has_land": p.has_land,
                "land_area": p.land_area,
                "is_bpl": p.is_bpl,
                # New fields - we can pass them in profile_data even if not in Profile model
                # Pydantic will ignore them unless we add them to Profile model
                "area_type": p.area_type,
                "family_size": p.family_size,
                "children_count": p.children_count,
                "is_disabled": p.is_disabled,
                "is_widow": p.is_widow,
                "is_senior_citizen": p.is_senior_citizen,
                "has_girl_child": p.has_girl_child
            }
            # Add full_name from DBUser to profile_data for convenience in frontend
            profile_data["full_name"] = db_user.full_name
        
        return User(
            user_id=db_user.user_id,
            language=db_user.language,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            profile=Profile(**profile_data)
        )
    
    def get_profile_summary(self, user_id: str) -> str:
        """Get human-readable profile summary"""
        user = self.get_user(user_id)
        if not user:
            return "No profile found."
        
        profile = user.profile
        parts = []
        
        if profile.age:
            parts.append(f"Age: {profile.age} years")
        if profile.income:
            parts.append(f"Annual Income: ₹{profile.income:,.0f}")
        if profile.occupation:
            parts.append(f"Occupation: {profile.occupation}")
        if profile.location:
            parts.append(f"Location: {profile.location}")
        if profile.community:
            parts.append(f"Community: {profile.community}")
        if profile.gender:
            parts.append(f"Gender: {profile.gender.title()}")
        if profile.is_farmer:
            parts.append("Farmer: Yes")
        if profile.is_bpl:
            parts.append("BPL: Yes")
        
        if not parts:
            return "Profile is empty. Please provide your details."
        
        return "\n".join(parts)
    
    def get_missing_fields(self, user_id: str) -> list:
        """Get list of missing important profile fields"""
        user = self.get_user(user_id)
        if not user:
            return ["age", "income", "location"]
        
        validation = user.profile.validate_profile()
        return validation.get("missing_fields", [])
    
    def clear_profile(self, user_id: str) -> bool:
        """Clear user profile in database"""
        db = self._get_db()
        try:
            db_user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if db_user:
                if db_user.profile:
                    db.delete(db_user.profile)
                db_user.profile = DBProfile(user_id=user_id)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user completely from database"""
        db = self._get_db()
        try:
            db_user = db.query(DBUser).filter(DBUser.user_id == user_id).first()
            if db_user:
                db.delete(db_user)
                db.commit()
                return True
            return False
        finally:
            db.close()


# Singleton instance
user_profile_service = UserProfileService()
