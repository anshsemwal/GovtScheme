"""Eligibility validation service"""

from typing import Dict, Any, List, Tuple
from app.models.user import Profile
from app.models.scheme import Scheme, EligibilityCriteria


class EligibilityValidator:
    """Validates user eligibility against scheme criteria"""
    
    def __init__(self):
        self.validation_messages = {
            "age_too_young": "You do not meet the minimum age requirement of {min_age} years.",
            "age_too_old": "You exceed the maximum age limit of {max_age} years.",
            "income_too_high": "Your income exceeds the maximum limit of ₹{max_income}.",
            "income_too_low": "Your income is below the minimum requirement of ₹{min_income}.",
            "community_mismatch": "This scheme is for {communities} communities only.",
            "location_mismatch": "This scheme is available only in {locations}.",
            "occupation_mismatch": "This scheme is for {occupations} only.",
            "gender_mismatch": "This scheme is for {gender} applicants only.",
            "farmer_required": "This scheme is only for farmers.",
            "bpl_required": "This scheme is only for Below Poverty Line (BPL) families.",
            "land_required": "This scheme requires land ownership."
        }
    
    def validate_eligibility(
        self, 
        profile: Profile, 
        scheme: Scheme
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate user profile against scheme eligibility criteria
        
        Returns:
            Tuple of (is_eligible, met_criteria, unmet_criteria)
        """
        criteria = scheme.eligibility_criteria
        met = []
        unmet = []
        
        # Age validation
        if profile.age is not None:
            if criteria.min_age and profile.age < criteria.min_age:
                unmet.append(self.validation_messages["age_too_young"].format(min_age=criteria.min_age))
            elif criteria.max_age and profile.age > criteria.max_age:
                unmet.append(self.validation_messages["age_too_old"].format(max_age=criteria.max_age))
            else:
                met.append(f"Age requirement met ({profile.age} years)")
        
        # Income validation
        if profile.income is not None:
            if criteria.max_income and profile.income > criteria.max_income:
                unmet.append(self.validation_messages["income_too_high"].format(max_income=criteria.max_income))
            elif criteria.min_income and profile.income < criteria.min_income:
                unmet.append(self.validation_messages["income_too_low"].format(min_income=criteria.min_income))
            else:
                met.append(f"Income requirement met (₹{profile.income})")
        
        # Community validation
        if criteria.communities and profile.community:
            if profile.community.upper() not in [c.upper() for c in criteria.communities]:
                unmet.append(self.validation_messages["community_mismatch"].format(
                    communities=", ".join(criteria.communities)
                ))
            else:
                met.append(f"Community requirement met ({profile.community})")
        
        # Location validation
        if criteria.locations and profile.location:
            location_match = any(
                loc.lower() in profile.location.lower() or profile.location.lower() in loc.lower()
                for loc in criteria.locations
            )
            if not location_match:
                unmet.append(self.validation_messages["location_mismatch"].format(
                    locations=", ".join(criteria.locations)
                ))
            else:
                met.append(f"Location requirement met ({profile.location})")
        
        # Occupation validation
        if criteria.occupations and profile.occupation:
            if profile.occupation.lower() not in [o.lower() for o in criteria.occupations]:
                unmet.append(self.validation_messages["occupation_mismatch"].format(
                    occupations=", ".join(criteria.occupations)
                ))
            else:
                met.append(f"Occupation requirement met ({profile.occupation})")
        
        # Gender validation
        if criteria.gender and profile.gender:
            if profile.gender.lower() != criteria.gender.lower():
                unmet.append(self.validation_messages["gender_mismatch"].format(gender=criteria.gender))
            else:
                met.append(f"Gender requirement met ({profile.gender})")
        
        # Farmer requirement
        if criteria.is_farmer_required:
            if not profile.is_farmer:
                unmet.append(self.validation_messages["farmer_required"])
            else:
                met.append("Farmer status verified")
        
        # BPL requirement
        if criteria.is_bpl_required:
            if not profile.is_bpl:
                unmet.append(self.validation_messages["bpl_required"])
            else:
                met.append("BPL status verified")
        
        # Land requirement
        if criteria.has_land_required:
            if not profile.has_land:
                unmet.append(self.validation_messages["land_required"])
            else:
                met.append("Land ownership verified")
        
        # Land area check
        if criteria.max_land_area and profile.land_area:
            if profile.land_area > criteria.max_land_area:
                unmet.append(f"Land area exceeds maximum limit of {criteria.max_land_area} hectares")
            else:
                met.append(f"Land area within limit ({profile.land_area} hectares)")
        
        is_eligible = len(unmet) == 0
        return is_eligible, met, unmet

    def get_eligibility_score(self, profile: Profile, scheme: Scheme) -> float:
        """
        Calculate eligibility score (0-1) for ranking schemes
        """
        is_eligible, met, unmet = self.validate_eligibility(profile, scheme)
        
        if is_eligible:
            return 1.0
        
        total_criteria = len(met) + len(unmet)
        if total_criteria == 0:
            return 0.5  # No criteria to check
        
        return len(met) / total_criteria

    def format_eligibility_result(
        self, 
        scheme: Scheme, 
        is_eligible: bool, 
        met: List[str], 
        unmet: List[str],
        language: str = "en"
    ) -> str:
        """Format eligibility check result as readable text"""
        result = []
        
        if language == "ta":
            scheme_name = scheme.name_tamil or scheme.name
            if is_eligible:
                result.append(f"✅ நீங்கள் **{scheme_name}** திட்டத்திற்கு தகுதியானவர்!")
            else:
                result.append(f"❌ நீங்கள் **{scheme_name}** திட்டத்திற்கு தகுதியற்றவர்.")
        else:
            if is_eligible:
                result.append(f"✅ You are **eligible** for **{scheme.name}**!")
            else:
                result.append(f"❌ You are **not eligible** for **{scheme.name}**.")
        
        if met:
            result.append("\n**Criteria Met:**")
            for item in met:
                result.append(f"  • {item}")
        
        if unmet:
            result.append("\n**Criteria Not Met:**")
            for item in unmet:
                result.append(f"  • {item}")
        
        return "\n".join(result)

    def get_application_guidance(self, scheme: Scheme, language: str = "en") -> str:
        """Get application guidance for a scheme"""
        if language == "ta":
            header = f"**{scheme.name_tamil or scheme.name}** திட்டத்திற்கு விண்ணப்பிக்க:\n\n"
        else:
            header = f"To apply for **{scheme.name}**:\n\n"
        
        guidance = [header]
        
        # Application process
        if scheme.application_process:
            guidance.append(f"**Application Process:**\n{scheme.application_process}\n")
        
        # Required documents
        if scheme.documents_required:
            guidance.append("**Required Documents:**")
            for doc in scheme.documents_required:
                guidance.append(f"  • {doc}")
        
        return "\n".join(guidance)


# Singleton instance
eligibility_validator = EligibilityValidator()
