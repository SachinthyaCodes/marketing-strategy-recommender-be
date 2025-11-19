# app/agents/profile_builder.py
"""
Profile Builder Agent

The core agent responsible for converting messy, unstructured SME input into 
a clean, standardized, machine-readable business profile.
"""

from typing import Dict, Any, List, Optional
import json
import re
import logging
from datetime import datetime

from app.tools.profile_extraction import ProfileExtractor, BusinessProfileTemplate
from app.utils.validators import BusinessProfile

logger = logging.getLogger(__name__)

class ProfileBuilderAgent:
    """
    The Profile Builder Agent - converts raw SME input into structured business profiles
    
    Key Features:
    - Handles mixed Sinhala + English input
    - Normalizes business terminology
    - Fills gaps with intelligent assumptions
    - Ensures consistent output format
    """
    
    def __init__(self, temperature: float = 0.1):
        self.temperature = temperature
        self.extractor = ProfileExtractor()
        self.template_generator = BusinessProfileTemplate()
        
        # Define the comprehensive system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Initialize business type classifications
        self.business_types = {
            "food_beverage": ["bakery", "restaurant", "cafe", "catering", "food truck", "hotel"],
            "retail": ["clothing", "electronics", "jewelry", "books", "cosmetics", "pharmacy"],
            "services": ["salon", "repair", "cleaning", "consulting", "tutoring", "fitness"],
            "healthcare": ["clinic", "dental", "physiotherapy", "veterinary"],
            "education": ["school", "training center", "language classes", "driving school"],
            "technology": ["software", "web development", "IT support", "digital marketing"]
        }
        
        # Sinhala to English mappings for common terms
        self.sinhala_mappings = {
            # Business goals
            "awareness ekak oni": "brand awareness",
            "sales wadakaranna oni": "increase sales", 
            "customers la gana": "customer acquisition",
            "reach eka wadakaranna": "increase reach",
            "online presence eka hadanna": "build online presence",
            
            # Business types
            "kade": "shop",
            "restaurant eka": "restaurant",
            "salon eka": "salon",
            "garage eka": "garage",
            
            # Challenges
            "photos nane": "lack of content",
            "time nane": "no time",
            "followers nane": "low followers",
            "engagement nane": "low engagement",
            "budget nane": "limited budget",
            
            # Strengths
            "hondama quality": "high quality",
            "loyal customers": "customer loyalty",
            "good location": "strategic location",
            
            # Platforms
            "fb": "Facebook",
            "ig": "Instagram",
            "whatsapp": "WhatsApp",
            "tiktok": "TikTok"
        }
    
    async def build_profile(self, raw_input: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main method to build a business profile from raw SME input
        
        Args:
            raw_input: Raw text input from SME (can be mixed Sinhala/English)
            user_context: Optional context about the user/business
            
        Returns:
            Structured business profile as dictionary
        """
        
        try:
            # Step 1: Preprocess and normalize input
            normalized_input = self._preprocess_input(raw_input)
            
            # Step 2: Extract structured data using LLM
            profile_data = await self._extract_profile_data(normalized_input, user_context)
            
            # Step 3: Validate and enhance the profile
            enhanced_profile = self._enhance_profile(profile_data, normalized_input)
            
            # Step 4: Fill missing data with intelligent assumptions
            complete_profile = self._fill_missing_data(enhanced_profile)
            
            # Step 5: Validate using Pydantic model
            validated_profile = BusinessProfile(**complete_profile)
            
            # Step 6: Add metadata
            final_profile = validated_profile.dict()
            final_profile["profile_metadata"] = {
                "created_at": datetime.utcnow().isoformat(),
                "agent_version": "1.0",
                "input_language": self._detect_language(raw_input),
                "processing_notes": self._get_processing_notes(raw_input, final_profile)
            }
            
            logger.info(f"Successfully built profile for business type: {final_profile['business_identity']['business_type']}")
            
            return final_profile
            
        except Exception as e:
            logger.error(f"Profile building failed: {str(e)}")
            raise Exception(f"Failed to build business profile: {str(e)}")
    
    def _preprocess_input(self, raw_input: str) -> str:
        """
        Preprocess raw input to normalize common terms and phrases
        """
        normalized = raw_input.lower().strip()
        
        # Replace common Sinhala phrases with English equivalents
        for sinhala_term, english_term in self.sinhala_mappings.items():
            normalized = normalized.replace(sinhala_term.lower(), english_term)
        
        # Clean up formatting
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
        normalized = re.sub(r'[•\-\*]\s*', '\n- ', normalized)  # Convert bullet points
        
        return normalized
    
    async def _extract_profile_data(self, normalized_input: str, user_context: Optional[Dict]) -> Dict[str, Any]:
        """
        Use LLM to extract structured data from normalized input
        """
        
        # Get the profile template
        template = self.template_generator.get_template()
        
        # Create the extraction prompt
        prompt = self._create_extraction_prompt(normalized_input, template, user_context)
        
        # Generate response using Ollama
        from app.utils.llm import get_llm_client
        
        llm_client = get_llm_client()
        
        try:
            response = await llm_client.generate(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            # Parse JSON response
            return self._parse_llm_response(response)
        
        except Exception as e:
            logger.error(f"Error generating profile: {e}")
            # Create fallback response with basic structure
            return {
                "business_identity": {
                    "business_name": "Unknown Business",
                    "business_type": "General Business",
                    "industry": "Unknown"
                }
            }
    
    def _create_system_prompt(self) -> str:
        """
        Create concise system prompt for the Profile Builder Agent
        """
        return """You are a business profile extractor for Sri Lankan SMEs.

Convert messy business input into structured JSON. Handle mixed Sinhala-English text.

Rules:
- Output ONLY valid JSON
- Make reasonable assumptions for missing data
- Use standard business terms
- Focus on key business information

Template structure:
{
  "business_identity": {"business_name": "", "business_type": "", "location": ""},
  "target_audience": {"demographics": "", "customer_count": ""},
  "products_services": "",
  "strengths": [],
  "challenges": []
}"""
    
    def _create_extraction_prompt(self, input_text: str, template: Dict, context: Optional[Dict]) -> str:
        """
        Create simplified extraction prompt
        """
        return f"""
Business Input:
{input_text}

Extract information and return as JSON with this structure:
{{
  "business_identity": {{
    "business_name": "extracted name or guess",
    "business_type": "Restaurant/Shop/Service etc",
    "location": "city/area"
  }},
  "target_audience": {{
    "demographics": "age group, type of people",
    "customer_count": "daily/monthly numbers if mentioned"
  }},
  "products_services": "what they sell/offer",
  "strengths": ["key advantages"],
  "challenges": ["main problems"]
}}

Return ONLY the JSON object."""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract JSON object
        """
        try:
            # Try direct parsing first
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Extract JSON from response text
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # More aggressive extraction
            start_idx = response.find('{')
            if start_idx != -1:
                # Find the matching closing brace
                brace_count = 0
                end_idx = start_idx
                for i, char in enumerate(response[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                try:
                    return json.loads(response[start_idx:end_idx])
                except json.JSONDecodeError:
                    pass
            
            raise ValueError(f"Could not extract valid JSON from LLM response: {response}")
    
    def _enhance_profile(self, profile_data: Dict[str, Any], original_input: str) -> Dict[str, Any]:
        """
        Enhance the extracted profile with business intelligence
        """
        enhanced = profile_data.copy()
        
        # Enhance business type classification
        business_type = enhanced.get('business_identity', {}).get('business_type', '').lower()
        enhanced_type = self._classify_business_type(business_type, original_input)
        if enhanced_type:
            enhanced.setdefault('business_identity', {})['business_type'] = enhanced_type
        
        # Enhance target audience specificity
        self._enhance_target_audience(enhanced, original_input)
        
        # Enhance platform recommendations
        self._enhance_platform_preferences(enhanced)
        
        # Enhance budget normalization
        self._normalize_budget(enhanced)
        
        return enhanced
    
    def _classify_business_type(self, business_type: str, input_text: str) -> Optional[str]:
        """
        Classify business type more accurately
        """
        input_lower = input_text.lower()
        
        # Check for specific business indicators in input
        for category, types in self.business_types.items():
            for biz_type in types:
                if biz_type in input_lower or biz_type in business_type:
                    return biz_type.title()
        
        # Return original if no match
        return business_type.title() if business_type else None
    
    def _enhance_target_audience(self, profile: Dict[str, Any], input_text: str):
        """
        Make target audience more specific and actionable
        """
        audience = profile.setdefault('target_audience', {})
        demographics = audience.get('demographics', '')
        
        if demographics and 'specific' not in demographics.lower():
            # Add more specificity based on business type
            business_type = profile.get('business_identity', {}).get('business_type', '').lower()
            
            if 'bakery' in business_type or 'restaurant' in business_type:
                if 'age' not in demographics:
                    audience['demographics'] = f"{demographics} (Ages 18-45, working professionals and families)"
            elif 'salon' in business_type or 'beauty' in business_type:
                if 'women' not in demographics.lower():
                    audience['demographics'] = f"{demographics} (Primarily women 20-50)"
    
    def _enhance_platform_preferences(self, profile: Dict[str, Any]):
        """
        Enhance platform preferences based on business type
        """
        platforms = profile.setdefault('platform_preferences', {}).setdefault('preferred_platforms', [])
        business_type = profile.get('business_identity', {}).get('business_type', '').lower()
        
        # Recommend platforms based on business type if none specified
        if not platforms:
            if any(word in business_type for word in ['restaurant', 'bakery', 'food']):
                platforms.extend(['Facebook', 'Instagram', 'WhatsApp'])
            elif any(word in business_type for word in ['salon', 'beauty', 'fashion']):
                platforms.extend(['Instagram', 'Facebook', 'TikTok'])
            elif any(word in business_type for word in ['tech', 'service', 'consulting']):
                platforms.extend(['LinkedIn', 'Facebook', 'WhatsApp'])
            else:
                platforms.extend(['Facebook', 'Instagram'])
    
    def _normalize_budget(self, profile: Dict[str, Any]):
        """
        Normalize budget format
        """
        resources = profile.setdefault('resources', {})
        budget = resources.get('monthly_budget', '')
        
        if budget and 'LKR' not in budget.upper():
            # Extract numbers and convert
            numbers = re.findall(r'[\d,]+', budget)
            if numbers:
                amount = numbers[0].replace(',', '')
                if 'k' in budget.lower():
                    amount = str(int(float(amount) * 1000))
                resources['monthly_budget'] = f"LKR {amount:,}" if amount.isdigit() else budget
    
    def _fill_missing_data(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill missing data with intelligent assumptions
        """
        assumptions = profile.setdefault('missing_data_assumptions', {})
        
        # Fill missing business stage
        if not profile.get('business_identity', {}).get('business_stage'):
            profile.setdefault('business_identity', {})['business_stage'] = 'Growing'
            assumptions['business_stage'] = 'Assumed "Growing" as most SMEs are in growth phase'
        
        # Fill missing team structure
        if not profile.get('resources', {}).get('team_or_solo'):
            profile.setdefault('resources', {})['team_or_solo'] = 'Solo or small team'
            assumptions['team_structure'] = 'Assumed small team structure typical for SMEs'
        
        # Fill missing content capacity
        if not profile.get('resources', {}).get('content_capacity'):
            profile.setdefault('resources', {})['content_capacity'] = 'Limited - needs simple solutions'
            assumptions['content_capacity'] = 'Assumed limited capacity typical for SMEs'
        
        # Add default strengths if none provided
        if not profile.get('strengths'):
            business_type = profile.get('business_identity', {}).get('business_type', '').lower()
            if 'restaurant' in business_type or 'bakery' in business_type:
                profile['strengths'] = ['Quality products', 'Local customer base']
                assumptions['strengths'] = 'Added typical F&B business strengths'
        
        return profile
    
    def _detect_language(self, text: str) -> str:
        """
        Detect if input contains Sinhala characters
        """
        # Simple detection for Sinhala Unicode range
        sinhala_pattern = r'[\u0D80-\u0DFF]'
        if re.search(sinhala_pattern, text):
            return 'Mixed Sinhala-English'
        return 'English'
    
    def _get_processing_notes(self, original_input: str, final_profile: Dict) -> List[str]:
        """
        Generate processing notes for transparency
        """
        notes = []
        
        if len(original_input) < 50:
            notes.append('Input was brief - made several assumptions')
        
        if self._detect_language(original_input) == 'Mixed Sinhala-English':
            notes.append('Processed mixed language input')
        
        assumptions = final_profile.get('missing_data_assumptions', {})
        if assumptions:
            notes.append(f'Made {len(assumptions)} intelligent assumptions')
        
        return notes

# Legacy function for backward compatibility
def build_profile(raw_input: str, temperature: float = 0.0) -> dict:
    """
    Legacy function - creates agent instance and builds profile
    """
    import asyncio
    agent = ProfileBuilderAgent(temperature=temperature)
    return asyncio.run(agent.build_profile(raw_input))
