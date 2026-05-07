"""Translation service for english-tamil multilingual support"""

from typing import Optional, Dict
import re
import logging
import requests
from deep_translator import GoogleTranslator
from app.config import settings

logger = logging.getLogger(__name__)

class TranslationService:
    """Translation service supporting English and Tamil"""
    
    def __init__(self):
        self.supported_languages = ["en", "ta", "hi", "te", "kn", "ml", "bn", "gu", "mr", "pa", "or"]
        
        # Common phrases dictionary for basic translation
        # In production, use Google Cloud Translation API
        self.en_to_ta = {
            # Greetings
            "hello": "வணக்கம்",
            "hi": "வணக்கம்",
            "welcome": "வரவேற்கிறோம்",
            "thank you": "நன்றி",
            "thanks": "நன்றி",
            "goodbye": "பிரியாவிடை",
            "yes": "ஆம்",
            "no": "இல்லை",
            
            # Common words
            "scheme": "திட்டம்",
            "schemes": "திட்டங்கள்",
            "government": "அரசு",
            "eligible": "தகுதியான",
            "eligibility": "தகுதி",
            "apply": "விண்ணப்பிக்க",
            "application": "விண்ணப்பம்",
            "documents": "ஆவணங்கள்",
            "required": "தேவையான",
            "income": "வருமானம்",
            "age": "வயது",
            "farmer": "விவசாயி",
            "benefits": "பலன்கள்",
            "help": "உதவி",
            
            # Phrases
            "how can i help you": "நான் உங்களுக்கு எவ்வாறு உதவ முடியும்",
            "what is your age": "உங்கள் வயது என்ன",
            "what is your income": "உங்கள் வருமானம் என்ன",
            "where do you live": "நீங்கள் எங்கே வாழ்கிறீர்கள்",
            "you are eligible": "நீங்கள் தகுதியானவர்",
            "you are not eligible": "நீங்கள் தகுதியற்றவர்",
            "here are some schemes": "இங்கே சில திட்டங்கள் உள்ளன",
            "based on your profile": "உங்கள் சுயவிவரத்தின் அடிப்படையில்",
        }
        
        # Reverse mapping
        self.ta_to_en = {v: k for k, v in self.en_to_ta.items()}
        
        # Tamil character detection pattern
        self.tamil_pattern = re.compile(r'[\u0B80-\u0BFF]')

    def detect_language(self, text: str) -> str:
        """
        Detect if text is in Tamil or English
        Returns 'ta' for Tamil, 'en' for English
        """
        if self.tamil_pattern.search(text):
            return "ta"
        return "en"
    
    def _translate_with_llm(self, text: str, target_lang: str) -> str:
        """Fallback translation using Mistral LLM"""
        try:
            if not settings.mistral_api_key:
                logger.warning("No Mistral key for translation fallback")
                return text

            # Helper for language codes
            lang_map = {
                "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada", 
                "ml": "Malayalam", "bn": "Bengali", "gu": "Gujarati", 
                "mr": "Marathi", "pa": "Punjabi", "or": "Odia"
            }
            target_name = lang_map.get(target_lang, target_lang)
            
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.mistral_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"Translate the following text to {target_name}. Output ONLY the translated text, no preamble or quotes. Text: {text}"
            
            data = {
                "model": "mistral-tiny",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            
            logger.error(f"LLM translation failed: {response.text}")
            return text
            
        except Exception as e:
            logger.error(f"LLM translation error: {e}")
            return text

    def translate_input(self, text: str, source_lang: Optional[str] = None) -> str:
        """
        Translate input text to English for processing
        """
        if source_lang is None:
            source_lang = self.detect_language(text)
        
        if source_lang == "en":
            return text
        
        try:
            # Use deep_translator for input
            translator = GoogleTranslator(source=source_lang if source_lang != "en" else "auto", target='en')
            return translator.translate(text)
        except Exception as e:
            logger.error(f"Translation input failed: {e}")
            # Fallback to dictionary for Tamil
            if source_lang == 'ta':
                translated = text.lower()
                for ta_phrase, en_phrase in self.ta_to_en.items():
                    if ta_phrase in translated:
                        translated = translated.replace(ta_phrase, en_phrase)
                return translated if translated != text.lower() else text
            
            # Fallback to LLM if input translation fails?
            # It's riskier for short inputs but worth a try if deep_translator fails entirely
            return self._translate_with_llm(text, "English")

    def translate_output(self, text: str, target_lang: str = "en") -> str:
        """
        Translate output text to target language
        """
        if target_lang == "en":
            return text
            
        try:
            # First attempt: GoogleTranslator (Free, Fast)
            translator = GoogleTranslator(source='auto', target=target_lang)
            translated = translator.translate(text)
            return translated
            
        except Exception as e:
            logger.warning(f"GoogleTranslator failed: {e}. Falling back to LLM.")
            
            # Second attempt: LLM (Reliable, requires key)
            return self._translate_with_llm(text, target_lang)
        
        return text

    def get_greeting(self, language: str = "en") -> str:
        """Get greeting message in specified language"""
        # Try to translate dynamic greeting if not en
        base_greeting = "Hello! Welcome to the Government Schemes Recommendation System. How can I help you today?"
        if language == "en":
            return base_greeting
        
        return self.translate_output(base_greeting, language)

    def get_profile_question(self, field: str, language: str = "en") -> str:
        """Get question for missing profile field"""
        if language == "en":
             questions = {
                "age": "What is your age?",
                "income": "What is your annual income (in INR)?",
                "location": "Which state do you live in?",
                "occupation": "What is your occupation?",
                "community": "What is your community category (SC/ST/OBC/General)?"
            }
             return questions.get(field, "")
             
        # Generate English question and translate it
        questions = {
            "age": "What is your age?",
            "income": "What is your annual income (in INR)?",
            "location": "Which state do you live in?",
            "occupation": "What is your occupation?",
            "community": "What is your community category (SC/ST/OBC/General)?"
        }
        q = questions.get(field, "")
        if q:
            return self.translate_output(q, language)
        return ""

    def format_scheme_response(self, schemes: list, language: str = "en") -> str:
        """Format scheme recommendations response"""
        msg = "Based on your profile, I recommend the following schemes:\n\n"
        if not schemes:
            msg = "I couldn't find any schemes matching your profile. Please provide more details about yourself."
            
        if language == "en":
            return msg
            
        return self.translate_output(msg, language)


# Singleton instance
translation_service = TranslationService()
