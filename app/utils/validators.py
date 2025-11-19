# app/utils/validators.py
"""
Validation Models for Business Profiles

Pydantic models for comprehensive business profile validation
optimized for Sri Lankan SME context.
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

class BusinessIdentity(BaseModel):
    """Business identity and basic information"""
    business_type: str = Field("", description="Type of business (e.g., Restaurant, Salon, Retail)")
    industry: str = Field("", description="Industry category")
    business_size: str = Field("", description="Business size (Solo, Small Team, Medium, Large)")
    location: str = Field("", description="Primary business location")
    business_stage: str = Field("", description="Current business stage (Just Started, Growing, Established, etc.)")
    products_services: str = Field("", description="Main products or services offered")
    unique_value: str = Field("", description="Unique value proposition")
    years_in_business: str = Field("", description="How long in business")
    
    @validator('business_type')
    def normalize_business_type(cls, v):
        if v:
            return v.title().strip()
        return v
    
    @validator('location')
    def normalize_location(cls, v):
        if v:
            # Common Sri Lankan location normalizations
            location_map = {
                'cmb': 'Colombo', 'col': 'Colombo',
                'gampaha': 'Gampaha', 'kandy': 'Kandy',
                'galle': 'Galle', 'negombo': 'Negombo'
            }
            lower_v = v.lower().strip()
            return location_map.get(lower_v, v.title())
        return v

class Resources(BaseModel):
    """Business resources and capabilities"""
    monthly_budget: str = Field("", description="Monthly marketing budget")
    team_or_solo: str = Field("", description="Team structure")
    content_capacity: str = Field("", description="Content creation capacity")
    technical_skills: str = Field("", description="Technical/digital skills level")
    available_hours_per_week: str = Field("", description="Hours available for marketing per week")
    
    @validator("monthly_budget", pre=True, always=True)
    def normalize_budget(cls, v):
        if not v:
            return ""
        
        s = str(v).strip().lower()
        
        # Extract number and handle k/thousand notation
        patterns = [
            (r'(\d+(?:,\d+)*)\s*k', lambda m: f"LKR {int(m.group(1).replace(',', '')) * 1000:,}"),
            (r'lkr\s*(\d+(?:,\d+)*)', lambda m: f"LKR {m.group(1)}"),
            (r'rs\.?\s*(\d+(?:,\d+)*)', lambda m: f"LKR {m.group(1)}"),
            (r'(\d+(?:,\d+)*)\s*(?:rupees?)', lambda m: f"LKR {m.group(1)}"),
            (r'(\d+(?:,\d+)*)', lambda m: f"LKR {m.group(1)}")
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, s)
            if match:
                return formatter(match)
        
        return v

class Goals(BaseModel):
    """Business goals and objectives"""
    primary_goal: str = Field("", description="Main business goal")
    secondary_goals: List[str] = Field(default_factory=list, description="Additional goals")
    success_metrics: List[str] = Field(default_factory=list, description="How success will be measured")
    timeline_expectations: str = Field("", description="Expected timeline for goals")
    
    @validator('primary_goal')
    def normalize_primary_goal(cls, v):
        if v:
            # Normalize common goal variations
            goal_map = {
                'awareness': 'Brand Awareness',
                'sales': 'Increase Sales', 
                'customers': 'Customer Acquisition',
                'reach': 'Increase Reach',
                'online presence': 'Build Online Presence',
                'growth': 'Business Growth'
            }
            lower_v = v.lower().strip()
            for key, normalized in goal_map.items():
                if key in lower_v:
                    return normalized
        return v

class TargetAudience(BaseModel):
    """Target audience definition"""
    demographics: str = Field("", description="Age, gender, occupation details")
    target_locations: str = Field("", description="Geographic target areas")
    interests_behaviors: str = Field("", description="Interests and behaviors")
    buying_frequency: str = Field("", description="How often they purchase")
    price_sensitivity: str = Field("", description="Price sensitivity level")
    communication_preferences: List[str] = Field(default_factory=list, description="Preferred communication channels")

class PlatformPreferences(BaseModel):
    """Social media and platform preferences"""
    preferred_platforms: List[str] = Field(default_factory=list, description="Preferred social media platforms")
    platform_experience: str = Field("", description="Experience level with platforms")
    brand_assets_available: List[str] = Field(default_factory=list, description="Available brand assets")
    current_followers: Dict[str, Any] = Field(default_factory=dict, description="Current follower counts")
    posting_frequency: str = Field("", description="Current or desired posting frequency")
    
    @validator('preferred_platforms', pre=True, always=True)
    def normalize_platforms(cls, v):
        if not v:
            return []
        
        platform_map = {
            'fb': 'Facebook', 'facebook': 'Facebook',
            'ig': 'Instagram', 'insta': 'Instagram', 'instagram': 'Instagram',
            'wp': 'WhatsApp', 'whatsapp': 'WhatsApp',
            'tiktok': 'TikTok', 'linkedin': 'LinkedIn',
            'youtube': 'YouTube', 'yt': 'YouTube'
        }
        
        normalized = []
        platforms = v if isinstance(v, list) else [v]
        
        for platform in platforms:
            if isinstance(platform, str):
                normalized_name = platform_map.get(platform.lower().strip(), platform.title())
                if normalized_name not in normalized:
                    normalized.append(normalized_name)
        
        return normalized

class MarketContext(BaseModel):
    """Market and competitive context"""
    seasonality: str = Field("", description="Seasonal factors affecting business")
    competitor_behavior: str = Field("", description="What competitors are doing")
    local_market_conditions: str = Field("", description="Local market conditions")
    economic_factors: str = Field("", description="Economic factors affecting business")
    cultural_considerations: str = Field("", description="Cultural factors to consider")

class BrandPersonality(BaseModel):
    """Brand personality and communication style"""
    suggested_tone: str = Field("", description="Suggested communication tone")
    brand_values: List[str] = Field(default_factory=list, description="Core brand values")
    communication_style: str = Field("", description="Communication style preferences")
    visual_preferences: str = Field("", description="Visual style preferences")

class ProfileMetadata(BaseModel):
    """Profile metadata and processing information"""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_version: str = Field(default="1.0")
    input_language: str = Field(default="English")
    processing_notes: List[str] = Field(default_factory=list)
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_level: Optional[str] = Field(None)

class BusinessProfile(BaseModel):
    """Complete business profile model"""
    business_identity: BusinessIdentity = Field(default_factory=BusinessIdentity)
    resources: Resources = Field(default_factory=Resources)
    goals: Goals = Field(default_factory=Goals)
    target_audience: TargetAudience = Field(default_factory=TargetAudience)
    platform_preferences: PlatformPreferences = Field(default_factory=PlatformPreferences)
    strengths: List[str] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    market_context: MarketContext = Field(default_factory=MarketContext)
    brand_personality: BrandPersonality = Field(default_factory=BrandPersonality)
    missing_data_assumptions: Dict[str, Any] = Field(default_factory=dict)
    profile_metadata: Optional[ProfileMetadata] = Field(default_factory=ProfileMetadata)
    
    @model_validator(mode='after')
    def validate_profile_completeness(self):
        """Validate that essential profile information is present"""
        business_identity = self.business_identity
        
        # Ensure business type is specified
        if business_identity and not business_identity.business_type:
            if not self.missing_data_assumptions:
                self.missing_data_assumptions = {}
            self.missing_data_assumptions['business_type'] = 'Business type not specified in input'
        
        return self
    
    def calculate_completeness_score(self) -> float:
        """Calculate profile completeness score (0-1)"""
        total_fields = 0
        completed_fields = 0
        
        # Check essential fields
        essential_fields = [
            (self.business_identity.business_type, 'business_type'),
            (self.business_identity.location, 'location'),
            (self.goals.primary_goal, 'primary_goal'),
            (self.target_audience.demographics, 'demographics'),
            (self.resources.monthly_budget, 'budget')
        ]
        
        for field_value, field_name in essential_fields:
            total_fields += 1
            if field_value and field_value.strip():
                completed_fields += 1
        
        # Check list fields
        list_fields = [
            (self.strengths, 'strengths'),
            (self.challenges, 'challenges'),
            (self.platform_preferences.preferred_platforms, 'platforms')
        ]
        
        for field_list, field_name in list_fields:
            total_fields += 1
            if field_list:
                completed_fields += 1
        
        return completed_fields / total_fields if total_fields > 0 else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the business profile"""
        return {
            "business_type": self.business_identity.business_type,
            "location": self.business_identity.location,
            "primary_goal": self.goals.primary_goal,
            "monthly_budget": self.resources.monthly_budget,
            "preferred_platforms": self.platform_preferences.preferred_platforms,
            "completeness_score": self.calculate_completeness_score(),
            "key_strengths": self.strengths[:3],  # Top 3 strengths
            "main_challenges": self.challenges[:3]  # Top 3 challenges
        }

# Legacy alias for backward compatibility
Profile = BusinessProfile

# Request/Response models for API
class ProfileCreateRequest(BaseModel):
    """Request model for creating a business profile"""
    raw_input: str = Field(..., description="Raw business input from SME")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Processing preferences")

class ProfileResponse(BaseModel):
    """Response model for profile operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    profile: Optional[BusinessProfile] = Field(None, description="Generated business profile")
    summary: Optional[Dict[str, Any]] = Field(None, description="Profile summary")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
