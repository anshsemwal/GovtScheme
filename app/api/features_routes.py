"""
Extended API routes for all features
- Saved Schemes, Applications, Family, Checklist, etc.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from ..database import get_db, SavedScheme, Application, FamilyMember, UserProfile, SessionLocal
from ..knowledge_base.schemes_data import schemes_data as SCHEMES

router = APIRouter()

# ============== Pydantic Models ==============

class SaveSchemeRequest(BaseModel):
    session_id: str
    scheme_id: str
    scheme_name: str
    scheme_category: Optional[str] = None
    documents_required: Optional[List[str]] = None

class ApplicationRequest(BaseModel):
    session_id: str
    scheme_id: str
    scheme_name: str
    notes: Optional[str] = None
    deadline: Optional[str] = None

class ApplicationUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class FamilyMemberRequest(BaseModel):
    session_id: str
    name: str
    relation: str
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    is_disabled: Optional[bool] = False
    is_student: Optional[bool] = False

class ProfileRequest(BaseModel):
    session_id: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    community: Optional[str] = None
    state: Optional[str] = None
    area_type: Optional[str] = None
    occupation: Optional[str] = None
    income: Optional[int] = None
    family_size: Optional[int] = None
    is_bpl: Optional[bool] = False
    is_disabled: Optional[bool] = False
    is_widow: Optional[bool] = False
    is_senior: Optional[bool] = False
    has_girl_child: Optional[bool] = False
    language: Optional[str] = 'en'


# ============== Saved Schemes ==============

@router.post("/schemes/save")
async def save_scheme(request: SaveSchemeRequest):
    """Save a scheme to user's bookmarks"""
    db = SessionLocal()
    try:
        # Check if already saved
        existing = db.query(SavedScheme).filter(
            SavedScheme.session_id == request.session_id,
            SavedScheme.scheme_id == request.scheme_id
        ).first()
        
        if existing:
            return {"success": False, "message": "Scheme already saved"}
        
        saved = SavedScheme(
            session_id=request.session_id,
            scheme_id=request.scheme_id,
            scheme_name=request.scheme_name,
            scheme_category=request.scheme_category,
            documents_required=json.dumps(request.documents_required) if request.documents_required else None
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
        
        return {"success": True, "saved": saved.to_dict()}
    finally:
        db.close()

@router.get("/schemes/saved/{session_id}")
async def get_saved_schemes(session_id: str):
    """Get all saved schemes for a session"""
    db = SessionLocal()
    try:
        schemes = db.query(SavedScheme).filter(
            SavedScheme.session_id == session_id
        ).order_by(SavedScheme.saved_at.desc()).all()
        
        return {"schemes": [s.to_dict() for s in schemes]}
    finally:
        db.close()

@router.delete("/schemes/saved/{session_id}/{scheme_id}")
async def remove_saved_scheme(session_id: str, scheme_id: str):
    """Remove a saved scheme"""
    db = SessionLocal()
    try:
        scheme = db.query(SavedScheme).filter(
            SavedScheme.session_id == session_id,
            SavedScheme.scheme_id == scheme_id
        ).first()
        
        if not scheme:
            raise HTTPException(status_code=404, detail="Saved scheme not found")
        
        db.delete(scheme)
        db.commit()
        
        return {"success": True}
    finally:
        db.close()


# ============== Applications Tracker ==============

@router.post("/applications")
async def create_application(request: ApplicationRequest):
    """Start tracking an application"""
    db = SessionLocal()
    try:
        # Check if already tracking
        existing = db.query(Application).filter(
            Application.session_id == request.session_id,
            Application.scheme_id == request.scheme_id
        ).first()
        
        if existing:
            return {"success": False, "message": "Already tracking this application", "application": existing.to_dict()}
        
        deadline = None
        if request.deadline:
            deadline = datetime.fromisoformat(request.deadline)
        
        app = Application(
            session_id=request.session_id,
            scheme_id=request.scheme_id,
            scheme_name=request.scheme_name,
            notes=request.notes,
            deadline=deadline
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        
        return {"success": True, "application": app.to_dict()}
    finally:
        db.close()

@router.get("/applications/{session_id}")
async def get_applications(session_id: str):
    """Get all applications for a session"""
    db = SessionLocal()
    try:
        apps = db.query(Application).filter(
            Application.session_id == session_id
        ).order_by(Application.updated_at.desc()).all()
        
        return {"applications": [a.to_dict() for a in apps]}
    finally:
        db.close()

@router.patch("/applications/{session_id}/{app_id}")
async def update_application(session_id: str, app_id: int, update: ApplicationUpdate):
    """Update application status"""
    db = SessionLocal()
    try:
        app = db.query(Application).filter(
            Application.id == app_id,
            Application.session_id == session_id
        ).first()
        
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if update.status not in Application.STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {Application.STATUSES}")
        
        app.status = update.status
        if update.notes:
            app.notes = update.notes
        
        db.commit()
        db.refresh(app)
        
        return {"success": True, "application": app.to_dict()}
    finally:
        db.close()

@router.get("/applications/history/{session_id}")
async def get_application_history(session_id: str):
    """Get completed applications (approved/rejected)"""
    db = SessionLocal()
    try:
        apps = db.query(Application).filter(
            Application.session_id == session_id,
            Application.status.in_(['approved', 'rejected'])
        ).order_by(Application.updated_at.desc()).all()
        
        return {"history": [a.to_dict() for a in apps]}
    finally:
        db.close()


# ============== Family Members ==============

@router.post("/family")
async def add_family_member(request: FamilyMemberRequest):
    """Add a family member"""
    db = SessionLocal()
    try:
        member = FamilyMember(
            session_id=request.session_id,
            name=request.name,
            relation=request.relation,
            age=request.age,
            gender=request.gender,
            occupation=request.occupation,
            is_disabled=request.is_disabled,
            is_student=request.is_student
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        
        return {"success": True, "member": member.to_dict()}
    finally:
        db.close()

@router.get("/family/{session_id}")
async def get_family_members(session_id: str):
    """Get all family members for a session"""
    db = SessionLocal()
    try:
        members = db.query(FamilyMember).filter(
            FamilyMember.session_id == session_id
        ).all()
        
        return {"members": [m.to_dict() for m in members]}
    finally:
        db.close()

@router.delete("/family/{session_id}/{member_id}")
async def remove_family_member(session_id: str, member_id: int):
    """Remove a family member"""
    db = SessionLocal()
    try:
        member = db.query(FamilyMember).filter(
            FamilyMember.id == member_id,
            FamilyMember.session_id == session_id
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="Family member not found")
        
        db.delete(member)
        db.commit()
        
        return {"success": True}
    finally:
        db.close()


# ============== Document Checklist ==============

@router.get("/checklist/{session_id}")
async def generate_checklist(session_id: str):
    """Generate unified document checklist from saved schemes"""
    db = SessionLocal()
    try:
        saved = db.query(SavedScheme).filter(
            SavedScheme.session_id == session_id
        ).all()
        
        if not saved:
            # Return default checklist
            return {
                "documents": [
                    {"name": "Aadhaar Card", "required_for": ["Most schemes"]},
                    {"name": "Income Certificate", "required_for": ["Income-based schemes"]},
                    {"name": "Caste Certificate", "required_for": ["SC/ST/OBC schemes"]},
                    {"name": "Bank Account Details", "required_for": ["Direct benefit transfer"]},
                    {"name": "Passport Size Photos", "required_for": ["Application forms"]},
                    {"name": "Address Proof", "required_for": ["Verification"]}
                ],
                "schemes_count": 0
            }
        
        # Collect all documents
        doc_map = {}
        for scheme in saved:
            docs = []
            if scheme.documents_required:
                try:
                    docs = json.loads(scheme.documents_required)
                except:
                    docs = []
            
            for doc in docs:
                if doc not in doc_map:
                    doc_map[doc] = []
                doc_map[doc].append(scheme.scheme_name)
        
        documents = [
            {"name": doc, "required_for": schemes}
            for doc, schemes in doc_map.items()
        ]
        
        return {
            "documents": documents,
            "schemes_count": len(saved)
        }
    finally:
        db.close()


# ============== User Profile (Database-backed) ==============

@router.post("/profile/save")
async def save_profile(request: ProfileRequest):
    """Save or update user profile in database"""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.session_id == request.session_id
        ).first()
        
        if profile:
            # Update existing
            for key, value in request.dict(exclude={'session_id'}).items():
                if value is not None:
                    setattr(profile, key, value)
        else:
            # Create new
            profile = UserProfile(
                session_id=request.session_id,
                **request.dict(exclude={'session_id'})
            )
            db.add(profile)
        
        db.commit()
        db.refresh(profile)
        
        return {"success": True, "profile": profile.to_dict()}
    finally:
        db.close()

@router.get("/profile/{session_id}")
async def get_profile(session_id: str):
    """Get user profile from database"""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.session_id == session_id
        ).first()
        
        if not profile:
            return {"profile": None}
        
        return {"profile": profile.to_dict()}
    finally:
        db.close()


# ============== Scheme Comparison ==============

@router.get("/schemes/compare")
async def compare_schemes(scheme_ids: str):
    """Compare multiple schemes side by side"""
    ids = scheme_ids.split(',')
    
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 schemes to compare")
    
    if len(ids) > 4:
        raise HTTPException(status_code=400, detail="Can compare maximum 4 schemes")
    
    schemes = []
    for scheme_id in ids:
        scheme = next((s for s in SCHEMES if s.scheme_id == scheme_id.strip()), None)
        if scheme:
            schemes.append({
                "id": scheme.scheme_id,
                "name": scheme.name,
                "category": scheme.category,
                "benefits": scheme.benefits,
                "eligibility": {
                    "max_income": scheme.eligibility_criteria.max_income,
                    "min_age": scheme.eligibility_criteria.min_age,
                    "max_age": scheme.eligibility_criteria.max_age,
                    "gender": scheme.eligibility_criteria.gender,
                    "communities": scheme.eligibility_criteria.communities
                },
                "documents": scheme.documents_required,
                "application_process": scheme.application_process
            })
    
    return {"schemes": schemes}


# ============== CSC Finder ==============

@router.get("/csc/states")
async def get_csc_states():
    """Get list of states with CSC center info"""
    states = [
        {"name": "Andhra Pradesh", "csc_portal": "https://ap.csc.gov.in"},
        {"name": "Bihar", "csc_portal": "https://bihar.csc.gov.in"},
        {"name": "Gujarat", "csc_portal": "https://gujarat.csc.gov.in"},
        {"name": "Karnataka", "csc_portal": "https://karnataka.csc.gov.in"},
        {"name": "Kerala", "csc_portal": "https://kerala.csc.gov.in"},
        {"name": "Madhya Pradesh", "csc_portal": "https://mp.csc.gov.in"},
        {"name": "Maharashtra", "csc_portal": "https://maharashtra.csc.gov.in"},
        {"name": "Rajasthan", "csc_portal": "https://rajasthan.csc.gov.in"},
        {"name": "Tamil Nadu", "csc_portal": "https://tn.csc.gov.in"},
        {"name": "Uttar Pradesh", "csc_portal": "https://up.csc.gov.in"},
        {"name": "West Bengal", "csc_portal": "https://wb.csc.gov.in"}
    ]
    return {
        "states": states,
        "locator_url": "https://locator.csccloud.in/"
    }


# ============== Supported Languages ==============

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported Indian languages"""
    return {
        "languages": [
            {"code": "en", "name": "English", "native": "English", "speech_code": "en-IN"},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी", "speech_code": "hi-IN"},
            {"code": "ta", "name": "Tamil", "native": "தமிழ்", "speech_code": "ta-IN"},
            {"code": "te", "name": "Telugu", "native": "తెలుగు", "speech_code": "te-IN"},
            {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ", "speech_code": "kn-IN"},
            {"code": "ml", "name": "Malayalam", "native": "മലയാളം", "speech_code": "ml-IN"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা", "speech_code": "bn-IN"},
            {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી", "speech_code": "gu-IN"},
            {"code": "mr", "name": "Marathi", "native": "मराठी", "speech_code": "mr-IN"},
            {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ", "speech_code": "pa-IN"},
            {"code": "or", "name": "Odia", "native": "ଓଡ଼ିଆ", "speech_code": "or-IN"}
        ]
    }
