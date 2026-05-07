"""Test API endpoints"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


class TestAPI:
    """Test cases for API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "schemes_count" in data
    
    def test_get_languages(self):
        """Test languages endpoint"""
        response = self.client.get("/api/languages")
        assert response.status_code == 200
        
        languages = response.json()
        assert len(languages) >= 2
        codes = [lang["code"] for lang in languages]
        assert "en" in codes
        assert "ta" in codes
    
    def test_get_schemes(self):
        """Test get all schemes"""
        response = self.client.get("/api/schemes")
        assert response.status_code == 200
        
        data = response.json()
        assert "schemes" in data
        assert "total_count" in data
        assert data["total_count"] > 0
    
    def test_get_schemes_by_category(self):
        """Test get schemes by category"""
        response = self.client.get("/api/schemes?category=Agriculture")
        assert response.status_code == 200
        
        data = response.json()
        if data["total_count"] > 0:
            for scheme in data["schemes"]:
                assert scheme["category"].lower() == "agriculture"
    
    def test_get_scheme_by_id(self):
        """Test get scheme by ID"""
        response = self.client.get("/api/schemes/PM-KISAN-001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["scheme_id"] == "PM-KISAN-001"
        assert "name" in data
        assert "description" in data
    
    def test_get_scheme_not_found(self):
        """Test get scheme with invalid ID"""
        response = self.client.get("/api/schemes/INVALID-ID")
        assert response.status_code == 404
    
    def test_chat_greeting(self):
        """Test chat with greeting"""
        response = self.client.post("/api/chat", json={
            "message": "Hello",
            "language": "en"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert len(data["session_id"]) > 0
    
    def test_chat_with_profile_info(self):
        """Test chat providing profile information"""
        response = self.client.post("/api/chat", json={
            "message": "I am a 35 year old farmer from Tamil Nadu",
            "language": "en"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        # Should extract some entities
        if data.get("extracted_entities"):
            assert "age" in data["extracted_entities"] or "is_farmer" in data["extracted_entities"]
    
    def test_chat_recommendation_request(self):
        """Test chat requesting recommendations"""
        # First, create a session with profile
        response1 = self.client.post("/api/chat", json={
            "message": "I am a 35 year old farmer from Tamil Nadu with income 80000",
            "language": "en"
        })
        session_id = response1.json()["session_id"]
        
        # Then request recommendations
        response2 = self.client.post("/api/chat", json={
            "message": "Recommend schemes for me",
            "session_id": session_id,
            "language": "en"
        })
        assert response2.status_code == 200
        
        data = response2.json()
        assert "response" in data
        # Response should contain scheme recommendations
        assert len(data["response"]) > 100
    
    def test_update_profile(self):
        """Test profile update endpoint"""
        response = self.client.post("/api/profile", json={
            "session_id": "test-session-123",
            "age": 30,
            "income": 100000,
            "location": "Karnataka"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["profile"]["age"] == 30
        assert data["profile"]["income"] == 100000
        assert data["profile"]["location"] == "Karnataka"
    
    def test_get_profile(self):
        """Test get profile endpoint"""
        # First create a profile
        self.client.post("/api/profile", json={
            "session_id": "test-get-profile",
            "age": 25,
            "income": 50000
        })
        
        # Then get it
        response = self.client.get("/api/profile/test-get-profile")
        assert response.status_code == 200
        
        data = response.json()
        assert data["profile"]["age"] == 25
    
    def test_eligibility_check(self):
        """Test eligibility check endpoint"""
        # Create profile first
        self.client.post("/api/profile", json={
            "session_id": "test-eligibility",
            "age": 35,
            "income": 80000,
            "is_farmer": True,
            "has_land": True,
            "land_area": 1.5
        })
        
        # Check eligibility
        response = self.client.post("/api/eligibility/check", json={
            "session_id": "test-eligibility"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
    
    def test_eligibility_check_specific_scheme(self):
        """Test eligibility check for specific scheme"""
        # Create profile
        self.client.post("/api/profile", json={
            "session_id": "test-eligibility-specific",
            "is_farmer": True,
            "has_land": True,
            "land_area": 1.0
        })
        
        # Check specific scheme
        response = self.client.post("/api/eligibility/check", json={
            "session_id": "test-eligibility-specific",
            "scheme_id": "PM-KISAN-001"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["scheme_id"] == "PM-KISAN-001"
    
    def test_clear_session(self):
        """Test clear session endpoint"""
        # Create a session
        response = self.client.post("/api/chat", json={
            "message": "Hello",
            "session_id": "test-clear-session"
        })
        
        # Clear it
        response = self.client.delete("/api/session/test-clear-session")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "test-clear-session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
