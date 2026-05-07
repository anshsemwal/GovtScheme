"""API routes for the Government Schemes Recommendation API"""

from typing import Optional
from fastapi import APIRouter, HTTPException
import uuid

from app import __version__
from app.chatbot.multilingual import MultiLanguageChatbot
from app.services.nlp_engine import nlp_engine
from app.services.user_profile import user_profile_service
from app.services.eligibility import eligibility_validator
from app.services.rag_pipeline import rag_pipeline
from app.knowledge_base.schemes_data import get_all_schemes, get_scheme_by_id
from app.chatbot.dialogue_manager import dialogue_manager

from .schemas import (
    ChatRequest,
    ChatResponse,
    ProfileRequest,
    ProfileResponse,
    SchemeResponse,
    SchemeInfo,
    EligibilityRequest,
    EligibilityResponse,
    EligibilityResult,
    HealthResponse
)

router = APIRouter()

# Store chatbot instances per session
chatbots: dict = {}


def get_chatbot(session_id: str, user_id: Optional[str] = None, language: str = "en") -> MultiLanguageChatbot:
    """Get or create chatbot instance for session"""
    if session_id not in chatbots:
        chatbots[session_id] = MultiLanguageChatbot(session_id, user_id, language)
    return chatbots[session_id]


from fastapi import Header
from app.services.auth import decode_access_token

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    Main chat endpoint for conversational interaction
    """
    session_id = request.session_id or str(uuid.uuid4())
    language = "en"
    
    # Try to extract user_id from token if provided
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
    
    # Get or create chatbot with optional permanent user_id
    chatbot = get_chatbot(session_id, user_id, language)
    
    # Detect intent and entities for response metadata
    intent, confidence = nlp_engine.detect_intent(request.message)
    entities = nlp_engine.extract_entities(request.message)
    
    # Update profile from context if provided (Sync frontend state with chatbot)
    if request.context:
        profile_update = request.context.copy()
        
        # Map frontend 'state' to backend 'location'
        if "state" in profile_update and not profile_update.get("location"):
            profile_update["location"] = profile_update["state"]
            
        # Ensure numeric types
        try:
            if profile_update.get("income"):
                profile_update["income"] = float(profile_update["income"])
            if profile_update.get("age"):
                profile_update["age"] = int(profile_update["age"])
        except (ValueError, TypeError):
            pass
            
        # Update the intuitive profile service
        # Ensure user exists in memory first
        user_profile_service.get_or_create_user(session_id) 
        user_profile_service.update_profile(session_id, **profile_update)
    
    # Process message
    response_text = chatbot.handle_query(request.message)
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        language=chatbot.language,
        detected_intent=intent.value,
        extracted_entities=entities if entities else None,
        recommendations=getattr(chatbot, "last_recommendations", None)
    )


@router.post("/profile", response_model=ProfileResponse)
async def update_profile(request: ProfileRequest):
    """
    Update user profile directly
    """
    # Use service to update with persistence
    update_data = request.model_dump(exclude={'session_id', 'language'}, exclude_none=True)
    user = user_profile_service.update_profile(request.session_id, **update_data)
    
    if not user:
        # User doesn't exist yet, create it
        user = user_profile_service.create_profile(request.session_id, **update_data)
    
    if request.language:
        user_profile_service.set_language(request.session_id, request.language)
    
    validation = user.profile.validate_profile()
    
    return ProfileResponse(
        session_id=request.session_id,
        profile=user.profile.model_dump(),
        is_complete=validation["is_valid"],
        missing_fields=validation["missing_fields"]
    )


@router.get("/profile/{session_id}", response_model=ProfileResponse)
async def get_profile(session_id: str):
    """Get user profile for session"""
    user = user_profile_service.get_user(session_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    validation = user.profile.validate_profile()
    
    return ProfileResponse(
        session_id=session_id,
        profile=user.profile.model_dump(),
        is_complete=validation["is_valid"],
        missing_fields=validation["missing_fields"]
    )


@router.get("/schemes", response_model=SchemeResponse)
async def get_schemes(category: Optional[str] = None, language: str = "en"):
    """
    Get all available government schemes
    
    - Optional category filter
    - Supports English and Tamil responses
    """
    all_schemes = get_all_schemes()
    
    if category:
        all_schemes = [s for s in all_schemes if s.category.lower() == category.lower()]
    
    scheme_list = []
    for scheme in all_schemes:
        details = scheme.get_details(language)
        scheme_list.append(SchemeInfo(
            scheme_id=scheme.scheme_id,
            name=details["name"],
            description=details["description"],
            benefits=details["benefits"],
            category=details["category"],
            documents_required=details["documents_required"],
            application_process=details["application_process"],
            source=details["source"]
        ))
    
    return SchemeResponse(
        schemes=scheme_list,
        total_count=len(scheme_list)
    )


@router.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str, language: str = "en"):
    """Get details of a specific scheme"""
    scheme = get_scheme_by_id(scheme_id)
    
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    
    return scheme.get_details(language)


@router.post("/schemes/recommend")
async def recommend_schemes(
    session_id: str,
    query: str = "recommend schemes",
    k: int = 5,
    language: str = "en"
):
    """
    Get personalized scheme recommendations based on user profile
    
    - Uses RAG pipeline for intelligent matching
    - Considers eligibility criteria
    """
    user = user_profile_service.get_user(session_id)
    profile = user.profile if user else None
    
    # Initialize RAG pipeline
    rag_pipeline.initialize()
    
    # Get recommendations
    results = rag_pipeline.retrieve_context(query, profile, k=k)
    
    recommendations = []
    for result in results:
        scheme = result["scheme"]
        eligibility = result.get("eligibility", {})
        
        recommendations.append({
            "scheme": scheme.get_details(language),
            "score": result["score"],
            "is_eligible": eligibility.get("is_eligible") if eligibility else None,
            "met_criteria": eligibility.get("met_criteria", []) if eligibility else [],
            "unmet_criteria": eligibility.get("unmet_criteria", []) if eligibility else []
        })
    
    return {
        "session_id": session_id,
        "recommendations": recommendations,
        "total_count": len(recommendations)
    }


@router.post("/eligibility/check", response_model=EligibilityResponse)
async def check_eligibility(request: EligibilityRequest):
    """
    Check eligibility for government schemes
    
    - Can check specific scheme or all schemes
    - Returns detailed eligibility breakdown
    """
    user = user_profile_service.get_user(request.session_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found. Please create a profile first.")
    
    profile = user.profile
    results = []
    
    if request.scheme_id:
        # Check specific scheme
        scheme = get_scheme_by_id(request.scheme_id)
        if not scheme:
            raise HTTPException(status_code=404, detail="Scheme not found")
        
        is_eligible, met, unmet = eligibility_validator.validate_eligibility(profile, scheme)
        score = eligibility_validator.get_eligibility_score(profile, scheme)
        
        results.append(EligibilityResult(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.name,
            is_eligible=is_eligible,
            score=score,
            met_criteria=met,
            unmet_criteria=unmet
        ))
    else:
        # Check all schemes
        for scheme in get_all_schemes():
            is_eligible, met, unmet = eligibility_validator.validate_eligibility(profile, scheme)
            score = eligibility_validator.get_eligibility_score(profile, scheme)
            
            results.append(EligibilityResult(
                scheme_id=scheme.scheme_id,
                scheme_name=scheme.name,
                is_eligible=is_eligible,
                score=score,
                met_criteria=met,
                unmet_criteria=unmet
            ))
        
        # Sort by eligibility score
        results.sort(key=lambda x: (x.is_eligible, x.score), reverse=True)
    
    return EligibilityResponse(
        session_id=request.session_id,
        results=results
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=__version__,
        schemes_count=len(get_all_schemes()),
        active_sessions=len(dialogue_manager.get_all_sessions())
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear session data"""
    dialogue_manager.clear_session(session_id)
    user_profile_service.delete_user(session_id)
    
    if session_id in chatbots:
        del chatbots[session_id]
    
    return {"message": "Session cleared", "session_id": session_id}



