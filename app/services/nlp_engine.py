"""NLP Engine for intent detection and entity extraction"""

import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class Intent(str, Enum):
    """User intent categories"""
    GET_RECOMMENDATIONS = "get_recommendations"
    CHECK_ELIGIBILITY = "check_eligibility"
    APPLY_SCHEME = "apply_scheme"
    PROVIDE_INFO = "provide_info"
    GET_DOCUMENTS = "get_documents"
    GET_SCHEME_DETAILS = "get_scheme_details"
    GREETING = "greeting"
    HELP = "help"
    UNKNOWN = "unknown"


class NLPEngine:
    """NLP-driven engine for intent detection and entity extraction"""
    
    def __init__(self):
        # Intent patterns (keywords and phrases)
        self.intent_patterns = {
            Intent.GET_RECOMMENDATIONS: [
                r"recommend", r"suggest", r"schemes?\s+for\s+me", r"what\s+schemes?",
                r"eligible\s+schemes?", r"available\s+schemes?", r"show\s+schemes?",
                r"find\s+schemes?", r"which\s+schemes?", r"government\s+schemes?"
            ],
            Intent.CHECK_ELIGIBILITY: [
                r"am\s+i\s+eligible", r"eligibility", r"can\s+i\s+(get|apply)",
                r"qualify", r"check\s+if", r"do\s+i\s+qualify"
            ],
            Intent.APPLY_SCHEME: [
                r"how\s+to\s+apply", r"application\s+process", r"apply\s+for",
                r"register\s+for", r"enroll", r"sign\s+up\s+for"
            ],
            Intent.GET_DOCUMENTS: [
                r"documents?\s+(required|needed)", r"what\s+documents?",
                r"papers?\s+needed", r"checklist"
            ],
            Intent.GET_SCHEME_DETAILS: [
                r"tell\s+me\s+(more\s+)?about", r"more\s+details?", r"explain",
                r"what\s+is", r"details?\s+(about|of|on)", r"scheme\s*\d",
                r"option\s*\d", r"number\s*\d", r"#\s*\d", r"more\s+info"
            ],
            Intent.PROVIDE_INFO: [
                r"i\s+am\s+a?", r"my\s+(age|income|occupation)",
                r"i\s+(live|work|earn)", r"i\s+have", r"years?\s+old"
            ],
            Intent.GREETING: [
                r"^(hi|hello|hey|namaste|vanakkam)", r"good\s+(morning|afternoon|evening)"
            ],
            Intent.HELP: [
                r"help", r"how\s+does\s+this\s+work", r"what\s+can\s+you\s+do"
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            "age": [
                r"(\d{1,3})\s*years?\s*old",
                r"age\s*(?:is\s*)?(\d{1,3})",
                r"i\s+am\s+(\d{1,3})"
            ],
            "income": [
                r"income\s*(?:is\s*)?([\d,]+)",
                r"earn\s*([\d,]+)",
                r"salary\s*(?:is\s*)?([\d,]+)",
                r"([\d,]+)\s*(?:per\s*(?:month|year|annum))"
            ],
            "occupation": [
                r"(?:i\s+am\s+a\s*|work\s+as\s+a?\s*|occupation\s*(?:is\s*)?)(farmer|teacher|laborer|worker|employee|student|business|retired|unemployed)",
            ],
            "location": [
                r"(?:from|in|live\s+in|living\s+in)\s+([A-Za-z\s]+?)(?:\s*,|\s*\.|$)",
                r"(?:state|district)\s*(?:is\s*)?([A-Za-z\s]+?)(?:\s*,|\s*\.|$)"
            ],
            "community": [
                r"(sc|st|obc|general|backward\s+class)",
                r"(scheduled\s+(?:caste|tribe))",
                r"(other\s+backward\s+class)"
            ],
            "gender": [
                r"\b(male|female|man|woman)\b"
            ],
            "is_farmer": [
                r"(?:i\s+am\s+a?\s*)?farmer",
                r"(?:do\s+)?farming",
                r"agricultural"
            ],
            "is_bpl": [
                r"bpl",
                r"below\s+poverty\s+line",
                r"poor\s+family"
            ]
        }
        
        # Location normalization - extensive list
        self.location_mapping = {
            "tamilnadu": "Tamil Nadu",
            "tamil nadu": "Tamil Nadu",
            "tn": "Tamil Nadu",
            "karnataka": "Karnataka",
            "ka": "Karnataka",
            "kerala": "Kerala",
            "kl": "Kerala",
            "andhra": "Andhra Pradesh",
            "andhra pradesh": "Andhra Pradesh",
            "ap": "Andhra Pradesh",
            "telangana": "Telangana",
            "ts": "Telangana",
            "maharashtra": "Maharashtra",
            "mh": "Maharashtra",
            "gujarat": "Gujarat",
            "gj": "Gujarat",
            "rajasthan": "Rajasthan",
            "rj": "Rajasthan",
            "up": "Uttar Pradesh",
            "uttar pradesh": "Uttar Pradesh",
            "uttarpradesh": "Uttar Pradesh",
            "bihar": "Bihar",
            "br": "Bihar",
            "mp": "Madhya Pradesh",
            "madhya pradesh": "Madhya Pradesh",
            "madhyapradesh": "Madhya Pradesh",
            "west bengal": "West Bengal",
            "westbengal": "West Bengal",
            "wb": "West Bengal",
            "punjab": "Punjab",
            "pb": "Punjab",
            "haryana": "Haryana",
            "hr": "Haryana",
            "odisha": "Odisha",
            "or": "Odisha",
            "assam": "Assam",
            "as": "Assam",
            "jharkhand": "Jharkhand",
            "jh": "Jharkhand",
            "chhattisgarh": "Chhattisgarh",
            "cg": "Chhattisgarh",
            "uttarakhand": "Uttarakhand",
            "uk": "Uttarakhand",
            "goa": "Goa",
            "delhi": "Delhi",
            "dl": "Delhi"
        }
        
        # Community normalization  
        self.community_mapping = {
            "sc": "SC",
            "scheduled caste": "SC",
            "st": "ST",
            "scheduled tribe": "ST",
            "obc": "OBC",
            "other backward class": "OBC",
            "backward class": "OBC",
            "general": "General"
        }

    def detect_intent(self, text: str) -> Tuple[Intent, float]:
        """
        Detect the primary intent of user message
        Returns (intent, confidence_score)
        """
        text_lower = text.lower().strip()
        
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                intent_scores[intent] = score / len(patterns)
        
        if not intent_scores:
            return Intent.UNKNOWN, 0.0
        
        # Get highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent] * 2, 1.0)  # Scale confidence
        
        return best_intent, confidence

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from user message
        """
        text_lower = text.lower()
        entities = {}
        
        # Extract age
        for pattern in self.entity_patterns["age"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    age = int(match.group(1))
                    if 0 < age <= 120:
                        entities["age"] = age
                        break
                except ValueError:
                    pass
        
        # Extract income
        for pattern in self.entity_patterns["income"]:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    income_str = match.group(1).replace(",", "")
                    income = float(income_str)
                    entities["income"] = income
                    break
                except ValueError:
                    pass
        
        # Extract occupation
        for pattern in self.entity_patterns["occupation"]:
            match = re.search(pattern, text_lower)
            if match:
                entities["occupation"] = match.group(1).strip().title()
                break
        
        # Extract location - first try patterns
        location_found = False
        for pattern in self.entity_patterns["location"]:
            match = re.search(pattern, text_lower)
            if match:
                location = match.group(1).strip().lower()
                entities["location"] = self.location_mapping.get(location, location.title())
                location_found = True
                break
        
        # If no pattern match, check if the entire text or any word is a known location
        if not location_found:
            text_clean = text_lower.strip()
            # Check if whole text is a location
            if text_clean in self.location_mapping:
                entities["location"] = self.location_mapping[text_clean]
            else:
                # Check each word
                for word in text_clean.split():
                    if word in self.location_mapping:
                        entities["location"] = self.location_mapping[word]
                        break
        
        # Extract community
        for pattern in self.entity_patterns["community"]:
            match = re.search(pattern, text_lower)
            if match:
                community = match.group(1).strip().lower()
                entities["community"] = self.community_mapping.get(community, community.upper())
                break
        
        # Extract gender
        for pattern in self.entity_patterns["gender"]:
            match = re.search(pattern, text_lower)
            if match:
                gender = match.group(1).lower()
                if gender in ["man", "male"]:
                    entities["gender"] = "male"
                elif gender in ["woman", "female"]:
                    entities["gender"] = "female"
                break
        
        # Check for farmer
        for pattern in self.entity_patterns["is_farmer"]:
            if re.search(pattern, text_lower):
                entities["is_farmer"] = True
                entities["occupation"] = "Farmer"
                break
        
        # Check for BPL
        for pattern in self.entity_patterns["is_bpl"]:
            if re.search(pattern, text_lower):
                entities["is_bpl"] = True
                break
        
        return entities

    def extract_scheme_name(self, text: str) -> Optional[str]:
        """Extract scheme name mentioned in text"""
        scheme_patterns = [
            r"pm\s*kisan",
            r"pm\s*awas",
            r"pmay",
            r"ujjwala",
            r"mudra",
            r"jan\s*dhan",
            r"ayushman\s*bharat",
            r"pmjay",
            r"sukanya\s*samriddhi",
            r"kisan\s*samman",
            r"mgnrega",
            r"widow\s*pension",
            r"scholarship"
        ]
        
        text_lower = text.lower()
        for pattern in scheme_patterns:
            if re.search(pattern, text_lower):
                return pattern.replace(r"\s*", " ").title()
        
        return None
    
    def extract_scheme_number(self, text: str) -> Optional[int]:
        """Extract scheme number from text like 'scheme 3' or 'option 2' or '#1'"""
        patterns = [
            r"scheme\s*#?\s*(\d+)",
            r"option\s*#?\s*(\d+)",
            r"number\s*#?\s*(\d+)",
            r"#\s*(\d+)",
            r"\b(\d+)(?:st|nd|rd|th)?\s*(?:one|scheme|option)?",
            r"(?:first|second|third|fourth|fifth)\s*(?:one|scheme|option)?"
        ]
        
        text_lower = text.lower()
        
        # Check for word numbers
        word_to_num = {
            "first": 1, "second": 2, "third": 3, 
            "fourth": 4, "fifth": 5, "1st": 1, 
            "2nd": 2, "3rd": 3, "4th": 4, "5th": 5
        }
        for word, num in word_to_num.items():
            if word in text_lower:
                return num
        
        # Check for numeric patterns
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass
        
        return None

    def get_missing_profile_fields(self, extracted: Dict[str, Any]) -> List[str]:
        """Get list of important missing profile fields"""
        required_fields = ["age", "income", "location"]
        missing = []
        
        for field in required_fields:
            if field not in extracted or extracted[field] is None:
                missing.append(field)
        
        return missing


# Singleton instance
nlp_engine = NLPEngine()
