"""
Profile Extraction Tool
Utilities for extracting and processing customer profile data from various sources
"""

from typing import Dict, Any, List, Optional, Union
import re
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProfileExtractor:
    """
    Tool for extracting structured customer profile data from various input formats
    """
    
    def __init__(self):
        self.demographic_fields = {
            "age", "gender", "location", "income", "education", "occupation",
            "marital_status", "family_size", "homeowner_status"
        }
        
        self.behavioral_fields = {
            "purchase_history", "website_interactions", "email_engagement",
            "social_media_activity", "product_preferences", "brand_loyalty"
        }
        
        self.psychographic_fields = {
            "interests", "values", "lifestyle", "personality_traits",
            "attitudes", "opinions", "motivations", "fears"
        }
    
    async def extract_profile_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured profile data from raw input
        
        Args:
            raw_data: Raw customer data from various sources
            
        Returns:
            Structured profile data organized by categories
        """
        
        try:
            extracted = {
                "demographics": self._extract_demographics(raw_data),
                "behavioral": self._extract_behavioral_data(raw_data),
                "psychographics": self._extract_psychographics(raw_data),
                "contact_info": self._extract_contact_info(raw_data),
                "preferences": self._extract_preferences(raw_data),
                "interaction_history": self._extract_interaction_history(raw_data),
                "metadata": {
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                    "data_sources": self._identify_data_sources(raw_data),
                    "data_quality_score": self._calculate_data_quality(raw_data)
                }
            }
            
            # Validate and clean extracted data
            extracted = self._validate_extracted_data(extracted)
            
            return extracted
            
        except Exception as e:
            logger.error(f"Profile extraction failed: {str(e)}")
            raise Exception(f"Failed to extract profile data: {str(e)}")
    
    def _extract_demographics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract demographic information"""
        
        demographics = {}
        
        # Direct field mapping
        field_mappings = {
            "age": ["age", "customer_age", "user_age"],
            "gender": ["gender", "sex"],
            "location": ["location", "address", "city", "state", "country", "zip_code", "postal_code"],
            "income": ["income", "annual_income", "salary", "household_income"],
            "education": ["education", "education_level", "degree"],
            "occupation": ["occupation", "job", "job_title", "profession", "work"],
            "marital_status": ["marital_status", "relationship_status", "married"],
            "family_size": ["family_size", "household_size", "children", "kids"]
        }
        
        for demo_field, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in data and data[key] is not None:
                    demographics[demo_field] = self._clean_demographic_value(demo_field, data[key])
                    break
        
        # Extract location from complex address data
        if "address" in data and isinstance(data["address"], dict):
            location_parts = []
            for location_key in ["city", "state", "country"]:
                if location_key in data["address"]:
                    location_parts.append(str(data["address"][location_key]))
            if location_parts:
                demographics["location"] = ", ".join(location_parts)
        
        # Age from birth_date
        if "birth_date" in data or "date_of_birth" in data:
            birth_date_str = data.get("birth_date") or data.get("date_of_birth")
            age = self._calculate_age_from_birth_date(birth_date_str)
            if age:
                demographics["age"] = age
        
        return demographics
    
    def _extract_behavioral_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral patterns and interaction data"""
        
        behavioral = {}
        
        # Purchase history
        if "purchase_history" in data:
            behavioral["purchase_history"] = self._process_purchase_history(data["purchase_history"])
        elif "orders" in data:
            behavioral["purchase_history"] = self._process_purchase_history(data["orders"])
        
        # Website interactions
        web_interactions = {}
        for key in ["page_views", "sessions", "time_on_site", "bounce_rate", "pages_per_session"]:
            if key in data:
                web_interactions[key] = data[key]
        if web_interactions:
            behavioral["website_interactions"] = web_interactions
        
        # Email engagement
        email_data = {}
        for key in ["email_opens", "email_clicks", "email_unsubscribes", "email_frequency"]:
            if key in data:
                email_data[key] = data[key]
        if email_data:
            behavioral["email_engagement"] = email_data
        
        # Social media activity
        social_data = {}
        for platform in ["facebook", "twitter", "instagram", "linkedin", "tiktok"]:
            if platform in data or f"{platform}_activity" in data:
                platform_data = data.get(platform) or data.get(f"{platform}_activity")
                if platform_data:
                    social_data[platform] = platform_data
        if social_data:
            behavioral["social_media_activity"] = social_data
        
        # Product preferences
        if "product_preferences" in data:
            behavioral["product_preferences"] = data["product_preferences"]
        elif "favorite_products" in data:
            behavioral["product_preferences"] = data["favorite_products"]
        
        return behavioral
    
    def _extract_psychographics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract psychographic information"""
        
        psychographics = {}
        
        # Direct psychographic fields
        for field in self.psychographic_fields:
            if field in data:
                psychographics[field] = data[field]
        
        # Survey responses
        if "survey_responses" in data:
            psychographics["survey_insights"] = self._analyze_survey_responses(data["survey_responses"])
        
        # Interests from various sources
        interests = []
        for key in ["interests", "hobbies", "preferences", "likes"]:
            if key in data:
                if isinstance(data[key], list):
                    interests.extend(data[key])
                else:
                    interests.append(str(data[key]))
        if interests:
            psychographics["interests"] = list(set(interests))  # Remove duplicates
        
        return psychographics
    
    def _extract_contact_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information"""
        
        contact = {}
        
        # Email
        for email_field in ["email", "email_address", "contact_email"]:
            if email_field in data and self._is_valid_email(data[email_field]):
                contact["email"] = data[email_field].lower()
                break
        
        # Phone
        for phone_field in ["phone", "phone_number", "mobile", "contact_phone"]:
            if phone_field in data:
                phone = self._clean_phone_number(data[phone_field])
                if phone:
                    contact["phone"] = phone
                break
        
        # Name
        if "name" in data:
            contact["name"] = data["name"]
        elif "first_name" in data or "last_name" in data:
            name_parts = []
            if "first_name" in data:
                name_parts.append(data["first_name"])
            if "last_name" in data:
                name_parts.append(data["last_name"])
            contact["name"] = " ".join(name_parts)
        
        return contact
    
    def _extract_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer preferences"""
        
        preferences = {}
        
        # Communication preferences
        comm_prefs = []
        for pref in ["email", "sms", "phone", "mail", "push_notifications"]:
            if f"prefers_{pref}" in data and data[f"prefers_{pref}"]:
                comm_prefs.append(pref)
            elif f"{pref}_preference" in data and data[f"{pref}_preference"]:
                comm_prefs.append(pref)
        
        if comm_prefs:
            preferences["communication_channels"] = comm_prefs
        
        # Content preferences
        if "content_preferences" in data:
            preferences["content_types"] = data["content_preferences"]
        
        # Frequency preferences
        if "contact_frequency" in data:
            preferences["contact_frequency"] = data["contact_frequency"]
        
        return preferences
    
    def _extract_interaction_history(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract interaction history"""
        
        interactions = []
        
        if "interaction_history" in data and isinstance(data["interaction_history"], list):
            for interaction in data["interaction_history"]:
                if isinstance(interaction, dict):
                    interactions.append({
                        "type": interaction.get("type", "unknown"),
                        "timestamp": interaction.get("timestamp", interaction.get("date")),
                        "details": interaction.get("details", interaction.get("description")),
                        "outcome": interaction.get("outcome", interaction.get("result"))
                    })
        
        # Extract from purchase history as interactions
        if "purchase_history" in data and isinstance(data["purchase_history"], list):
            for purchase in data["purchase_history"]:
                if isinstance(purchase, dict):
                    interactions.append({
                        "type": "purchase",
                        "timestamp": purchase.get("date", purchase.get("timestamp")),
                        "details": f"Purchased {purchase.get('product', 'unknown product')}",
                        "value": purchase.get("amount", purchase.get("total"))
                    })
        
        return interactions
    
    def _clean_demographic_value(self, field: str, value: Any) -> Any:
        """Clean and validate demographic values"""
        
        if value is None:
            return None
        
        if field == "age":
            try:
                age = int(value)
                return age if 0 < age < 120 else None
            except (ValueError, TypeError):
                return None
        
        elif field == "gender":
            gender_str = str(value).lower()
            if gender_str in ["m", "male", "man"]:
                return "Male"
            elif gender_str in ["f", "female", "woman"]:
                return "Female"
            elif gender_str in ["other", "non-binary", "nb"]:
                return "Other"
            else:
                return str(value).title()
        
        elif field == "income":
            # Extract numeric income from strings like "$50,000" or "50k"
            income_str = str(value).replace("$", "").replace(",", "").lower()
            if "k" in income_str:
                try:
                    return int(float(income_str.replace("k", "")) * 1000)
                except ValueError:
                    return None
            try:
                return int(float(income_str))
            except ValueError:
                return str(value)
        
        return str(value).strip()
    
    def _calculate_age_from_birth_date(self, birth_date_str: str) -> Optional[int]:
        """Calculate age from birth date string"""
        
        try:
            # Try common date formats
            for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    birth_date = datetime.strptime(birth_date_str, date_format)
                    age = (datetime.now() - birth_date).days // 365
                    return age if 0 < age < 120 else None
                except ValueError:
                    continue
        except Exception:
            pass
        
        return None
    
    def _process_purchase_history(self, purchase_data: Any) -> List[Dict[str, Any]]:
        """Process and clean purchase history data"""
        
        if not isinstance(purchase_data, list):
            return []
        
        processed = []
        for purchase in purchase_data:
            if isinstance(purchase, dict):
                processed_purchase = {
                    "date": purchase.get("date", purchase.get("timestamp")),
                    "amount": purchase.get("amount", purchase.get("total", purchase.get("value"))),
                    "product": purchase.get("product", purchase.get("item", purchase.get("product_name"))),
                    "category": purchase.get("category", purchase.get("product_category"))
                }
                processed.append(processed_purchase)
        
        return processed
    
    def _analyze_survey_responses(self, survey_data: Any) -> Dict[str, Any]:
        """Analyze survey responses for psychographic insights"""
        
        insights = {
            "satisfaction_level": "unknown",
            "key_motivators": [],
            "pain_points": [],
            "brand_perception": "neutral"
        }
        
        if isinstance(survey_data, dict):
            # Extract satisfaction
            for key in ["satisfaction", "satisfaction_score", "rating"]:
                if key in survey_data:
                    insights["satisfaction_level"] = survey_data[key]
                    break
            
            # Extract motivators and pain points from text responses
            for key, value in survey_data.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    if any(word in value_lower for word in ["like", "love", "enjoy", "prefer"]):
                        insights["key_motivators"].append(value)
                    elif any(word in value_lower for word in ["dislike", "hate", "problem", "issue", "difficult"]):
                        insights["pain_points"].append(value)
        
        return insights
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        
        if not email or not isinstance(email, str):
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def _clean_phone_number(self, phone: Any) -> Optional[str]:
        """Clean and format phone number"""
        
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', str(phone))
        
        # Basic validation (7-15 digits)
        if 7 <= len(digits) <= 15:
            return digits
        
        return None
    
    def _identify_data_sources(self, data: Dict[str, Any]) -> List[str]:
        """Identify the sources of the data"""
        
        sources = []
        
        # Check for source indicators
        if "source" in data:
            sources.append(data["source"])
        
        # Infer sources from data structure
        if any(key in data for key in ["page_views", "sessions", "bounce_rate"]):
            sources.append("website_analytics")
        
        if any(key in data for key in ["email_opens", "email_clicks"]):
            sources.append("email_marketing")
        
        if any(key in data for key in ["purchase_history", "orders"]):
            sources.append("transaction_system")
        
        if any(key in data for key in ["survey_responses", "feedback"]):
            sources.append("customer_feedback")
        
        if any(platform in str(data) for platform in ["facebook", "twitter", "instagram"]):
            sources.append("social_media")
        
        return sources or ["unknown"]
    
    def _calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score (0-1)"""
        
        total_fields = 0
        filled_fields = 0
        
        important_fields = [
            "name", "email", "age", "location", "purchase_history",
            "interests", "preferences"
        ]
        
        for field in important_fields:
            total_fields += 1
            if field in data and data[field] is not None and str(data[field]).strip():
                filled_fields += 1
        
        # Check for nested data completeness
        for section in ["demographics", "behavioral", "contact_info"]:
            if section in data and isinstance(data[section], dict):
                total_fields += len(data[section])
                filled_fields += sum(1 for v in data[section].values() if v is not None)
        
        return round(filled_fields / max(total_fields, 1), 2)
    
    def _validate_extracted_data(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        # Ensure all expected sections exist
        for section in ["demographics", "behavioral", "psychographics", "contact_info", "preferences"]:
            if section not in extracted:
                extracted[section] = {}
        
        if "interaction_history" not in extracted:
            extracted["interaction_history"] = []
        
        # Remove empty values
        for section_name, section_data in extracted.items():
            if isinstance(section_data, dict):
                extracted[section_name] = {k: v for k, v in section_data.items() if v is not None and str(v).strip()}
        
        return extracted