"""MultiLanguage Chatbot extending base chatbot with translation capabilities"""

from typing import Optional
from app.services.translation import translation_service
from .base import Chatbot


class MultiLanguageChatbot(Chatbot):
    """Chatbot with multilingual support (English and Tamil)"""
    
    SUPPORTED_LANGUAGES = ["en", "ta"]
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None, language: str = "en"):
        """
        Initialize multilingual chatbot
        
        Args:
            session_id: Unique session identifier
            user_id: Permanent user identifier (optional)
            language: Initial language (en or ta)
        """
        if language not in self.SUPPORTED_LANGUAGES:
            language = "en"
        
        super().__init__(session_id, user_id, language)
        self.auto_detect_language = True
    
    def handle_query(self, query: str) -> str:
        """
        Handle user query with automatic language detection
        
        Args:
            query: User message (can be in English or Tamil)
            
        Returns:
            Bot response in the detected/set language
        """
        # Auto-detect language if enabled
        if self.auto_detect_language:
            detected_lang = translation_service.detect_language(query)
            if detected_lang in self.SUPPORTED_LANGUAGES:
                self.set_language(detected_lang)
        
        # Translate input to English for processing
        english_query = self.translate_input(query)
        
        # Process with base chatbot
        # Note: We override language in parent and pass english query
        original_lang = self.language
        self.language = "en"
        response = super().handle_query(english_query)
        self.language = original_lang
        
        # Translate output to user's language
        if self.language != "en":
            response = self.translate_output(response, self.language)
        
        return response
    
    def translate_input(self, text: str) -> str:
        """
        Translate input text to English for processing
        
        Args:
            text: Input text (any supported language)
            
        Returns:
            English text
        """
        source_lang = translation_service.detect_language(text)
        if source_lang == "en":
            return text
        return translation_service.translate_input(text, source_lang)
    
    def translate_output(self, text: str, target_lang: str = "ta") -> str:
        """
        Translate output text to target language
        
        Args:
            text: English text
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if target_lang == "en":
            return text
        return translation_service.translate_output(text, target_lang)
    
    def set_auto_detect(self, enabled: bool) -> None:
        """Enable or disable automatic language detection"""
        self.auto_detect_language = enabled
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of supported languages"""
        return [
            {"code": "en", "name": "English", "native": "English"},
            {"code": "ta", "name": "Tamil", "native": "தமிழ்"}
        ]
