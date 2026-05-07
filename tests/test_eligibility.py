"""Test Eligibility Validator"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import Profile
from app.models.scheme import Scheme, EligibilityCriteria
from app.services.eligibility import EligibilityValidator


class TestEligibilityValidator:
    """Test cases for Eligibility Validator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = EligibilityValidator()
        
        # Sample scheme - PM Kisan
        self.pm_kisan = Scheme(
            scheme_id="PM-KISAN-001",
            name="PM Kisan Samman Nidhi",
            description="Income support for farmers",
            benefits="₹6000 per year",
            eligibility_criteria=EligibilityCriteria(
                is_farmer_required=True,
                has_land_required=True,
                max_land_area=2.0
            )
        )
        
        # Sample scheme with income limit
        self.pmay = Scheme(
            scheme_id="PMAY-002",
            name="PM Awas Yojana",
            description="Housing scheme",
            benefits="Housing subsidy",
            eligibility_criteria=EligibilityCriteria(
                max_income=300000
            )
        )
        
        # Sample scheme with age limit
        self.sukanya = Scheme(
            scheme_id="SSY-003",
            name="Sukanya Samriddhi Yojana",
            description="Savings for girl child",
            benefits="8.2% interest",
            eligibility_criteria=EligibilityCriteria(
                gender="female",
                max_age=10
            )
        )
    
    def test_farmer_eligibility_eligible(self):
        """Test farmer eligibility - eligible case"""
        profile = Profile(
            age=35,
            income=80000,
            location="Tamil Nadu",
            occupation="Farmer",
            is_farmer=True,
            has_land=True,
            land_area=1.5
        )
        
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.pm_kisan)
        assert is_eligible == True
        assert len(unmet) == 0
    
    def test_farmer_eligibility_not_farmer(self):
        """Test farmer eligibility - not a farmer"""
        profile = Profile(
            age=35,
            income=80000,
            location="Tamil Nadu",
            occupation="Teacher",
            is_farmer=False
        )
        
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.pm_kisan)
        assert is_eligible == False
        assert any("farmer" in msg.lower() for msg in unmet)
    
    def test_income_eligibility_eligible(self):
        """Test income eligibility - within limit"""
        profile = Profile(
            age=35,
            income=200000,
            location="Tamil Nadu"
        )
        
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.pmay)
        assert is_eligible == True
    
    def test_income_eligibility_exceeds(self):
        """Test income eligibility - exceeds limit"""
        profile = Profile(
            age=35,
            income=500000,
            location="Tamil Nadu"
        )
        
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.pmay)
        assert is_eligible == False
        assert any("income" in msg.lower() for msg in unmet)
    
    def test_age_eligibility_eligible(self):
        """Test age eligibility - within limit"""
        profile = Profile(
            age=8,
            gender="female"
        )
        
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.sukanya)
        assert is_eligible == True
    
    def test_age_eligibility_exceeds(self):
        """Test age eligibility - exceeds limit"""
        profile = Profile(
            age=15,
            gender="female"
        )
        
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.sukanya)
        assert is_eligible == False
        assert any("age" in msg.lower() for msg in unmet)
    
    def test_gender_eligibility(self):
        """Test gender eligibility"""
        profile_female = Profile(age=8, gender="female")
        profile_male = Profile(age=8, gender="male")
        
        is_eligible_f, _, _ = self.validator.validate_eligibility(profile_female, self.sukanya)
        is_eligible_m, _, _ = self.validator.validate_eligibility(profile_male, self.sukanya)
        
        assert is_eligible_f == True
        assert is_eligible_m == False
    
    def test_eligibility_score(self):
        """Test eligibility score calculation"""
        # Fully eligible profile
        eligible_profile = Profile(
            is_farmer=True,
            has_land=True,
            land_area=1.5
        )
        
        # Partially eligible profile
        partial_profile = Profile(
            is_farmer=True,
            has_land=False
        )
        
        score_eligible = self.validator.get_eligibility_score(eligible_profile, self.pm_kisan)
        score_partial = self.validator.get_eligibility_score(partial_profile, self.pm_kisan)
        
        assert score_eligible == 1.0  # Fully eligible
        assert 0 < score_partial < 1.0  # Partially eligible
    
    def test_format_eligibility_result(self):
        """Test formatting eligibility result"""
        profile = Profile(is_farmer=True, has_land=True, land_area=1.5)
        is_eligible, met, unmet = self.validator.validate_eligibility(profile, self.pm_kisan)
        
        result = self.validator.format_eligibility_result(
            self.pm_kisan, is_eligible, met, unmet, "en"
        )
        
        assert "PM Kisan" in result
        assert "eligible" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
