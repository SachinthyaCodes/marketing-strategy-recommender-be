"""
Validation Schemas
Pydantic models for request/response validation and data schemas
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

# Enums for controlled values
class CustomerSegment(str, Enum):
    HIGH_VALUE = "high_value"
    LOYAL = "loyal"
    AT_RISK = "at_risk"
    NEW = "new"
    CHAMPION = "champion"
    POTENTIAL = "potential"
    HIBERNATING = "hibernating"

class CampaignObjective(str, Enum):
    AWARENESS = "awareness"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ACQUISITION = "acquisition"
    LOYALTY = "loyalty"

class CommunicationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    PUSH_NOTIFICATION = "push_notification"
    DIRECT_MAIL = "direct_mail"
    PHONE = "phone"
    IN_APP = "in_app"

class ContentType(str, Enum):
    BLOG_POST = "blog_post"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"
    EMAIL_CAMPAIGN = "email_campaign"
    SOCIAL_POST = "social_post"
    WEBINAR = "webinar"
    EBOOK = "ebook"
    CASE_STUDY = "case_study"

# Request Models
class CustomerDemographics(BaseModel):
    age: Optional[int] = Field(None, ge=18, le=120, description="Customer age")
    gender: Optional[str] = Field(None, description="Customer gender")
    location: Optional[str] = Field(None, description="Customer location")
    income: Optional[Union[int, str]] = Field(None, description="Annual income")
    education: Optional[str] = Field(None, description="Education level")
    occupation: Optional[str] = Field(None, description="Job or profession")
    marital_status: Optional[str] = Field(None, description="Marital status")
    family_size: Optional[int] = Field(None, ge=1, description="Number of family members")

class CustomerBehavioral(BaseModel):
    purchase_frequency: Optional[str] = Field(None, description="How often customer purchases")
    average_order_value: Optional[float] = Field(None, ge=0, description="Average spending per order")
    preferred_channels: Optional[List[CommunicationChannel]] = Field(None, description="Preferred communication channels")
    product_categories: Optional[List[str]] = Field(None, description="Preferred product categories")
    engagement_level: Optional[str] = Field(None, description="Customer engagement level")
    last_purchase_date: Optional[datetime] = Field(None, description="Date of last purchase")

class CustomerPsychographics(BaseModel):
    interests: Optional[List[str]] = Field(None, description="Customer interests and hobbies")
    values: Optional[List[str]] = Field(None, description="Core values and beliefs")
    lifestyle: Optional[str] = Field(None, description="Lifestyle description")
    personality_traits: Optional[List[str]] = Field(None, description="Key personality traits")
    motivations: Optional[List[str]] = Field(None, description="What motivates the customer")
    pain_points: Optional[List[str]] = Field(None, description="Customer challenges and pain points")

class ContactInformation(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    name: Optional[str] = Field(None, description="Full name")
    preferred_contact_time: Optional[str] = Field(None, description="Preferred time for contact")

class ProfileCreateRequest(BaseModel):
    """Request model for creating a customer profile"""
    
    # Customer identification
    customer_id: Optional[str] = Field(None, description="Unique customer identifier")
    source: Optional[str] = Field(None, description="Data source identifier")
    
    # Core profile data
    demographics: Optional[CustomerDemographics] = Field(None, description="Demographic information")
    behavioral: Optional[CustomerBehavioral] = Field(None, description="Behavioral data")
    psychographics: Optional[CustomerPsychographics] = Field(None, description="Psychographic information")
    contact_info: Optional[ContactInformation] = Field(None, description="Contact information")
    
    # Raw data fields (flexible for various input formats)
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Additional raw customer data")
    
    # Interaction history
    interaction_history: Optional[List[Dict[str, Any]]] = Field(None, description="Previous interaction history")
    
    # Metadata
    data_collection_date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When data was collected")
    consent_status: Optional[bool] = Field(True, description="Customer consent for data processing")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "customer_id": "cust_12345",
                "source": "website_form",
                "demographics": {
                    "age": 32,
                    "gender": "Female",
                    "location": "San Francisco, CA",
                    "income": 75000,
                    "education": "Bachelor's Degree",
                    "occupation": "Software Engineer"
                },
                "behavioral": {
                    "purchase_frequency": "Monthly",
                    "average_order_value": 150.0,
                    "preferred_channels": ["email", "social_media"],
                    "product_categories": ["Technology", "Books"],
                    "engagement_level": "High"
                },
                "contact_info": {
                    "email": "customer@example.com",
                    "name": "Jane Smith",
                    "preferred_contact_time": "Evening"
                },
                "consent_status": True
            }
        }

class StrategyRequest(BaseModel):
    """Request model for generating marketing strategy"""
    
    campaign_objectives: List[CampaignObjective] = Field(..., description="Campaign objectives")
    budget_range: str = Field(..., description="Budget range (e.g., '$1000-$5000')")
    timeline: str = Field(..., description="Campaign timeline (e.g., '3 months')")
    target_channels: Optional[List[CommunicationChannel]] = Field(None, description="Preferred marketing channels")
    content_preferences: Optional[List[ContentType]] = Field(None, description="Preferred content types")
    campaign_constraints: Optional[List[str]] = Field(None, description="Any campaign constraints or limitations")
    
    class Config:
        schema_extra = {
            "example": {
                "campaign_objectives": ["awareness", "engagement"],
                "budget_range": "$2000-$5000",
                "timeline": "3 months",
                "target_channels": ["email", "social_media"],
                "content_preferences": ["blog_post", "social_post"],
                "campaign_constraints": ["No video content", "Focus on digital channels only"]
            }
        }

# Response Models
class CustomerProfile(BaseModel):
    """Complete customer profile data model"""
    
    # Demographics
    demographics: Dict[str, Any] = Field(default_factory=dict)
    
    # Behavioral insights
    behavioral_patterns: List[str] = Field(default_factory=list)
    purchase_behavior: Dict[str, Any] = Field(default_factory=dict)
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Psychographics
    psychographics: Dict[str, Any] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)
    
    # Segmentation
    customer_segment: CustomerSegment = Field(default=CustomerSegment.POTENTIAL)
    segment_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Preferences
    communication_preferences: List[CommunicationChannel] = Field(default_factory=list)
    content_preferences: List[ContentType] = Field(default_factory=list)
    
    # Insights
    pain_points: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)
    recommended_touchpoints: List[str] = Field(default_factory=list)
    
    # Scoring
    engagement_score: float = Field(default=5.0, ge=0.0, le=10.0)
    value_score: float = Field(default=5.0, ge=0.0, le=10.0)
    retention_risk: float = Field(default=0.3, ge=0.0, le=1.0)

class MarketingStrategy(BaseModel):
    """Marketing strategy data model"""
    
    # Strategy overview
    strategy_overview: str = Field(..., description="High-level strategy description")
    positioning_statement: str = Field(..., description="Brand positioning for this customer")
    
    # Channel strategy
    recommended_channels: List[CommunicationChannel] = Field(..., description="Recommended marketing channels")
    channel_priorities: Dict[str, int] = Field(default_factory=dict, description="Channel priority rankings")
    
    # Content strategy
    content_themes: List[str] = Field(default_factory=list, description="Key content themes")
    messaging_pillars: List[str] = Field(default_factory=list, description="Core messaging pillars")
    content_calendar: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested content calendar")
    
    # Campaign tactics
    campaign_tactics: List[Dict[str, Any]] = Field(default_factory=list, description="Specific campaign tactics")
    personalization_opportunities: List[str] = Field(default_factory=list, description="Personalization opportunities")
    
    # Budget and timeline
    budget_allocation: Dict[str, str] = Field(default_factory=dict, description="Budget allocation by channel/tactic")
    timeline_phases: List[Dict[str, Any]] = Field(default_factory=list, description="Campaign timeline phases")
    
    # Metrics and optimization
    success_metrics: List[str] = Field(default_factory=list, description="Key success metrics to track")
    optimization_opportunities: List[str] = Field(default_factory=list, description="Areas for optimization")
    
    # Risk and recommendations
    risk_factors: List[str] = Field(default_factory=list, description="Potential risk factors")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation strategies")
    recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")

class ProfileResponse(BaseModel):
    """Response model for profile creation/retrieval"""
    
    id: str = Field(..., description="Unique profile identifier")
    status: str = Field(..., description="Processing status")
    profile_data: CustomerProfile = Field(..., description="Complete customer profile")
    created_at: str = Field(..., description="Profile creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data quality score")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "profile_abc123",
                "status": "completed",
                "profile_data": {
                    "customer_segment": "high_value",
                    "engagement_score": 8.5,
                    "demographics": {"age": 32, "location": "San Francisco, CA"},
                    "interests": ["Technology", "Books", "Travel"],
                    "pain_points": ["Time constraints", "Information overload"],
                    "recommended_touchpoints": ["email", "social_media"]
                },
                "created_at": "2023-11-18T10:30:00Z",
                "updated_at": "2023-11-18T10:30:00Z",
                "data_quality_score": 0.85
            }
        }

class StrategyResponse(BaseModel):
    """Response model for marketing strategy generation"""
    
    profile_id: str = Field(..., description="Associated profile identifier")
    strategy: MarketingStrategy = Field(..., description="Complete marketing strategy")
    generated_at: str = Field(..., description="Strategy generation timestamp")
    campaign_objectives: List[CampaignObjective] = Field(..., description="Original campaign objectives")
    budget_range: str = Field(..., description="Original budget range")
    timeline: str = Field(..., description="Original timeline")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Strategy confidence score")
    
    class Config:
        schema_extra = {
            "example": {
                "profile_id": "profile_abc123",
                "strategy": {
                    "strategy_overview": "Multi-channel engagement strategy focusing on education and value delivery",
                    "recommended_channels": ["email", "social_media", "content_marketing"],
                    "content_themes": ["Product education", "Industry insights", "Customer success stories"],
                    "success_metrics": ["Email open rate", "Social engagement", "Conversion rate"]
                },
                "generated_at": "2023-11-18T10:35:00Z",
                "campaign_objectives": ["awareness", "engagement"],
                "budget_range": "$2000-$5000",
                "timeline": "3 months",
                "confidence_score": 0.9
            }
        }

# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")

# Utility Models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Number of records to return")

class ListResponse(BaseModel):
    """Generic list response model"""
    
    items: List[Dict[str, Any]] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items requested")
    has_more: bool = Field(..., description="Whether there are more items available")

# Validation Utilities
def validate_customer_segment(segment: str) -> CustomerSegment:
    """Validate and convert customer segment string to enum"""
    try:
        return CustomerSegment(segment.lower())
    except ValueError:
        return CustomerSegment.POTENTIAL

def validate_communication_channels(channels: List[str]) -> List[CommunicationChannel]:
    """Validate and convert communication channel strings to enums"""
    valid_channels = []
    for channel in channels:
        try:
            valid_channels.append(CommunicationChannel(channel.lower()))
        except ValueError:
            continue
    return valid_channels

def validate_campaign_objectives(objectives: List[str]) -> List[CampaignObjective]:
    """Validate and convert campaign objective strings to enums"""
    valid_objectives = []
    for objective in objectives:
        try:
            valid_objectives.append(CampaignObjective(objective.lower()))
        except ValueError:
            continue
    return valid_objectives