# app/tools/profile_extraction.py
"""
Profile Extraction Tools

Provides utilities for extracting and structuring business profile data
optimized for Sri Lankan SME context.
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class BusinessProfileTemplate:
    """
    Generates business profile templates optimized for Sri Lankan SMEs
    """
    
    def __init__(self):
        self.base_template = {
            "business_identity": {
                "business_type": "",
                "industry": "", 
                "business_size": "",
                "location": "",
                "business_stage": "",
                "products_services": "",
                "unique_value": "",
                "years_in_business": ""
            },
            "resources": {
                "monthly_budget": "",
                "team_or_solo": "",
                "content_capacity": "",
                "technical_skills": "",
                "available_hours_per_week": ""
            },
            "goals": {
                "primary_goal": "",
                "secondary_goals": [],
                "success_metrics": [],
                "timeline_expectations": ""
            },
            "target_audience": {
                "demographics": "",
                "target_locations": "",
                "interests_behaviors": "",
                "buying_frequency": "",
                "price_sensitivity": "",
                "communication_preferences": []
            },
            "platform_preferences": {
                "preferred_platforms": [],
                "platform_experience": "",
                "brand_assets_available": [],
                "current_followers": {},
                "posting_frequency": ""
            },
            "strengths": [],
            "challenges": [],
            "opportunities": [],
            "market_context": {
                "seasonality": "",
                "competitor_behavior": "",
                "local_market_conditions": "",
                "economic_factors": "",
                "cultural_considerations": ""
            },
            "brand_personality": {
                "suggested_tone": "",
                "brand_values": [],
                "communication_style": "",
                "visual_preferences": ""
            },
            "missing_data_assumptions": {}
        }
        
        # Sri Lankan specific business contexts
        self.sri_lankan_context = {
            "common_locations": [
                "Colombo", "Gampaha", "Kandy", "Galle", "Matara", "Jaffna", 
                "Negombo", "Anuradhapura", "Batticaloa", "Trincomalee"
            ],
            "business_stages": [
                "Just Started", "Growing", "Established", "Expanding", "Mature"
            ],
            "common_goals": [
                "brand awareness", "increase sales", "customer acquisition", 
                "online presence", "customer retention", "market expansion"
            ],
            "platform_priorities": {
                "food_beverage": ["Facebook", "Instagram", "WhatsApp"],
                "retail": ["Facebook", "Instagram", "WhatsApp", "TikTok"],
                "services": ["Facebook", "WhatsApp", "LinkedIn"],
                "beauty": ["Instagram", "Facebook", "TikTok"],
                "technology": ["LinkedIn", "Facebook", "Instagram"]
            }
        }
    
    def get_template(self, business_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get profile template, optionally customized for business type
        """
        template = self.base_template.copy()
        
        if business_type:
            # Customize based on business type
            template = self._customize_for_business_type(template, business_type)
        
        return template
    
    def _customize_for_business_type(self, template: Dict, business_type: str) -> Dict:
        """
        Customize template based on business type
        """
        business_lower = business_type.lower()
        
        # Customize platform preferences
        for category, platforms in self.sri_lankan_context["platform_priorities"].items():
            if any(word in business_lower for word in category.split('_')):
                template["platform_preferences"]["preferred_platforms"] = platforms
                break
        
        # Add business-specific success metrics
        if "restaurant" in business_lower or "food" in business_lower:
            template["goals"]["success_metrics"] = [
                "Daily orders", "Customer reviews", "Social media engagement"
            ]
        elif "retail" in business_lower or "shop" in business_lower:
            template["goals"]["success_metrics"] = [
                "Monthly sales", "Foot traffic", "Online inquiries"
            ]
        
        return template

