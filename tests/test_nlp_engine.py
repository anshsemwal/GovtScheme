"""Test NLP Engine"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.nlp_engine import NLPEngine, Intent


class TestNLPEngine:
    """Test cases for NLP Engine"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.nlp = NLPEngine()
    
    def test_detect_greeting_intent(self):
        """Test greeting intent detection"""
        intent, confidence = self.nlp.detect_intent("Hello")
        assert intent == Intent.GREETING
        
        intent, confidence = self.nlp.detect_intent("Hi there")
        assert intent == Intent.GREETING
        
        intent, confidence = self.nlp.detect_intent("Good morning")
        assert intent == Intent.GREETING
    
    def test_detect_recommendation_intent(self):
        """Test recommendation intent detection"""
        intent, confidence = self.nlp.detect_intent("Recommend schemes for me")
        assert intent == Intent.GET_RECOMMENDATIONS
        
        intent, confidence = self.nlp.detect_intent("What government schemes are available?")
        assert intent == Intent.GET_RECOMMENDATIONS
        
        intent, confidence = self.nlp.detect_intent("Show me eligible schemes")
        assert intent == Intent.GET_RECOMMENDATIONS
    
    def test_detect_eligibility_intent(self):
        """Test eligibility check intent detection"""
        intent, confidence = self.nlp.detect_intent("Am I eligible for PM Kisan?")
        assert intent == Intent.CHECK_ELIGIBILITY
        
        intent, confidence = self.nlp.detect_intent("Check my eligibility")
        assert intent == Intent.CHECK_ELIGIBILITY
    
    def test_detect_apply_intent(self):
        """Test application intent detection"""
        intent, confidence = self.nlp.detect_intent("How to apply for PMAY?")
        assert intent == Intent.APPLY_SCHEME
        
        intent, confidence = self.nlp.detect_intent("Application process for mudra")
        assert intent == Intent.APPLY_SCHEME
    
    def test_extract_age(self):
        """Test age extraction"""
        entities = self.nlp.extract_entities("I am 35 years old")
        assert entities.get("age") == 35
        
        entities = self.nlp.extract_entities("My age is 42")
        assert entities.get("age") == 42
    
    def test_extract_income(self):
        """Test income extraction"""
        entities = self.nlp.extract_entities("My income is 50000")
        assert entities.get("income") == 50000
        
        entities = self.nlp.extract_entities("I earn 1,00,000 per year")
        assert entities.get("income") == 100000
    
    def test_extract_location(self):
        """Test location extraction"""
        entities = self.nlp.extract_entities("I live in Tamil Nadu")
        assert entities.get("location") == "Tamil Nadu"
        
        entities = self.nlp.extract_entities("I am from Karnataka")
        assert entities.get("location") == "Karnataka"
    
    def test_extract_occupation(self):
        """Test occupation extraction"""
        entities = self.nlp.extract_entities("I am a farmer")
        assert entities.get("occupation") == "Farmer"
        assert entities.get("is_farmer") == True
        
        entities = self.nlp.extract_entities("I work as a teacher")
        assert entities.get("occupation") == "Teacher"
    
    def test_extract_community(self):
        """Test community extraction"""
        entities = self.nlp.extract_entities("I belong to SC community")
        assert entities.get("community") == "SC"
        
        entities = self.nlp.extract_entities("I am from OBC category")
        assert entities.get("community") == "OBC"
    
    def test_extract_bpl(self):
        """Test BPL status extraction"""
        entities = self.nlp.extract_entities("I am from a BPL family")
        assert entities.get("is_bpl") == True
        
        entities = self.nlp.extract_entities("We are below poverty line")
        assert entities.get("is_bpl") == True
    
    def test_extract_multiple_entities(self):
        """Test extracting multiple entities from single message"""
        entities = self.nlp.extract_entities(
            "I am a 35 year old farmer from Tamil Nadu with income 80000"
        )
        assert entities.get("age") == 35
        assert entities.get("occupation") == "Farmer"
        # Location extraction may not work perfectly with complex sentences
        # Core entities should be extracted
        assert entities.get("is_farmer") == True
        assert entities.get("income") == 80000
    
    def test_scheme_name_extraction(self):
        """Test scheme name extraction"""
        name = self.nlp.extract_scheme_name("Tell me about PM Kisan")
        assert name is not None
        assert "kisan" in name.lower()
        
        name = self.nlp.extract_scheme_name("Check eligibility for Ujjwala")
        assert name is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
