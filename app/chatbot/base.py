"""Base Chatbot class"""

from typing import Dict, Any, Optional
import uuid

from app.models.interaction import DialogueState
from app.services.nlp_engine import nlp_engine, Intent
from app.services.rag_pipeline import rag_pipeline
from app.services.eligibility import eligibility_validator
from app.services.user_profile import user_profile_service
from app.services.translation import translation_service
from app.knowledge_base.schemes_data import get_scheme_by_id, get_all_schemes
from .dialogue_manager import dialogue_manager


class Chatbot:
    """Base chatbot class for handling user queries"""
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None, language: str = "en"):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.language = language
        
        # Initialize session
        self.session = dialogue_manager.get_or_create_session(self.session_id, language)
        
        # Initialize RAG pipeline
        rag_pipeline.initialize()
        
        # State for interactive responses
        self.last_recommendations = []
    
    def handle_query(self, query: str) -> str:
        """
        Main method to handle user query
        
        Args:
            query: User message text
            
        Returns:
            Bot response text
        """
        # Add user message to history
        dialogue_manager.add_user_message(self.session_id, query)
        
        # Clear previous recommendations
        self.last_recommendations = []
        
        # Detect intent
        intent, confidence = nlp_engine.detect_intent(query)
        
        # Extract entities
        entities = nlp_engine.extract_entities(query)
        
        # Update user profile with extracted entities
        if entities:
            user_profile_service.update_from_entities(self.user_id or self.session_id, entities)
            self.session.add_extracted_entities(entities)
        
        # Get current user profile
        user = user_profile_service.get_or_create_user(self.user_id or self.session_id)
        profile = user.profile
        
        # Generate response based on intent
        response = self._process_intent(intent, query, profile, entities)
        
        # Add assistant message to history
        dialogue_manager.add_assistant_message(self.session_id, response)
        
        return response
    
    def _process_intent(
        self, 
        intent: Intent, 
        query: str, 
        profile, 
        entities: Dict[str, Any]
    ) -> str:
        """Process intent and generate response with AI-first priority"""
        
        # 1. Handle hardcoded structural commands first
        if intent == Intent.GREETING:
            return self._handle_greeting()
        
        elif intent == Intent.HELP:
            return self._handle_help()
        
        # 2. For everything else (RAG, Details, Recommendations, Random questions like 2+2):
        # We use the RAG pipeline because it now has the smarts to skip database 
        # and use LLM knowledge for anything it doesn't find in the vector store.
        
        # Update context if it was a profile provider info
        if intent == Intent.PROVIDE_INFO:
            user_profile_service.update_from_entities(self.user_id or self.session_id, entities)
        
        # Get context from RAG
        results = rag_pipeline.retrieve_context(query, profile, k=5)
        
        # Get conversation history
        history = dialogue_manager.get_conversation_history(self.session_id, limit=5)
        
        # Generate response
        # This will now answer math, general facts, OR specific schemes naturally
        response = rag_pipeline.generate_response(query, results, profile, self.language, history=history)
        
        # Store recommendations in session for frontend/metadata usage
        if results:
            scheme_ids = [r["scheme"].scheme_id for r in results]
            self.last_recommendations = [
                {
                    "scheme_id": r["scheme"].scheme_id,
                    "scheme_name": r["scheme"].name,
                    "category": r["scheme"].category
                } for r in results[:3]
            ]
            dialogue_manager.update_context(self.session_id, last_recommended_schemes=scheme_ids)
            
        return response
    
    def _handle_greeting(self) -> str:
        """Handle greeting intent"""
        self.session.update_state(DialogueState.GREETING)
        return translation_service.get_greeting(self.language)
    
    def _handle_help(self) -> str:
        """Handle help request"""
        help_text = {
            "en": "I am CivicScheme AI. Tell me about yourself or ask about any government scheme.",
            "ta": "நான் ஸ்கீம்ஸ் ஏஐ. உங்களைப் பற்றி சொல்லுங்கள் அல்லது ஏதேனும் அரசுத் திட்டத்தைப் பற்றி கேளுங்கள்."
        }
        return help_text.get(self.language, help_text["en"])
    
    def _handle_profile_update(self, entities: Dict[str, Any], profile) -> str:
        """Handle profile information update"""
        if not entities:
            return self._ask_for_profile_info({})
        
        self.session.update_state(DialogueState.COLLECTING_PROFILE)
        
        # Build confirmation message
        profile_summary = user_profile_service.get_profile_summary(self.user_id or self.session_id)
        missing = user_profile_service.get_missing_fields(self.user_id or self.session_id)
        
        # Get the updated profile (entities were already applied)
        user = user_profile_service.get_or_create_user(self.user_id or self.session_id)
        profile = user.profile
        
        # Check if we now have enough info to recommend (at least 2 fields)
        filled_count = sum([
            profile.age is not None,
            profile.income is not None,
            profile.location is not None,
            profile.occupation is not None
        ])
        
        if filled_count >= 2:
            # Have enough for recommendations - Don't ask, just give recommendations!
            # The user provided info, they WANT recommendations.
            
            # Get recommendations directly
            results = rag_pipeline.retrieve_context("recommend schemes based on my profile", profile, k=5)
            
            # Get conversation history
            history = dialogue_manager.get_conversation_history(self.session_id, limit=5)

            # Generate personalized response using LLM which handles language naturally
            recommendations = rag_pipeline.generate_response(
                query=f"I have updated my profile: {profile_summary}. Please recommend schemes or acknowledge the update.",
                context=results,
                profile=profile,
                language=self.language,
                history=history
            )
            return recommendations
        
        else:
            # Need more info
            # Use LLM to ask for missing info naturally in target language
            missing_str = ", ".join(missing)
            
            # No context needed for this simple request, but we use generate_response to handle language
            # We pass a dummy context or just use the system prompt logic for "no schemes found" but adapted
            # Actually, simpler to just use the LLM to format the "missing info" request
            
            prompt = f"The user provided some info but I need more: {missing_str}. Current profile: {profile_summary}."
            
            # To avoid complexity, we can use a simple RAG call with empty context but specific query
            # OR just return a simple formatted string if we want to be safe, but user asked for "no repetition"
            
            # Get conversation history
            history = dialogue_manager.get_conversation_history(self.session_id, limit=5)

            # Let's try to get a recommendation anyway with what we have, even if incomplete
            results = rag_pipeline.retrieve_context("recommend schemes", profile, k=3)
            response = rag_pipeline.generate_response(
                query=f"I updated my profile. Missing: {missing_str}. Recommend if possible or ask for missing info.",
                context=results,
                profile=profile,
                language=self.language,
                history=history
            )
            return response
            
            return response
    
    def _handle_recommendations(self, query: str, profile) -> str:
        """Handle scheme recommendation request"""
        self.session.update_state(DialogueState.RECOMMENDING)
        
        # Check if profile is complete enough - but still process query even without profile
        has_profile = profile.age or profile.income or profile.location
        
        # Get recommendations from RAG pipeline using the ACTUAL USER QUERY
        # This ensures semantic search finds relevant schemes based on what user asked
        results = rag_pipeline.retrieve_context(query, profile if has_profile else None, k=5)
        
        # Store scheme IDs in context for later reference
        scheme_ids = [r["scheme"].scheme_id for r in results]
        
        # Store full structured recommendations for API response
        self.last_recommendations = []
        for r in results:
            scheme = r["scheme"]
            self.last_recommendations.append({
                "scheme_id": scheme.scheme_id,
                "scheme_name": scheme.name,
                "category": scheme.category,
                "description": scheme.description,
                "documents": scheme.documents_required
            })
            
        dialogue_manager.update_context(self.session_id, last_recommended_schemes=scheme_ids)
        
        # Get conversation history
        history = dialogue_manager.get_conversation_history(self.session_id, limit=5)

        # Generate response
        response = rag_pipeline.generate_response(query, results, profile, self.language, history=history)
        
        return response
    
    def _handle_eligibility_check(self, query: str, profile) -> str:
        """Handle eligibility check request"""
        self.session.update_state(DialogueState.CHECKING_ELIGIBILITY)
        
        # Try to extract scheme name from query
        scheme_name = nlp_engine.extract_scheme_name(query)
        
        if scheme_name:
            # Find specific scheme
            for scheme in get_all_schemes():
                if scheme_name.lower() in scheme.name.lower():
                    is_eligible, met, unmet = eligibility_validator.validate_eligibility(
                        profile, scheme
                    )
                    return eligibility_validator.format_eligibility_result(
                        scheme, is_eligible, met, unmet, self.language
                    )
        
        # No specific scheme - check all and show eligible ones
        eligible_schemes = []
        partial_schemes = []
        
        for scheme in get_all_schemes():
            is_eligible, met, unmet = eligibility_validator.validate_eligibility(
                profile, scheme
            )
            if is_eligible:
                eligible_schemes.append(scheme.name)
            elif len(met) > len(unmet):
                partial_schemes.append(scheme.name)
        
        if self.language == "ta":
            if eligible_schemes:
                response = "✅ நீங்கள் இந்த திட்டங்களுக்கு தகுதியானவர்:\n"
                response += "\n".join(f"• {s}" for s in eligible_schemes)
            else:
                response = "உங்கள் சுயவிவரத்தின் அடிப்படையில் தகுதியான திட்டங்கள் இல்லை."
        else:
            if eligible_schemes:
                response = "✅ You are eligible for these schemes:\n"
                response += "\n".join(f"• {s}" for s in eligible_schemes)
            else:
                response = "Based on your profile, no schemes match all eligibility criteria."
            
            if partial_schemes:
                response += "\n\n⚠️ You may be partially eligible for:\n"
                response += "\n".join(f"• {s}" for s in partial_schemes[:3])
        
        return response
    
    def _handle_application_guidance(self, query: str) -> str:
        """Handle application guidance request"""
        self.session.update_state(DialogueState.PROVIDING_GUIDANCE)
        
        scheme_name = nlp_engine.extract_scheme_name(query)
        
        if scheme_name:
            for scheme in get_all_schemes():
                if scheme_name.lower() in scheme.name.lower():
                    return eligibility_validator.get_application_guidance(scheme, self.language)
        
        # Generic guidance
        if self.language == "ta":
            return "எந்த திட்டத்திற்கு விண்ணப்பிக்க விரும்புகிறீர்கள்? திட்டத்தின் பெயரைக் குறிப்பிடவும்."
        return "Which scheme would you like to apply for? Please mention the scheme name."
    
    def _handle_document_checklist(self, query: str) -> str:
        """Handle document checklist request"""
        scheme_name = nlp_engine.extract_scheme_name(query)
        
        if scheme_name:
            for scheme in get_all_schemes():
                if scheme_name.lower() in scheme.name.lower():
                    docs = scheme.documents_required
                    if self.language == "ta":
                        response = f"**{scheme.name_tamil or scheme.name}** திட்டத்திற்கு தேவையான ஆவணங்கள்:\n\n"
                    else:
                        response = f"**Documents required for {scheme.name}:**\n\n"
                    response += "\n".join(f"• {doc}" for doc in docs)
                    return response
        
        if self.language == "ta":
            return "எந்த திட்டத்திற்கு ஆவணங்கள் தேவை? திட்டத்தின் பெயரைக் குறிப்பிடவும்."
        return "Which scheme do you need documents for? Please mention the scheme name."
    
    def _handle_scheme_details(self, query: str, profile) -> str:
        """Handle request for scheme details (e.g., 'tell me about scheme 3')"""
        
        # First try to extract scheme number
        scheme_number = nlp_engine.extract_scheme_number(query)
        scheme_to_describe = None
        
        if scheme_number:
            # Get the last recommended schemes from context
            context = dialogue_manager.get_context(self.session_id)
            last_schemes = context.get("last_recommended_schemes", [])
            
            if last_schemes and 1 <= scheme_number <= len(last_schemes):
                scheme_id = last_schemes[scheme_number - 1]
                scheme_to_describe = get_scheme_by_id(scheme_id)
            else:
                # Fallback: get from all schemes
                all_schemes = get_all_schemes()
                if 1 <= scheme_number <= len(all_schemes):
                    scheme_to_describe = all_schemes[scheme_number - 1]
        
        # If no number, try to find by name
        if not scheme_to_describe:
            scheme_name = nlp_engine.extract_scheme_name(query)
            if scheme_name:
                for scheme in get_all_schemes():
                    if scheme_name.lower() in scheme.name.lower():
                        scheme_to_describe = scheme
                        break
        
        if not scheme_to_describe:
            if self.language == "ta":
                return "எந்த திட்டத்தைப் பற்றி தெரிந்துகொள்ள விரும்புகிறீர்கள்? திட்டத்தின் பெயரை அல்லது எண்ணைக் குறிப்பிடவும்."
            return "Which scheme would you like to know about? Please mention the scheme name or number (e.g., 'scheme 1', 'scheme 2')."
        
        # Generate detailed response
        return self._generate_scheme_detail_response(scheme_to_describe, profile)
    
    def _generate_scheme_detail_response(self, scheme, profile) -> str:
        """Generate detailed response about a scheme"""
        
        # Get eligibility info
        is_eligible, met_criteria, unmet_criteria = eligibility_validator.validate_eligibility(
            profile, scheme
        )
        
        # Build detailed response
        name = scheme.name_tamil if self.language == "ta" and scheme.name_tamil else scheme.name
        desc = scheme.description_tamil if self.language == "ta" and scheme.description_tamil else scheme.description
        benefits = scheme.benefits_tamil if self.language == "ta" and scheme.benefits_tamil else scheme.benefits
        
        if self.language == "ta":
            response = f"## {name}\n\n"
            response += f"**விளக்கம்:** {desc}\n\n"
            response += f"**சலுகைகள்:** {benefits}\n\n"
            
            if is_eligible:
                response += "✅ **உங்கள் தகுதி நிலை:** நீங்கள் தகுதியானவர்!\n\n"
            else:
                response += "⚠️ **உங்கள் தகுதி நிலை:** சில நிபந்தனைகள் பூர்த்தியாகவில்லை\n"
                if unmet_criteria:
                    response += "• " + "\n• ".join(unmet_criteria) + "\n\n"
            
            response += "**தேவையான ஆவணங்கள்:**\n"
            for doc in scheme.documents_required:
                response += f"• {doc}\n"
            
            response += f"\n**விண்ணப்பிக்கும் முறை:** {scheme.application_process}\n"
            response += f"\n**மூலம்:** {scheme.source}"
        else:
            response = f"## {name}\n\n"
            response += f"**Description:** {desc}\n\n"
            response += f"**Benefits:** {benefits}\n\n"
            
            if is_eligible:
                response += "✅ **Your Eligibility:** You are eligible for this scheme!\n\n"
            else:
                response += "⚠️ **Your Eligibility:** Some criteria not met\n"
                if unmet_criteria:
                    response += "• " + "\n• ".join(unmet_criteria) + "\n\n"
            
            response += "**Documents Required:**\n"
            for doc in scheme.documents_required:
                response += f"• {doc}\n"
            
            response += f"\n**How to Apply:** {scheme.application_process}\n"
            response += f"\n**Source:** {scheme.source}"
        
        return response

    
    def _ask_for_profile_info(self, current_entities: Dict[str, Any]) -> str:
        """Ask user for missing profile information"""
        self.session.update_state(DialogueState.COLLECTING_PROFILE)
        
        missing = user_profile_service.get_missing_fields(self.session_id)
        
        if not missing:
            if self.language == "ta":
                return "உங்கள் சுயவிவரம் பூர்த்தியானது! திட்டங்களை பரிந்துரைக்கவா?"
            return "Your profile is complete! Would you like me to recommend schemes?"
        
        # Ask for first missing field
        first_missing = missing[0]
        question = translation_service.get_profile_question(first_missing, self.language)
        
        if self.language == "ta":
            prompt = "திட்டங்களை பரிந்துரைக்க, சில தகவல்கள் தேவை.\n\n"
        else:
            prompt = "To recommend schemes, I need some information.\n\n"
        
        return prompt + question
    
    def manage_dialogue(self) -> DialogueState:
        """Get current dialogue state"""
        return self.session.state
    
    def set_language(self, language: str) -> None:
        """Set conversation language"""
        self.language = language
        dialogue_manager.set_language(self.session_id, language)
        user_profile_service.set_language(self.session_id, language)
    
    def get_profile_summary(self) -> str:
        """Get current user profile summary"""
        return user_profile_service.get_profile_summary(self.user_id or self.session_id)
    
    def reset(self) -> None:
        """Reset conversation and profile"""
        dialogue_manager.clear_session(self.session_id)
        user_profile_service.clear_profile(self.user_id or self.session_id)
        self.session = dialogue_manager.get_or_create_session(self.session_id, self.language)