class ProfileExtractor:
    """
    Extracts structured data from raw business input
    """
    
    def __init__(self):
        self.template_generator = BusinessProfileTemplate()
        
        # Common Sri Lankan business terms and their mappings
        self.term_mappings = {
            # Business types
            "kade": "shop", "kedey": "shop", 
            "restaurant eka": "restaurant", "kema kade": "restaurant",
            "salon eka": "beauty salon", "lassana kade": "beauty salon",
            "garage eka": "auto repair", "motor garage": "auto repair",
            
            # Goals
            "awareness ekak oni": "brand awareness",
            "sales wadakaranna": "increase sales",
            "customers la gana": "customer acquisition", 
            "reach eka wadakaranna": "increase reach",
            "online presence eka": "build online presence",
            "business eka grow karanna": "business growth",
            
            # Challenges
            "photos nane": "lack of content",
            "time nane": "time constraints",
            "followers nane": "low follower count",
            "engagement nane": "poor engagement",
            "budget nane": "limited budget",
            "posts karanna bane": "difficulty creating content",
            "social media dannne nane": "lack of social media knowledge",
            
            # Strengths
            "hondama quality": "high quality products",
            "loyal customers": "strong customer loyalty", 
            "good location": "strategic location",
            "kana eka hondai": "good food",
            "service eka hondai": "excellent service",
            
            # Platforms
            "fb": "Facebook", "facebook": "Facebook",
            "ig": "Instagram", "insta": "Instagram",
            "whatsapp": "WhatsApp", "wp": "WhatsApp",
            "tiktok": "TikTok", "youtube": "YouTube"
        }
        
        # Budget patterns
        self.budget_patterns = {
            r'(\d+)\s*k': lambda m: f"LKR {int(m.group(1)) * 1000:,}",
            r'(\d{1,3}(?:,\d{3})*)': lambda m: f"LKR {m.group(1)}",
            r'lkr\s*(\d+(?:,\d+)*)': lambda m: f"LKR {m.group(1)}",
            r'rs\s*(\d+(?:,\d+)*)': lambda m: f"LKR {m.group(1)}",
            r'rupees?\s*(\d+(?:,\d+)*)': lambda m: f"LKR {m.group(1)}"
        }
    
    def normalize_sinhala_terms(self, text: str) -> str:
        """
        Normalize Sinhala/mixed language terms to English
        """
        normalized = text.lower()
        
        for sinhala_term, english_term in self.term_mappings.items():
            normalized = normalized.replace(sinhala_term, english_term)
        
        return normalized
    
    def extract_budget(self, text: str) -> Optional[str]:
        """
        Extract and normalize budget information
        """
        text_lower = text.lower()
        
        for pattern, formatter in self.budget_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                return formatter(match)
        
        return None
    
    def extract_platforms(self, text: str) -> List[str]:
        """
        Extract social media platforms mentioned
        """
        platforms = []
        text_lower = text.lower()
        
        platform_keywords = {
            "facebook": ["facebook", "fb"],
            "instagram": ["instagram", "insta", "ig"],
            "whatsapp": ["whatsapp", "wp"],
            "tiktok": ["tiktok"],
            "youtube": ["youtube", "yt"],
            "linkedin": ["linkedin"]
        }
        
        for platform, keywords in platform_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                platforms.append(platform.title())
        
        return platforms
    
    def extract_business_type(self, text: str) -> Optional[str]:
        """
        Extract business type from text
        """
        text_lower = text.lower()
        
        business_indicators = {
            "restaurant": ["restaurant", "kema kade", "food", "dining"],
            "bakery": ["bakery", "cake", "bread", "pastry"],
            "salon": ["salon", "beauty", "hair", "lassana"],
            "retail": ["shop", "store", "kade", "selling"],
            "garage": ["garage", "repair", "motor"],
            "pharmacy": ["pharmacy", "medicine", "beheth"],
            "tutoring": ["tuition", "class", "teaching", "education"]
        }
        
        for business_type, keywords in business_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                return business_type.title()
        
        return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """
        Extract Sri Lankan location from text
        """
        sri_lankan_locations = [
            "colombo", "gampaha", "kandy", "galle", "matara", "jaffna",
            "negombo", "anuradhapura", "batticaloa", "trincomalee",
            "kurunegala", "ratnapura", "badulla", "monaragala", "hambantota",
            "kalutara", "kegalle", "nuwara eliya", "polonnaruwa", "puttalam",
            "vavuniya", "mannar", "mullativu", "kilinochchi", "ampara"
        ]
        
        text_lower = text.lower()
        for location in sri_lankan_locations:
            if location in text_lower:
                return location.title()
        
        return None
    
    def extract_challenges(self, text: str) -> List[str]:
        """
        Extract business challenges from text
        """
        challenges = []
        text_lower = text.lower()
        
        challenge_patterns = {
            "lack of content": ["photos nane", "content nane", "no photos", "no content"],
            "time constraints": ["time nane", "no time", "busy"],
            "limited budget": ["budget nane", "money nane", "expensive"],
            "low engagement": ["engagement nane", "no likes", "no comments"],
            "small audience": ["followers nane", "no followers", "small reach"],
            "lack of knowledge": ["dannne nane", "don't know", "new to social media"]
        }
        
        for challenge, keywords in challenge_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                challenges.append(challenge)
        
        return challenges
    
    def extract_strengths(self, text: str) -> List[str]:
        """
        Extract business strengths from text
        """
        strengths = []
        text_lower = text.lower()
        
        strength_patterns = {
            "high quality products": ["quality", "hondama", "best", "good quality"],
            "loyal customers": ["loyal", "regular customers", "repeat customers"],
            "good location": ["good location", "prime location", "strategic location"],
            "experienced team": ["experienced", "skilled", "expert"],
            "unique products": ["unique", "special", "different", "exclusive"]
        }
        
        for strength, keywords in strength_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                strengths.append(strength)
        
        return strengths
